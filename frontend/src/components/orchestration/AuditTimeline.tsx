"use client";

import { CheckCircleIcon, ShootingStarIcon, TimeIcon } from "@/icons";
import { AuditEvent } from "@/types/orchestration";
import React from "react";

interface AuditTimelineProps {
  logs: AuditEvent[];
  maxHeight?: string;
}

export default function AuditTimeline({ logs }: AuditTimelineProps) {
  const getBadgeColor = (badge: AuditEvent["status_badge"]) => {
    switch (badge) {
      case "success":
        return "bg-success-50 text-success-700 border-success-200 dark:bg-success-500/15 dark:text-success-400 dark:border-success-500/30";
      case "warning":
        return "bg-warning-50 text-warning-700 border-warning-200 dark:bg-warning-500/15 dark:text-warning-400 dark:border-warning-500/30";
      case "error":
        return "bg-error-50 text-error-700 border-error-200 dark:bg-error-500/15 dark:text-error-400 dark:border-error-500/30";
      default:
        return "bg-brand-50 text-brand-700 border-brand-200 dark:bg-brand-500/15 dark:text-brand-400 dark:border-brand-500/30";
    }
  };

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-5 xl:p-6 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
      <div className="flex items-center justify-between border-b border-gray-100 pb-3 dark:border-gray-800">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300">
            <TimeIcon/>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
              Live Audit Log
            </h3>
            <p className="text-[11px] text-gray-500 dark:text-gray-400">
              The audit trail of the agent transition is recorded immutably.
            </p>
          </div>
        </div>
        <span className="rounded-md bg-gray-100 px-2 py-0.5 text-[10px] font-mono text-gray-600 dark:bg-gray-800 dark:text-gray-300">
          {logs.length} Events
        </span>
      </div>

      {/* Timeline Stream */}
      <div className="mt-4 flow-root">
        <ul className="space-y-4">
          {logs.map((event, eventIdx) => (
            <li key={event.id} className="relative flex gap-x-3">
              {eventIdx !== logs.length - 1 ? (
                <span
                  className="absolute top-4 start-3.5 -bottom-4 w-0.5 bg-gray-200 dark:bg-gray-800"
                  aria-hidden="true"
                />
              ) : null}

              <div className="relative flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 shadow-2xs">
                {event.status_badge === "success" ? (
                  <CheckCircleIcon className="text-success-500" />
                ) : (
                  <ShootingStarIcon className="text-brand-500" />
                )}
              </div>

              <div className="flex-auto rounded-xl border border-gray-100 bg-gray-50/60 p-2.5 dark:border-gray-800/80 dark:bg-gray-800/30">
                <div className="flex items-center justify-between gap-x-2">
                  <div className="text-xs font-semibold text-gray-800 dark:text-white line-clamp-1">
                    {event.title}
                  </div>
                  <time className="shrink-0 font-mono text-[10px] text-gray-400">
                    {event.timestamp}
                  </time>
                </div>

                <p className="mt-0.5 text-[11px] text-gray-500 dark:text-gray-400 leading-normal">
                  {event.description}
                </p>

                <div className="mt-2 flex items-center justify-between pt-1.5 border-t border-gray-200/40 dark:border-gray-800/40 text-[10px]">
                  <span className="text-gray-400">
                    Actor: <strong className="text-gray-700 dark:text-gray-300 font-medium">{event.actor}</strong>
                  </span>
                  <span
                    className={`rounded-md border px-1.5 py-0.2 font-mono text-[9px] font-semibold ${getBadgeColor(
                      event.status_badge
                    )}`}
                  >
                    {event.event_type}
                  </span>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* <div className="mt-6 pt-3 border-t border-gray-100 dark:border-gray-800 text-[10px] text-gray-400 text-center font-mono">
        Audit Log ID: tblm_audit_log • Immutable PostgreSQL Checkpoint
      </div> */}
    </div>
  );
}
