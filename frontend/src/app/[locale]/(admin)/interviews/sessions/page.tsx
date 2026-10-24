"use client";

import React from "react";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import SessionTable from "@/components/interviews/sessions/SessionTable";
import { initialInterviewSessions } from "@/data/mockInterviewData";
import { AudioIcon, LockIcon } from "@/icons";

export default function InterviewSessionsPage() {
  return (
    <div>
      <PageBreadcrumb pageTitle="Interview Sessions" />

      {/* Module Overview Banner */}
      <div className="mb-4 rounded-xl border border-gray-200 bg-white p-4 shadow-2xs dark:border-gray-800 dark:bg-gray-900">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
              <AudioIcon/>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <span>Interview Sessions & Audio Ingestion</span>
                <span className="rounded bg-brand-50 px-2 py-0.5 text-[10px] font-bold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
                  POST-INTERVIEW PHASE
                </span>
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Manage completed interview recordings, candidate consent verification, and speech-to-text pipeline jobs.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="inline-flex items-center gap-1 rounded-md bg-success-50 px-2.5 py-1 font-semibold text-success-700 dark:bg-success-500/15 dark:text-success-300">
              <LockIcon/>
              Consent Verification Active
            </span>
          </div>
        </div>
      </div>

      {/* Master Session Table */}
      <SessionTable initialSessions={initialInterviewSessions} />
    </div>
  );
}
