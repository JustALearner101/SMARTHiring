"use client";

import React from "react";
import { CheckCircleIcon, AlertIcon, TimeIcon, BoltIcon } from "@/icons";
import { NegotiationThread } from "@/types/orchestration";

interface ThreadStatsCardsProps {
  threads: NegotiationThread[];
}

export default function ThreadStatsCards({ threads }: ThreadStatsCardsProps) {
  const activeCount = threads.filter((t) => t.status === "NEGOTIATING").length;
  const scheduledCount = threads.filter((t) => t.status === "SCHEDULED").length;
  const deadlockCount = threads.filter((t) => t.status === "DEADLOCK_ESCALATED").length;
  const avgRounds =
    threads.length > 0
      ? (threads.reduce((acc, t) => acc + t.current_round, 0) / threads.length).toFixed(1)
      : "1.0";

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {/* 1. Active Threads */}
      <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
            Active Triage Threads
          </span>
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-300">
            <BoltIcon />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-bold text-gray-900 dark:text-white">
            {activeCount}
          </span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            in negotiation
          </span>
        </div>
        <p className="mt-2 text-[11px] text-gray-400">
          Autonomous back-and-forth loops active
        </p>
      </div>

      {/* 2. Scheduled by AI */}
      <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
            AI Autonomous Resolved
          </span>
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-success-50 text-success-600 dark:bg-success-500/15 dark:text-success-400">
            <CheckCircleIcon />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-bold text-gray-900 dark:text-white">
            {scheduledCount}
          </span>
          <span className="rounded-full bg-success-50 px-2 py-0.5 text-[10px] font-semibold text-success-700 dark:bg-success-500/15 dark:text-success-400">
            Confirmed
          </span>
        </div>
        <p className="mt-2 text-[11px] text-gray-400">
          No human rescheduling intervention required
        </p>
      </div>

      {/* 3. Deadlock Escalations */}
      <div className="rounded-2xl border border-error-100 bg-error-50/20 p-5 shadow-theme-xs dark:border-error-900/40 dark:bg-error-500/5">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-error-700 dark:text-error-400">
            Deadlock Escalations (LIMITS)
          </span>
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-error-100 text-error-600 dark:bg-error-500/20 dark:text-error-400">
            <AlertIcon />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-bold text-error-800 dark:text-error-300">
            {deadlockCount}
          </span>
          <span className="rounded-full bg-error-100 px-2 py-0.5 text-[10px] font-bold text-error-700 dark:bg-error-500/20 dark:text-error-300">
            Human Required
          </span>
        </div>
        <p className="mt-2 text-[11px] text-error-600/90 dark:text-error-400/80">
          Halted: 3x limit reached or out-of-scope query
        </p>
      </div>

      {/* 4. Avg Negotiation Rounds */}
      <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
            Avg Negotiation Rounds
          </span>
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-warning-50 text-warning-600 dark:bg-warning-500/15 dark:text-warning-400">
            <TimeIcon />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-bold text-gray-900 dark:text-white">
            {avgRounds}
          </span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            / 3.0 Max Limit
          </span>
        </div>
        <p className="mt-2 text-[11px] text-gray-400">
          Enforced hard stop at 3 rounds per candidate
        </p>
      </div>
    </div>
  );
}
