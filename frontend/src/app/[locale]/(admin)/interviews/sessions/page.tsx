"use client";

import React, { Suspense, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import SessionTable from "@/components/interviews/sessions/SessionTable";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { LockIcon } from "@/icons";
import {
  deleteInterviewSession,
  listInterviewSessions,
  uploadInterviewFile,
  uploadInterviewSession,
} from "@/services/interviewService";
import { listCandidates, listContacts, listRubrics } from "@/services/masterService";
import { InterviewScopeFilter, InterviewSession } from "@/types/interview";
import { Candidate, InterviewerContact, RubricProfile } from "@/types/master";

function parseScopeParam(raw: string | null): InterviewScopeFilter {
  if (raw === "mine" || raw === "awaiting_hr" || raw === "all") {
    return raw;
  }
  return "all";
}

function InterviewSessionsContent() {
  const searchParams = useSearchParams();
  const { user, role } = useAuth();
  const { showSuccess, showError } = useToast();

  const candidateIdParam = searchParams.get("candidateId");
  const candidateCodeParam = searchParams.get("candidateCode");
  const actionParam = searchParams.get("action");
  const scopeParam = searchParams.get("scope");

  const [prevScopeParam, setPrevScopeParam] = useState<string | null>(scopeParam);
  const [selectedScope, setSelectedScope] = useState<InterviewScopeFilter>(() =>
    parseScopeParam(scopeParam)
  );

  if (scopeParam !== prevScopeParam) {
    setPrevScopeParam(scopeParam);
    setSelectedScope(parseScopeParam(scopeParam));
  }

  const effectiveScope: InterviewScopeFilter =
    role === "INTERVIEWER"
      ? "mine"
      : role === "ADMIN" && selectedScope === "mine"
      ? "all"
      : selectedScope;

  const [sessions, setSessions] = useState<InterviewSession[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [rubrics, setRubrics] = useState<RubricProfile[]>([]);
  const [interviewers, setInterviewers] = useState<InterviewerContact[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    let cancelled = false;

    const loadAll = async () => {
      setIsLoading(true);
      try {
        const [sessionsPage, candidatesPage, rubricList, contactList] = await Promise.all([
          listInterviewSessions({
            page_size: 50,
            scope: effectiveScope,
            candidate_code: candidateCodeParam || undefined,
          }),
          listCandidates({ page_size: 100 }).catch(() => ({
            items: [] as Candidate[],
            total: 0,
            page: 1,
            page_size: 100,
            total_pages: 1,
          })),
          listRubrics().catch(() => [] as RubricProfile[]),
          listContacts().catch(() => [] as InterviewerContact[]),
        ]);
        if (!cancelled) {
          setSessions(Array.isArray(sessionsPage?.items) ? sessionsPage.items : []);
          setCandidates(Array.isArray(candidatesPage?.items) ? candidatesPage.items : []);
          setRubrics(Array.isArray(rubricList) ? rubricList : []);
          setInterviewers(Array.isArray(contactList) ? contactList : []);
        }
      } catch (error) {
        console.error("Failed to fetch interview sessions & master metadata:", error);
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void loadAll();

    return () => {
      cancelled = true;
    };
  }, [effectiveScope, candidateCodeParam, user?.id, role]);

  // Auto-polling when there are active background jobs in progress
  useEffect(() => {
    const hasActiveJobs = sessions.some(
      (s) =>
        s.consent_status === "GRANTED" &&
        s.job_status !== "COMPLETED" &&
        s.job_status !== "REJECTED_NO_CONSENT" &&
        (s.progress_percentage ?? 100) < 100
    );

    if (!hasActiveJobs) return;

    const interval = setInterval(async () => {
      try {
        const page = await listInterviewSessions({
          page_size: 50,
          scope: effectiveScope,
          candidate_code: candidateCodeParam || undefined,
        });
        if (Array.isArray(page?.items)) {
          setSessions(page.items);
        }
      } catch (error) {
        console.error("Failed polling interview sessions:", error);
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [sessions, effectiveScope, candidateCodeParam]);

  const handleUploadSession = useCallback(
    async (
      localSession: InterviewSession,
      file?: File | null
    ): Promise<InterviewSession | null> => {
      const profileId = localSession.profile_id || rubrics[0]?.id || "1";
      const candidateId = localSession.candidate_id || "1";
      const interviewerId =
        role === "INTERVIEWER"
          ? user?.id ?? localSession.interviewer_id
          : localSession.interviewer_id;

      try {
        let created: InterviewSession;
        if (file) {
          const formData = new FormData();
          formData.append("file", file);
          formData.append("candidate_id", candidateId);
          formData.append("profile_id", profileId);
          if (interviewerId) {
            formData.append("interviewer_id", interviewerId);
          }
          formData.append("consent_status", localSession.consent_status);
          formData.append(
            "notes",
            `${localSession.round_name} - Interviewer: ${localSession.interviewer_name}`
          );
          created = await uploadInterviewFile(formData);
        } else {
          created = await uploadInterviewSession({
            candidate_id: candidateId,
            profile_id: profileId,
            interviewer_id: interviewerId || undefined,
            consent_status: localSession.consent_status,
            audio_url: localSession.audio_url,
            audio_duration: localSession.audio_duration,
            notes: `${localSession.round_name} - Interviewer: ${localSession.interviewer_name}`,
          });
        }
        setSessions((prev) => [created, ...prev.filter((s) => s.id !== created.id)]);
        return created;
      } catch (error) {
        console.error("Failed to upload interview session:", error);
        throw error;
      }
    },
    [role, rubrics, user?.id]
  );

  const handleDeleteSession = useCallback(
    async (sessionId: string): Promise<void> => {
      try {
        await deleteInterviewSession(sessionId);
        setSessions((prev) => prev.filter((s) => s.id !== sessionId));
        showSuccess(
          "Interview Session Deleted",
          "Interview session without an evaluation decision was successfully deleted."
        );
      } catch (error) {
        const msg =
          error instanceof Error
            ? error.message
            : "Failed to delete interview session.";
        showError("Failed to Delete Session", msg);
        throw error;
      }
    },
    [showError, showSuccess]
  );

  return (
    <div className="space-y-4">
      <PageBreadcrumb pageTitle="Interview Sessions" />

      {/* Role-Based Scope Navigation & Data Isolation Header */}
      {role === "INTERVIEWER" ? (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-brand-200 bg-brand-50/50 px-4 py-3 dark:border-brand-500/20 dark:bg-brand-500/10">
          <div className="flex items-center gap-2.5 text-start">
            <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-500/10 text-brand-600 dark:text-brand-400">
              <LockIcon />
            </span>
            <div>
              <h4 className="text-xs font-bold text-gray-900 dark:text-white">
                My Assigned Interview Sessions ({user?.name || "Interviewer"})
              </h4>
              <p className="text-[11px] text-gray-600 dark:text-gray-300">
                Showing interview sessions assigned to you. Your evaluation recommendations will automatically be forwarded to HR for final review.
              </p>
            </div>
          </div>
          <span className="rounded-full bg-white px-2.5 py-1 font-mono text-[10px] font-bold text-brand-700 shadow-2xs dark:bg-gray-900 dark:text-brand-300">
            STRICT USER SCOPE
          </span>
        </div>
      ) : (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-gray-200 bg-white p-2 dark:border-gray-800 dark:bg-gray-900">
          <div className="flex flex-wrap items-center gap-1.5">
            <button
              type="button"
              onClick={() => setSelectedScope("all")}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                effectiveScope === "all"
                  ? "bg-brand-500 text-white shadow-theme-xs"
                  : "text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
              }`}
            >
              All Pipeline Sessions
            </button>
            <button
              type="button"
              onClick={() => setSelectedScope("awaiting_hr")}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                effectiveScope === "awaiting_hr"
                  ? "bg-warning-500 text-white shadow-theme-xs"
                  : "text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
              }`}
            >
              Awaiting HR Follow-Up
            </button>
            {role === "HR" && (
              <button
                type="button"
                onClick={() => setSelectedScope("mine")}
                className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                  effectiveScope === "mine"
                    ? "bg-brand-500 text-white shadow-theme-xs"
                    : "text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
                }`}
              >
                My HR Sessions
              </button>
            )}
          </div>

          <span className="pe-2 text-[11px] text-gray-500 dark:text-gray-400">
            {effectiveScope === "awaiting_hr"
              ? "Showing interviewer recommendations awaiting final HR confirmation"
              : effectiveScope === "mine"
              ? "Showing interview sessions where you are the interviewer"
              : "Showing all recruitment pipeline interview sessions"}
          </span>
        </div>
      )}

      <SessionTable
        sessions={sessions}
        isLoading={isLoading}
        onUploadSession={handleUploadSession}
        onDeleteSession={handleDeleteSession}
        candidates={candidates}
        rubrics={rubrics}
        interviewers={interviewers}
        initialUploadCandidateId={candidateIdParam}
        autoOpenUpload={actionParam === "upload" || Boolean(candidateIdParam)}
        currentUserId={user?.id ?? null}
        currentUserName={user?.name ?? null}
        currentRole={role}
      />
    </div>
  );
}

export default function InterviewSessionsPage() {
  return (
    <Suspense
      fallback={
        <div className="p-8 text-center text-xs text-gray-400">
          Loading Interview Sessions...
        </div>
      }
    >
      <InterviewSessionsContent />
    </Suspense>
  );
}
