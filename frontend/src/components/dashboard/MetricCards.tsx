"use client";

import React from "react";
import {
  ArrowDownIcon,
  ArrowUpIcon,
  BoltIcon,
  CalenderIcon,
  ChatIcon,
  GroupIcon,
} from "@/icons";
import Badge from "@/components/ui/badge/Badge";
import type { MetricCard } from "@/services/dashboardService";

interface MetricCardsProps {
  metrics: MetricCard[];
}

function getMetricIcon(key: string) {
  switch (key) {
    case "active_candidates":
      return <GroupIcon className="text-brand-600 dark:text-brand-400" />;
    case "interviews_this_week":
      return <CalenderIcon className="text-success-600 dark:text-success-400" />;
    case "pending_approvals":
      return <BoltIcon className="text-warning-600 dark:text-warning-400" />;
    case "active_negotiations":
      return <ChatIcon className="text-purple-600 dark:text-purple-400" />;
    default:
      return <GroupIcon className="text-gray-700 dark:text-gray-300" />;
  }
}

function getIconBg(key: string) {
  switch (key) {
    case "active_candidates":
      return "bg-brand-50 dark:bg-brand-500/10";
    case "interviews_this_week":
      return "bg-success-50 dark:bg-success-500/10";
    case "pending_approvals":
      return "bg-warning-50 dark:bg-warning-500/10";
    case "active_negotiations":
      return "bg-purple-50 dark:bg-purple-500/10";
    default:
      return "bg-gray-100 dark:bg-gray-800";
  }
}

export function MetricCards({ metrics }: MetricCardsProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4 md:gap-6">
      {metrics.map((m) => (
        <div
          key={m.key}
          className="rounded-2xl border border-gray-200 bg-white p-5 md:p-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900"
        >
          <div
            className={`flex h-12 w-12 items-center justify-center rounded-xl ${getIconBg(
              m.key
            )}`}
          >
            {getMetricIcon(m.key)}
          </div>

          <div className="mt-5 flex items-end justify-between">
            <div>
              <span className="text-sm font-medium text-gray-500 dark:text-gray-400">
                {m.label}
              </span>
              <h4 className="mt-1 text-2xl font-bold tracking-tight text-gray-900 dark:text-white">
                {m.value.toLocaleString("id-ID")}
              </h4>
            </div>

            {m.trend !== "neutral" && (
              <Badge
                color={m.trend === "up" ? "success" : "error"}
                size="sm"
                startIcon={
                  m.trend === "up" ? (
                    <ArrowUpIcon className="text-success-600 dark:text-success-500" />
                  ) : (
                    <ArrowDownIcon className="text-error-600 dark:text-error-500" />
                  )
                }
              >
                {Math.abs(m.change_percent)}%
              </Badge>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

