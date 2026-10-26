"use client";

import React, { useState, useEffect, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import ReviewHeader from "@/components/interviews/review/ReviewHeader";
import AudioWavePlayer from "@/components/interviews/review/AudioWavePlayer";
import TranscriptStream from "@/components/interviews/review/TranscriptStream";
import CompetencyCard from "@/components/interviews/review/CompetencyCard";
import CandidateSnapshotCard from "@/components/interviews/review/CandidateSnapshotCard";
import HrDecisionCard from "@/components/interviews/review/HrDecisionCard";
import {
  InterviewSession,
  TranscriptSegment,
  SummaryEvidence,
  HrDecision,
  HrDecisionType,
} from "@/types/interview";
import {
  getInterviewSession,
  getInterviewTranscripts,
  listInterviewSessions,
  saveHrDecision,
} from "@/services/interviewService";
import { ShootingStarIcon, CheckCircleIcon } from "@/icons";

function ReviewContent() {
  const searchParams = useSearchParams();
  const sessionIdParam = searchParams.get("id");

  // Audio Player State (Client-side UX simulation, Ledger U-07)
  const [currentTimeMs, setCurrentTimeMs] = useState<number>(80000);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [activeSegmentId, setActiveSegmentId] = useState<string | null>(null);

  const [sessionData, setSessionData] = useState<InterviewSession | null>(null);
  const [transcriptSegments, setTranscriptSegments] = useState<TranscriptSegment[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const durationMs = 45 * 60 * 1000 + 20 * 1000; // 45:20 in ms

  // Hydrate session metadata + verbatim transcript strictly from the Backend API
  useEffect(() => {
    let cancelled = false;

    const loadEvidence = async () => {
      setIsLoading(true);
      try {
        let targetId = sessionIdParam;
        if (!targetId) {
          const listPage = await listInterviewSessions({ page_size: 1 });
          targetId = listPage?.items?.[0]?.id ?? null;
        }

        if (!targetId || cancelled) {
          if (!cancelled) setIsLoading(false);
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
        console.error("Failed to fetch interview review data:", error);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    };

    void loadEvidence();

    return () => {
      cancelled = true;
    };
  }, [sessionIdParam]);

  const competencyPoints = sessionData?.competency_points ?? [];

  // Audio play simulation timer
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isPlaying) {
      interval = setInterval(() => {
        setCurrentTimeMs((prev) => {
          if (prev >= durationMs) {
            setIsPlaying(false);
            return 0;
          }
          const next = prev + 1000;

          // Auto-match active transcript segment as audio plays
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
  }, [isPlaying, durationMs, activeSegmentId, transcriptSegments]);

  // Click on evidence quote -> jump audio + highlight transcript
  const handleJumpToEvidence = (evidence: SummaryEvidence) => {
    setCurrentTimeMs(evidence.start_ms);
    setActiveSegmentId(evidence.transcript_segment_id);
    setIsPlaying(true);
  };

  // Click directly on transcript segment
  const handleSelectSegment = (segment: TranscriptSegment) => {
    setCurrentTimeMs(segment.start_ms);
    setActiveSegmentId(segment.id);
  };

  const handleDecisionSubmit = useCallback(
    async (decision: HrDecisionType, notes: string) => {
      if (!sessionData) return;

      try {
        const saved = await saveHrDecision(sessionData.id, { decision, notes });
        const hrDecision: HrDecision = {
          decision: saved.decision,
          notes: saved.notes || notes,
          decided_at: String(saved.decided_at),
          decided_by: saved.decided_by,
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
      } catch (error) {
        console.error("Failed to save HR decision:", error);
      }
    },
    [sessionData]
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

  if (!sessionData) {
    return (
      <div>
        <PageBreadcrumb pageTitle="Review & Evidence Workspace" />
        <div className="rounded-2xl border border-gray-200 bg-white p-8 text-center text-xs text-gray-400 dark:border-gray-800 dark:bg-gray-900">
          No interview session found in database.
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageBreadcrumb pageTitle="Review & Evidence Workspace" />

      {/* Top Session Metadata Header */}
      <ReviewHeader session={sessionData} />

      {/* Split-View Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Left Pane: Audio Wave Player & Transcript (5 Cols) - Pinned Sticky */}
        <div className="lg:col-span-5 space-y-4 lg:sticky lg:top-20">
          <AudioWavePlayer
            currentTimeMs={currentTimeMs}
            durationMs={durationMs}
            isPlaying={isPlaying}
            onTogglePlay={() => setIsPlaying(!isPlaying)}
            onSeek={(ms) => setCurrentTimeMs(ms)}
          />

          <TranscriptStream
            segments={transcriptSegments}
            activeSegmentId={activeSegmentId}
            onSelectSegment={handleSelectSegment}
          />

          {/* Provenance & ATS Match Snapshot */}
          <CandidateSnapshotCard session={sessionData} />
        </div>

        {/* Right Pane: AI Copilot Rubric Assessment & HR Decision Gate (7 Cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Header Card */}
          <div className="rounded-2xl border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
                  <ShootingStarIcon/>
                </div>
                <div>
                  <h3 className="text-sm font-bold text-gray-900 dark:text-white">
                    AI Copilot Competency Assessment
                  </h3>
                  <p className="text-[11px] text-gray-500 dark:text-gray-400">
                    Objective summary generated per approved rubric. 100% backed by cited candidate quotes.
                  </p>
                </div>
              </div>

              <span className="inline-flex items-center gap-1 rounded-md bg-success-50 px-2.5 py-1 text-xs font-semibold text-success-700 dark:bg-success-500/15 dark:text-success-300">
                <CheckCircleIcon/>
                <span>
                  Audited {competencyPoints.length}/{competencyPoints.length} Points
                </span>
              </span>
            </div>
          </div>

          {/* Competency Rubric Cards */}
          <div className="space-y-3">
            {competencyPoints.map((point) => (
              <CompetencyCard
                key={point.id}
                point={point}
                onJumpToEvidence={handleJumpToEvidence}
              />
            ))}
          </div>

          {/* HR Decision Gate Form */}
          <HrDecisionCard
            key={sessionData.hr_decision?.decided_at ?? "pending-decision"}
            initialDecision={sessionData.hr_decision}
            onSubmitDecision={handleDecisionSubmit}
            candidateName={sessionData.candidate_name}
          />
        </div>
      </div>
    </div>
  );
}

export default function ReviewEvidencePage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs text-gray-400">Loading Review Workspace...</div>}>
      <ReviewContent />
    </Suspense>
  );
}
