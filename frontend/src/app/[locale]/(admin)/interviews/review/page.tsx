"use client";

import React, { Suspense, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { Link } from "@/i18n/navigation";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { ApiError } from "@/lib/api";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import Button from "@/components/ui/button/Button";
import ReviewHeader from "@/components/interviews/review/ReviewHeader";
import AudioWavePlayer from "@/components/interviews/review/AudioWavePlayer";
import TranscriptStream from "@/components/interviews/review/TranscriptStream";
import CompetencyCard from "@/components/interviews/review/CompetencyCard";
import CandidateSnapshotCard from "@/components/interviews/review/CandidateSnapshotCard";
import HrDecisionCard from "@/components/interviews/review/HrDecisionCard";
import {
  AdvanceNextStage,
  HrDecision,
  HrDecisionType,
  InterviewSession,
  SummaryEvidence,
  TranscriptSegment,
} from "@/types/interview";
import {
  getInterviewSession,
  getInterviewTranscripts,
  listInterviewSessions,
  saveHrDecision,
  swapSessionSpeakers,
  reEvaluateSession,
} from "@/services/interviewService";
import { AudioIcon, LockIcon, ShootingStarIcon } from "@/icons";

function ReviewContent() {
  const searchParams = useSearchParams();
  const sessionIdParam = searchParams.get("id");
  const queryClient = useQueryClient();
  const { user, role } = useAuth();
  const { showSuccess, showError } = useToast();

  // Audio Player State
  const [currentTimeMs, setCurrentTimeMs] = useState<number>(0);
  const [streamDurationMs, setStreamDurationMs] = useState<number | null>(null);
  const [isSwapping, setIsSwapping] = useState<boolean>(false);
  const [isReEvaluating, setIsReEvaluating] = useState<boolean>(false);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [activeSegmentId, setActiveSegmentId] = useState<string | null>(null);

  const [allSessions, setAllSessions] = useState<InterviewSession[]>([]);
  const [sessionData, setSessionData] = useState<InterviewSession | null>(null);
  const [transcriptSegments, setTranscriptSegments] = useState<TranscriptSegment[]>([]);
  const [accessDeniedMessage, setAccessDeniedMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const audioDurationStr = sessionData?.audio_duration;
  let parsedDurationMs = 60000;
  if (audioDurationStr) {
    const parts = audioDurationStr.split(":");
    if (parts.length === 2) {
      const ms = (parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10)) * 1000;
      if (!isNaN(ms) && ms > 0) parsedDurationMs = ms;
    }
  }

  const durationMs = streamDurationMs ?? parsedDurationMs;

  // Hydrate all sessions (for Session Switcher) + active session metadata + verbatim transcript
  useEffect(() => {
    let cancelled = false;

    const loadEvidence = async () => {
      setIsLoading(true);
      setAccessDeniedMessage(null);
      try {
        const listPage = await listInterviewSessions({
          page_size: 50,
          scope: role === "INTERVIEWER" ? "mine" : "all",
        });
        const sessionItems = Array.isArray(listPage?.items) ? listPage.items : [];
        if (!cancelled) {
          setAllSessions(sessionItems);
        }

        let targetId = sessionIdParam;
        if (!targetId) {
          const awaitingHrFollowup =
            role === "HR" || role === "ADMIN"
              ? sessionItems.find(
                  (s) =>
                    s.consent_status === "GRANTED" &&
                    s.job_status === "COMPLETED" &&
                    s.hr_decision?.workflow_status === "PENDING_HR_FOLLOWUP"
                )
              : undefined;
          const pendingOwnReview = sessionItems.find(
            (s) =>
              s.consent_status === "GRANTED" &&
              s.job_status === "COMPLETED" &&
              !s.hr_decision &&
              (role === "INTERVIEWER" ||
                !s.interviewer_id ||
                s.interviewer_id === user?.id)
          );
          const fallbackGranted = sessionItems.find((s) => s.consent_status === "GRANTED");
          targetId =
            awaitingHrFollowup?.id ??
            pendingOwnReview?.id ??
            fallbackGranted?.id ??
            sessionItems[0]?.id ??
            null;
        }

        if (!targetId || cancelled) {
          if (!cancelled) {
            setSessionData(null);
            setIsLoading(false);
          }
          return;
        }

        const [session, segments] = await Promise.all([
          getInterviewSession(targetId),
          getInterviewTranscripts(targetId),
        ]);
        if (cancelled) return;

        setSessionData(session);

        const validSegments = Array.isArray(segments) ? segments : [];
        setTranscriptSegments(validSegments);
        if (validSegments.length > 0) {
          setActiveSegmentId((prev) =>
            prev && validSegments.some((seg) => seg.id === prev)
              ? prev
              : validSegments[0].id
          );
        }
      } catch (error) {
        if (!cancelled && error instanceof ApiError && error.status === 403) {
          setSessionData(null);
          setAccessDeniedMessage(
            error.message ||
              "Access denied (403): You do not have permission to open an interview session belonging to another interviewer."
          );
        } else {
          console.error("Failed to fetch interview review data:", error);
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    };

    void loadEvidence();

    return () => {
      cancelled = true;
    };
  }, [sessionIdParam, user?.id, role]);

  const competencyPoints = sessionData?.competency_points ?? [];
  const verifiedCount = competencyPoints.filter(
    (p) => p.verification_status === "VERIFIED" && p.coverage_status !== "NOT_DISCUSSED"
  ).length;

  const handleSwapSpeakers = async () => {
    if (!sessionData) return;
    setIsSwapping(true);
    try {
      const updated = await swapSessionSpeakers(sessionData.id);
      setSessionData(updated);
      const freshSegments = await getInterviewTranscripts(sessionData.id);
      setTranscriptSegments(freshSegments);
      showSuccess("Pembicara Berhasil Ditukar", "Peran pembicara dan evaluasi AI telah diperbarui.");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Gagal menghubungi server.";
      showError("Gagal Menukar Pembicara", msg);
    } finally {
      setIsSwapping(false);
    }
  };

  const handleReEvaluate = async () => {
    if (!sessionData) return;
    setIsReEvaluating(true);
    try {
      const updated = await reEvaluateSession(sessionData.id);
      setSessionData(updated);
      showSuccess("Evaluasi Ulang Berhasil", "Rubrik kompetensi telah dievaluasi ulang dari transkrip.");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Gagal menghubungi server.";
      showError("Gagal Evaluasi Ulang", msg);
    } finally {
      setIsReEvaluating(false);
    }
  };

  // Audio play simulation timer (fallback when no native audio stream)
  useEffect(() => {
    const hasAudio = !!(sessionData?.audio_stream_url || sessionData?.audio_url);
    let interval: NodeJS.Timeout;
    if (isPlaying && !hasAudio) {
      interval = setInterval(() => {
        setCurrentTimeMs((prev) => {
          if (prev >= durationMs) {
            setIsPlaying(false);
            return 0;
          }
          const next = prev + 1000;

          const matchingSeg = transcriptSegments.find(
            (s) => next >= s.start_ms && next <= s.end_ms
          );
          if (matchingSeg && matchingSeg.id !== activeSegmentId) {
            setActiveSegmentId(matchingSeg.id);
          }

          return next;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isPlaying, durationMs, activeSegmentId, transcriptSegments, sessionData?.audio_stream_url, sessionData?.audio_url]);

  const handleJumpToEvidence = (evidence: SummaryEvidence) => {
    setCurrentTimeMs(evidence.start_ms);
    setActiveSegmentId(evidence.transcript_segment_id);
    setIsPlaying(true);
  };

  const handleSelectSegment = (segment: TranscriptSegment) => {
    setCurrentTimeMs(segment.start_ms);
    setActiveSegmentId(segment.id);
  };

  const handleDecisionSubmit = useCallback(
    async (
      decision: HrDecisionType,
      notes: string,
      nextStage?: AdvanceNextStage | null
    ) => {
      if (!sessionData) return;

      try {
        const saved = await saveHrDecision(sessionData.id, {
          decision,
          next_stage: nextStage,
          notes,
        });
        const hrDecision: HrDecision = {
          decision: saved.decision,
          next_stage: saved.next_stage ?? nextStage ?? null,
          resulting_candidate_status: saved.resulting_candidate_status ?? null,
          actor_role: saved.actor_role,
          workflow_status: saved.workflow_status,
          notes: saved.notes || notes,
          decided_at: String(saved.decided_at),
          decided_by: saved.decided_by,
          decided_by_user_id: saved.decided_by_user_id ?? null,
        };
        setSessionData((prev) =>
          prev
            ? {
                ...prev,
                hr_decision: hrDecision,
                job_status: "COMPLETED",
              }
            : prev
        );
        setAllSessions((prev) =>
          prev.map((item) =>
            item.id === sessionData.id ? { ...item, hr_decision: hrDecision } : item
          )
        );

        // Immediately sync Master Candidates cache so HR never edits status manually
        void queryClient.invalidateQueries({ queryKey: ["candidates"] });

        const resultingStatusLabel = saved.resulting_candidate_status || decision;
        if (saved.workflow_status === "PENDING_HR_FOLLOWUP") {
          showSuccess(
            "Evaluation Recommendation Forwarded to HR",
            `Recommendation ${decision} for ${sessionData.candidate_name} is locked and submitted to HR for final review (status: ${resultingStatusLabel}).`
          );
        } else {
          showSuccess(
            "HR Final Decision Permanently Saved",
            `Final decision ${decision} for ${sessionData.candidate_name} is locked. Candidate application status automatically updated to ${resultingStatusLabel}.`
          );
        }
      } catch (error) {
        console.error("Failed to save HR decision:", error);
        const msg =
          error instanceof Error
            ? error.message
            : "Failed to save evaluation decision to server.";
        showError("Failed to Save Decision", msg);
      }
    },
    [queryClient, sessionData, showError, showSuccess]
  );

  if (isLoading) {
    return (
      <div>
        <PageBreadcrumb pageTitle="Review & Evidence Workspace" />
        <div className="rounded-2xl border border-gray-200 bg-white p-8 text-center text-xs text-gray-400 dark:border-gray-800 dark:bg-gray-900">
          Loading interview session and evidence from database...
        </div>
      </div>
    );
  }

  if (accessDeniedMessage) {
    return (
      <div>
        <PageBreadcrumb pageTitle="Review & Evidence Workspace" />
        <div className="rounded-2xl border border-error-200 bg-error-50/50 p-10 text-center space-y-3 dark:border-error-500/30 dark:bg-error-500/10">
          <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-error-100 text-error-600 dark:bg-error-500/20 dark:text-error-400">
            <LockIcon />
          </div>
          <p className="text-sm font-bold text-error-800 dark:text-error-300">
            Zero-Trust Ownership Guard (403 Forbidden)
          </p>
          <p className="mx-auto max-w-md text-xs text-gray-600 dark:text-gray-300">
            {accessDeniedMessage}
          </p>
          <div>
            <Link
              href="/interviews/sessions"
              className="inline-flex items-center gap-1.5 rounded-xl bg-brand-500 px-4 py-2 text-xs font-semibold text-white hover:bg-brand-600 transition-all"
            >
              <AudioIcon />
              <span>Kembali ke Sesi Wawancara Saya</span>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!sessionData) {
    return (
      <div>
        <PageBreadcrumb pageTitle="Review & Evidence Workspace" />
        <div className="rounded-2xl border border-gray-200 bg-white p-10 text-center space-y-3 dark:border-gray-800 dark:bg-gray-900">
          <p className="text-sm font-semibold text-gray-800 dark:text-white">
            There are no interview recordings in the database yet.
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Upload interview recordings from candidates through the Interview Sessions page.
          </p>
          <div>
            <Link
              href="/interviews/sessions"
              className="inline-flex items-center gap-1.5 rounded-xl bg-brand-500 px-4 py-2 text-xs font-semibold text-white hover:bg-brand-600 transition-all"
            >
              <AudioIcon />
              <span>Open Interview Sessions</span>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageBreadcrumb pageTitle="Review & Evidence Workspace" />

      {/* Top Session Metadata Header + Session Switcher */}
      <ReviewHeader session={sessionData} allSessions={allSessions} />

      {/* Split-View Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Left Pane: Audio Wave Player & Transcript (5 Cols) - Pinned Sticky */}
        <div className="lg:col-span-5 space-y-4 lg:sticky lg:top-20">
          <AudioWavePlayer
            currentTimeMs={currentTimeMs}
            durationMs={durationMs}
            isPlaying={isPlaying}
            audioStreamUrl={sessionData.audio_stream_url || sessionData.audio_url}
            onTogglePlay={() => setIsPlaying(!isPlaying)}
            onSeek={(ms) => setCurrentTimeMs(ms)}
            onDurationChange={(dur) => setStreamDurationMs(dur)}
            onTimeUpdate={(ms) => {
              setCurrentTimeMs(ms);
              const matchingSeg = transcriptSegments.find(
                (s) => ms >= s.start_ms && ms <= s.end_ms
              );
              if (matchingSeg && matchingSeg.id !== activeSegmentId) {
                setActiveSegmentId(matchingSeg.id);
              }
            }}
            onEnded={() => setIsPlaying(false)}
          />

          <TranscriptStream
            segments={transcriptSegments}
            activeSegmentId={activeSegmentId}
            onSelectSegment={handleSelectSegment}
            onSwapSpeakers={handleSwapSpeakers}
            isSwapping={isSwapping}
          />

          <CandidateSnapshotCard session={sessionData} />
        </div>

        {/* Right Pane: AI Copilot Rubric Assessment & HR Decision Gate (7 Cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="rounded-2xl border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-2.5 text-start min-w-0">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
                  <ShootingStarIcon />
                </div>
                <div className="min-w-0">
                  <h3 className="text-sm font-bold text-gray-900 dark:text-white truncate">
                    AI Competency Assessment
                  </h3>
                  <p className="text-[11px] text-gray-500 dark:text-gray-400">
                    {verifiedCount} of {competencyPoints.length} competencies verified with candidate quotes
                  </p>
                </div>
              </div>

              <div className="shrink-0">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleReEvaluate}
                  isLoading={isReEvaluating}
                  className="whitespace-nowrap"
                  title="Evaluasi ulang transkrip menggunakan AI Agent"
                >
                  Re-evaluate AI
                </Button>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            {competencyPoints.map((point) => (
              <CompetencyCard
                key={point.id}
                point={point}
                onJumpToEvidence={handleJumpToEvidence}
              />
            ))}
          </div>

          <HrDecisionCard
            key={`${sessionData.id}-${sessionData.hr_decision?.workflow_status ?? "none"}-${sessionData.hr_decision?.decided_at ?? "pending"}`}
            initialDecision={sessionData.hr_decision}
            onSubmitDecision={handleDecisionSubmit}
            candidateId={sessionData.candidate_id}
            candidateName={sessionData.candidate_name}
            roundName={sessionData.round_name}
            currentUserId={user?.id ?? null}
            currentUserRole={role}
            interviewerId={sessionData.interviewer_id ?? null}
            interviewerName={sessionData.interviewer_name}
          />
        </div>
      </div>
    </div>
  );
}

export default function ReviewEvidencePage() {
  return (
    <Suspense
      fallback={
        <div className="p-8 text-center text-xs text-gray-400">
          Loading Review Workspace...
        </div>
      }
    >
      <ReviewContent />
    </Suspense>
  );
}
