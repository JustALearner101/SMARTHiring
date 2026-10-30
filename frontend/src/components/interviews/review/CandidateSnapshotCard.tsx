"use client";

import React from "react";
import { InterviewSession } from "@/types/interview";
import { AudioIcon, LockIcon, UserIcon } from "@/icons";

interface CandidateSnapshotCardProps {
  session: InterviewSession;
}

export default function CandidateSnapshotCard({
  session,
}: CandidateSnapshotCardProps) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-4 md:p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
      <div className="flex items-center justify-between border-b border-gray-100 pb-3 dark:border-gray-800">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-400">
            <UserIcon />
          </div>
          <h4 className="text-xs font-bold text-gray-900 dark:text-white">
            Interview Provenance & Candidate Info
          </h4>
        </div>
      </div>

      {/* Profile Details & Metadata */}
      <div className="mt-3 space-y-2.5 text-xs">
        <div className="flex items-center justify-between text-gray-600 dark:text-gray-400">
          <span className="text-[11px]">Applied Position:</span>
          <span className="font-semibold text-gray-800 dark:text-gray-200">{session.position}</span>
        </div>

        <div className="flex items-center justify-between text-gray-600 dark:text-gray-400">
          <span className="text-[11px]">Evaluation Round:</span>
          <span className="font-medium text-gray-800 dark:text-gray-200 truncate max-w-[200px]" title={session.round_name}>
            {session.round_name}
          </span>
        </div>

        <hr className="border-gray-100 dark:border-gray-800" />

        {/* Source File & Audit Notice */}
        <div className="rounded-xl bg-gray-50/80 p-2.5 dark:bg-gray-800/40 space-y-1.5">
          <div className="flex items-center justify-between text-[11px]">
            <span className="flex items-center gap-1 text-gray-500 dark:text-gray-400">
              <AudioIcon className="text-brand-500" />
              <span>Recording File:</span>
            </span>
            <span className="font-mono text-gray-700 dark:text-gray-300 truncate max-w-[180px]">
              {session.audio_url?.split("/").pop() || "recording.mp3"}
            </span>
          </div>

          <div className="flex items-center justify-between text-[11px]">
            <span className="flex items-center gap-1 text-gray-500 dark:text-gray-400">
              <LockIcon className="text-success-500" />
              <span>Consent Notice:</span>
            </span>
            <span className="font-mono text-[10px] text-success-700 dark:text-success-400">
              {session.consent_notice_version || "v2.1-id-consent"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
