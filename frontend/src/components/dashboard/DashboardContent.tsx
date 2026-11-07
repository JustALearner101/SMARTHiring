"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/context/AuthContext";
import {
  fetchActivityFeed,
  fetchDashboardSummary,
  fetchUpcomingInterviews,
  type ActivityFeed,
  type DashboardSummary,
  type UpcomingInterview,
} from "@/services/dashboardService";
import { MetricCards } from "./MetricCards";
import { PipelineFunnel } from "./PipelineFunnel";
import { TrendChart } from "./TrendChart";
import { UpcomingInterviewsTable } from "./UpcomingInterviewsTable";
import { PendingApprovals } from "./PendingApprovals";
import { ActiveNegotiations } from "./ActiveNegotiations";
import { RecentAuditTrail } from "./RecentAuditTrail";

export function DashboardContent() {
  const { role } = useAuth();
  const isAdmin = role === "ADMIN";

  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [interviews, setInterviews] = useState<UpcomingInterview[]>([]);
  const [feed, setFeed] = useState<ActivityFeed | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const executeFetch = useCallback(async () => {
    try {
      const [sumRes, intRes, feedRes] = await Promise.all([
        fetchDashboardSummary(),
        fetchUpcomingInterviews(5),
        fetchActivityFeed(),
      ]);
      setSummary(sumRes);
      setInterviews(intRes);
      setFeed(feedRes);
    } catch (err: unknown) {
      console.error("Failed to load dashboard data:", err);
      setError(
        err instanceof Error ? err.message : "An error occurred while loading dashboard data."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    executeFetch();
  }, [executeFetch]);

  const handleRetry = () => {
    setLoading(true);
    setError(null);
    executeFetch();
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center gap-3">
        <div className="h-9 w-9 animate-spin rounded-full border-3 border-brand-500 border-t-transparent" />
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Loading the SmartHiring dashboard summary...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-error-200 bg-error-50/50 p-6 text-center dark:border-error-800 dark:bg-error-950/20">
        <h4 className="text-base font-semibold text-error-700 dark:text-error-400">
          Failed to Load Dashboard
        </h4>
        <p className="mt-1 text-sm text-error-600 dark:text-error-300">
          {error}
        </p>
        <button
          onClick={handleRetry}
          className="mt-4 rounded-lg bg-error-600 px-4 py-2 text-xs font-semibold text-white hover:bg-error-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 w-full max-w-full overflow-hidden">
      {/* 1. Header Ringkasan */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-white sm:text-2xl">
            Dashboard
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400 sm:text-sm">
            A central hub for coordinating recruitment, scheduling interviews, and automated triage
          </p>
        </div>
      </div>

      {/* 2. KPI Metrics Cards */}
      <div className="w-full min-w-0">
        <MetricCards metrics={summary?.metrics ?? []} />
      </div>

      {/* 3. Trend Chart & Pipeline Funnel */}
      <div className="grid grid-cols-12 gap-4 md:gap-6">
        <div className="col-span-12 xl:col-span-7 min-w-0">
          <TrendChart data={summary?.weekly_trend ?? []} />
        </div>
        <div className="col-span-12 xl:col-span-5 min-w-0">
          <PipelineFunnel stages={summary?.pipeline ?? []} />
        </div>
      </div>

      {/* 4. Upcoming Interviews */}
      <div className="w-full min-w-0">
        <UpcomingInterviewsTable interviews={interviews} />
      </div>

      {/* 5. Pending Approvals & Active Negotiations */}
      <div className="grid grid-cols-12 gap-4 md:gap-6">
        <div className="col-span-12 lg:col-span-6 min-w-0">
          <PendingApprovals items={feed?.pending_approvals ?? []} />
        </div>
        <div className="col-span-12 lg:col-span-6 min-w-0">
          <ActiveNegotiations threads={feed?.active_negotiations ?? []} />
        </div>
      </div>

      {/* 6. Recent Audit Trail (ADMIN Role only) */}
      {isAdmin && (
        <div className="w-full min-w-0">
          <RecentAuditTrail events={feed?.recent_audit ?? []} />
        </div>
      )}
    </div>
  );
}
