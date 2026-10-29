"use client";

import React from "react";
import { Link, useRouter } from "@/i18n/navigation";
import { InterviewSession } from "@/types/interview";
import ConsentBadge from "../sessions/ConsentBadge";
import { CheckCircleIcon, ChevronLeftIcon, TimeIcon, UserIcon } from "@/icons";

interface ReviewHeaderProps {
  session: InterviewSession;
  allSessions?: InterviewSession[];
}

export default function ReviewHeader({
  session,
  allSessions = [],
}: ReviewHeaderProps) {
  const router = useRouter();

  const switchableSessions = allSessions.filter(
    (s) => s.consent_status === "GRANTED"
  );

  return (
    <div className="mb-5 rounded-2xl border border-gray-200 bg-white p-4 md:p-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900 space-y-4">
      {/* Integrated Session Switcher Bar */}
      {switchableSessions.length > 1 && (
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-gray-100 pb-3.5 dark:border-gray-800">
          <span className="text-xs font-semibold text-gray-600 dark:text-gray-300">
            Active Session Workspace ({switchableSessions.length} Recorded Sessions):
          </span>
          <select
            value={session.id}
            onChange={(e) => {
              router.replace(`/interviews/review?id=${encodeURIComponent(e.target.value)}`);
            }}
            className="w-full sm:w-auto sm:min-w-[340px] rounded-xl border border-gray-300 bg-gray-50 px-3 py-1.5 text-xs font-medium text-gray-800 focus:border-brand-500 focus:bg-white focus:outline-hidden dark:border-gray-700 dark:bg-gray-800 dark:text-white"
          >
            {switchableSessions.map((item) => {
              const decisionTag = item.hr_decision
                ? `[${item.hr_decision.decision}]`
                : "[Pending Decision]";
              return (
                <option key={item.id} value={item.id}>
                  #{item.id} — {item.candidate_name} ({item.candidate_code}) • {item.round_name}{" "}
                  {decisionTag}
                </option>
              );
            })}
          </select>
        </div>
      )}

      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-start gap-3.5">
          <Link
            href="/interviews/sessions"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-gray-200 text-gray-500 hover:bg-gray-50 dark:border-gray-800 dark:text-gray-400 dark:hover:bg-gray-800"
            title="Back to Interview Sessions"
          >
            <ChevronLeftIcon className="rtl:rotate-180" />
          </Link>

          <div className="text-start">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                {session.candidate_name}
              </h2>
              <span className="rounded-md bg-brand-50 px-2 py-0.5 font-mono text-xs font-bold text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
                {session.candidate_code}
              </span>
              <span className="rounded-md bg-gray-100 px-2 py-0.5 text-xs text-gray-700 dark:bg-gray-800 dark:text-gray-300">
                {session.position}
              </span>
            </div>

            <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
              <span className="flex items-center gap-1">
                <UserIcon className="text-brand-500" />
                Interviewer: <strong>{session.interviewer_name}</strong> ({session.interviewer_role})
              </span>
              <span>&bull;</span>
              <span>{session.round_name}</span>
              <span>&bull;</span>
              <span>{session.scheduled_at}</span>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <ConsentBadge status={session.consent_status} />

          <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300 border border-brand-200 dark:border-brand-500/30">
            <CheckCircleIcon className="text-brand-600" />
            <span>SOURCES: 100% Cited</span>
          </span>

          <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-3 py-1 font-mono text-xs text-gray-700 dark:bg-gray-800 dark:text-gray-300">
            <TimeIcon />
            <span>Duration: {session.audio_duration || "45:20"}</span>
          </span>
        </div>
      </div>
    </div>
  );
}
