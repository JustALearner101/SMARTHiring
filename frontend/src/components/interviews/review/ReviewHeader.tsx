"use client";

import React from "react";
import { Link, useRouter } from "@/i18n/navigation";
import { InterviewSession } from "@/types/interview";
import ConsentBadge from "../sessions/ConsentBadge";
import { ChevronLeftIcon, UserIcon } from "@/icons";
import { formatWib } from "@/utils/formatDateTime";

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
    <div className="mb-5 rounded-2xl border border-gray-200 bg-white p-4 md:p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        {/* Left: Back button + Candidate and Session metadata */}
        <div className="flex items-start gap-3.5 min-w-0">
          <Link
            href="/interviews/sessions"
            className="flex h-9.5 w-9.5 shrink-0 items-center justify-center rounded-xl border border-gray-200 text-gray-500 hover:bg-gray-50 dark:border-gray-800 dark:text-gray-400 dark:hover:bg-gray-800 transition-colors"
            title="Back to Interview Sessions"
          >
            <ChevronLeftIcon className="rtl:rotate-180" />
          </Link>

          <div className="text-start min-w-0">
            <div className="flex items-baseline gap-2.5 flex-wrap">
              <h2 className="text-lg font-bold text-gray-900 dark:text-white truncate">
                {session.candidate_name}
              </h2>
              <span className="text-xs text-gray-500 dark:text-gray-400 font-mono">
                {session.position} • {session.candidate_code}
              </span>
            </div>

            <div className="mt-1 flex flex-wrap items-center gap-2.5 text-xs text-gray-500 dark:text-gray-400">
              <span className="flex items-center gap-1 text-gray-600 dark:text-gray-300">
                <UserIcon className="text-brand-500 text-sm" />
                <span>Interviewer: <strong>{session.interviewer_name}</strong></span>
              </span>
              <span>•</span>
              <span className="truncate max-w-[240px]" title={session.round_name}>
                {session.round_name}
              </span>
              <span>•</span>
              <span>{formatWib(session.scheduled_at)}</span>
            </div>
          </div>
        </div>

        {/* Right: Compact Session Switcher & Non-Granted Alert if applicable */}
        <div className="flex items-center gap-3 shrink-0">
          {session.consent_status !== "GRANTED" && (
            <ConsentBadge status={session.consent_status} />
          )}

          {switchableSessions.length > 1 && (
            <div className="flex items-center gap-2">
              <label htmlFor="session-switcher" className="text-xs text-gray-500 dark:text-gray-400 hidden sm:inline whitespace-nowrap">
                Session:
              </label>
              <select
                id="session-switcher"
                value={session.id}
                onChange={(e) => {
                  router.replace(`/interviews/review?id=${encodeURIComponent(e.target.value)}`);
                }}
                className="rounded-xl border border-gray-300 bg-gray-50 px-3 py-1.5 text-xs font-medium text-gray-800 focus:border-brand-500 focus:bg-white focus:outline-hidden dark:border-gray-700 dark:bg-gray-800 dark:text-white max-w-[280px] truncate"
              >
                {switchableSessions.map((item) => {
                  const decisionTag = item.hr_decision
                    ? `[${item.hr_decision.decision}]`
                    : "[Pending]";
                  return (
                    <option key={item.id} value={item.id}>
                      #{item.id} — {item.candidate_name} {decisionTag}
                    </option>
                  );
                })}
              </select>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
