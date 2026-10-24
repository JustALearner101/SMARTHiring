"use client";

import React from "react";
import { Link } from "@/i18n/navigation";
import { InterviewSession } from "@/types/interview";
import ConsentBadge from "../sessions/ConsentBadge";
import { ChevronLeftIcon, TimeIcon, CheckCircleIcon, UserIcon } from "@/icons";

interface ReviewHeaderProps {
  session: InterviewSession;
}

export default function ReviewHeader({ session }: ReviewHeaderProps) {
  return (
    <div className="mb-5 rounded-2xl border border-gray-200 bg-white p-4 md:p-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-start gap-3.5">
          <Link
            href="/interviews/sessions"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-gray-200 text-gray-500 hover:bg-gray-50 dark:border-gray-800 dark:text-gray-400 dark:hover:bg-gray-800"
            title="Back to Sessions"
          >
            <ChevronLeftIcon/>
          </Link>

          <div>
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
            <TimeIcon/>
            <span>Duration: {session.audio_duration}</span>
          </span>
        </div>
      </div>
    </div>
  );
}
