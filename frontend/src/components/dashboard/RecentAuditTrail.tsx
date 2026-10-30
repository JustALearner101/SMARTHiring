"use client";

import React from "react";
import { Link } from "@/i18n/navigation";
import { ListIcon, ArrowRightIcon } from "@/icons";
import Badge from "@/components/ui/badge/Badge";
import type { RecentAudit } from "@/services/dashboardService";

interface RecentAuditTrailProps {
  events: RecentAudit[];
}

export function RecentAuditTrail({ events }: RecentAuditTrailProps) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-5 md:p-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
      <div className="flex items-center justify-between pb-4 border-b border-gray-100 dark:border-gray-800">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300">
            <ListIcon/>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Recent Audit Trail
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              System & Orchestration Action Audit Trail History
            </p>
          </div>
        </div>
        <Link
          href="/audit/logs"
          className="inline-flex items-center gap-1 text-xs font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400"
        >
          View Full Log
          <ArrowRightIcon/>
        </Link>
      </div>

      {events.length === 0 ? (
        <div className="py-8 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            No audit activity has been recorded yet.
          </p>
        </div>
      ) : (
        <div className="mt-4 space-y-2.5">
          {events.map((ev) => (
            <div
              key={ev.id}
              className="flex items-center justify-between rounded-xl border border-gray-100 p-3 text-xs dark:border-gray-800"
            >
              <div className="flex items-center gap-3">
                <Badge color={ev.badge_variant} size="sm">
                  {ev.event_type}
                </Badge>
                <div>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {ev.title}
                  </span>
                  <span className="ms-2 text-gray-500 dark:text-gray-400">
                    by <strong className="font-medium text-gray-700 dark:text-gray-300">{ev.actor}</strong>
                  </span>
                </div>
              </div>
              <span className="text-gray-400 shrink-0">
                {new Date(ev.timestamp).toLocaleString("id-ID", {
                  day: "numeric",
                  month: "short",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

