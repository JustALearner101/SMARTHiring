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
      <SessionTable sessions={sessions} onUploadSession={handleUploadSession} />
    </div>
  );
}
