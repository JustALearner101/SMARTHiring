"use client";

import React, { useCallback, useEffect, useState } from "react";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import SessionTable from "@/components/interviews/sessions/SessionTable";
import {
  listInterviewSessions,
  uploadInterviewFile,
  uploadInterviewSession,
} from "@/services/interviewService";
import { InterviewSession } from "@/types/interview";
import { AudioIcon, LockIcon } from "@/icons";

// Rubric profile seeded in the backend
const DEFAULT_PROFILE_ID = "1";

export default function InterviewSessionsPage() {
  const [sessions, setSessions] = useState<InterviewSession[]>([]);

  useEffect(() => {
    let cancelled = false;

    const loadSessions = async () => {
      try {
        const page = await listInterviewSessions({ page_size: 50 });
        if (!cancelled) {
          setSessions(Array.isArray(page?.items) ? page.items : []);
        }
      } catch (error) {
        console.error("Failed to fetch interview sessions:", error);
      }
    };

    void loadSessions();

    return () => {
      cancelled = true;
    };
  }, []);

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
        const page = await listInterviewSessions({ page_size: 50 });
        if (Array.isArray(page?.items)) {
          setSessions(page.items);
        }
      } catch (error) {
        console.error("Failed polling interview sessions:", error);
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [sessions]);

  const handleUploadSession = useCallback(
    async (localSession: InterviewSession, file?: File | null): Promise<InterviewSession | null> => {
      try {
        let created: InterviewSession;
        if (file) {
          const formData = new FormData();
          formData.append("file", file);
          formData.append("candidate_id", localSession.candidate_id || "1");
          formData.append("profile_id", DEFAULT_PROFILE_ID);
          formData.append("consent_status", localSession.consent_status);
          formData.append(
            "notes",
            `${localSession.round_name} - Interviewer: ${localSession.interviewer_name}`
          );
          created = await uploadInterviewFile(formData);
        } else {
          created = await uploadInterviewSession({
            candidate_id: localSession.candidate_id || "1",
            profile_id: DEFAULT_PROFILE_ID,
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
    []
  );

  return (
    <div>
      <PageBreadcrumb pageTitle="Interview Sessions" />

      {/* Module Overview Banner */}
      <div className="mb-4 rounded-xl border border-gray-200 bg-white p-4 shadow-2xs dark:border-gray-800 dark:bg-gray-900">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
              <AudioIcon />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <span>Interview Sessions &amp; Audio Ingestion</span>
                <span className="rounded bg-brand-50 px-2 py-0.5 text-[10px] font-bold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
                  POST-INTERVIEW PHASE
                </span>
                <span className="rounded bg-purple-50 px-2 py-0.5 text-[10px] font-bold text-purple-700 dark:bg-purple-500/15 dark:text-purple-300">
                  ELEVENLABS SCRIBE
                </span>
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Manage completed interview recordings, candidate consent verification, and speech-to-text pipeline jobs.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="inline-flex items-center gap-1 rounded-md bg-success-50 px-2.5 py-1 font-semibold text-success-700 dark:bg-success-500/15 dark:text-success-300">
              <LockIcon />
              Consent Verification Active
            </span>
          </div>
        </div>
      </div>

      {/* Master Session Table */}
      <SessionTable sessions={sessions} onUploadSession={handleUploadSession} />
    </div>
  );
}
