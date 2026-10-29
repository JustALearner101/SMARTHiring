"use client";

import { Link } from "@/i18n/navigation";
import {
  ArrowRightIcon,
  CheckCircleIcon,
  CloseIcon,
  ShootingStarIcon,
  TimeIcon,
} from "@/icons";
import { AuditEvent } from "@/types/orchestration";
import React, { useMemo, useState } from "react";

interface AuditTimelineProps {
  logs: AuditEvent[];
  maxHeight?: string;
}

type AuditCategory = "ALL" | "APPROVALS" | "DISPATCHES" | "GUARDRAILS";

export default function AuditTimeline({ logs, maxHeight }: AuditTimelineProps) {
  const [category, setCategory] = useState<AuditCategory>("ALL");

  const getBadgeColor = (badge: AuditEvent["status_badge"]) => {
    switch (badge) {
      case "success":
        return "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-500/15 dark:text-emerald-400 dark:border-emerald-500/30";
      case "warning":
        return "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-500/15 dark:text-amber-400 dark:border-amber-500/30";
      case "error":
        return "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-500/15 dark:text-rose-400 dark:border-rose-500/30";
      default:
        return "bg-brand-50 text-brand-700 border-brand-200 dark:bg-brand-500/15 dark:text-brand-400 dark:border-brand-500/30";
    }
  };

  const getStatusIcon = (badge: AuditEvent["status_badge"]) => {
    switch (badge) {
      case "success":
        return <CheckCircleIcon className="text-emerald-500" />;
      case "warning":
        return <TimeIcon className="text-amber-500" />;
      case "error":
        return <CloseIcon className="text-rose-500" />;
      default:
        return <ShootingStarIcon className="text-brand-500" />;
    }
  };

  // Counts for Category Pills
  const counts = useMemo(() => {
    let approvals = 0;
    let dispatches = 0;
    let guardrails = 0;

    for (const log of logs) {
      const type = log.event_type.toUpperCase();
      if (/APPROV|UNDO|REJECT/.test(type)) approvals++;
      if (/DISPATCH|EXECUT|EMAIL|WHATSAPP|CALENDAR/.test(type)) dispatches++;
      if (/GUARDRAIL|VALIDAT|SOURCE|DISAMBIG|LIMIT/.test(type)) guardrails++;
    }

    return {
      all: logs.length,
      approvals,
      dispatches,
      guardrails,
    };
  }, [logs]);

  // Filtered Events
  const filteredLogs = useMemo(() => {
    if (category === "ALL") return logs;
    return logs.filter((log) => {
      const type = log.event_type.toUpperCase();
      if (category === "APPROVALS") return /APPROV|UNDO|REJECT/.test(type);
      if (category === "DISPATCHES")
        return /DISPATCH|EXECUT|EMAIL|WHATSAPP|CALENDAR/.test(type);
      if (category === "GUARDRAILS")
        return /GUARDRAIL|VALIDAT|SOURCE|DISAMBIG|LIMIT/.test(type);
      return true;
    });
  }, [logs, category]);

  const heightStyle = maxHeight ?? "max-h-[calc(100vh-6.5rem)] min-h-[500px]";

  return (
    <div
      className={`flex flex-col rounded-2xl border border-gray-200 bg-white p-5 xl:p-6 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs ${heightStyle}`}
    >
      {/* Header (Non-shrinking) */}
      <div className="shrink-0 border-b border-gray-100 pb-3.5 dark:border-gray-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300">
              <TimeIcon/>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-gray-900 dark:text-white">
                  Live Audit Log
                </h3>
                <div className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-2 py-0.5 border border-emerald-200/60 dark:bg-emerald-500/10 dark:border-emerald-500/30">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                  </span>
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400">
                    Live
                  </span>
                </div>
              </div>
              <p className="text-[11px] text-gray-500 dark:text-gray-400">
                Pillar 5 (RECORD) &bull; PostgreSQL Immutable Ledger
              </p>
            </div>
          </div>
          <span className="rounded-md bg-gray-100 px-2 py-0.5 text-[10px] font-mono font-semibold text-gray-600 dark:bg-gray-800 dark:text-gray-300">
            {filteredLogs.length} Events
          </span>
        </div>

        {/* Category Filter Tabs */}
        <div className="mt-3.5 flex flex-wrap items-center gap-1.5">
          <button
            type="button"
            onClick={() => setCategory("ALL")}
            className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[11px] font-semibold transition-all ${
              category === "ALL"
                ? "bg-gray-900 text-white dark:bg-white dark:text-gray-900 shadow-2xs"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200/80 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700/80"
            }`}
          >
            <span>All</span>
            <span
              className={`rounded-md px-1 py-0.2 text-[9px] font-mono ${
                category === "ALL"
                  ? "bg-white/20 text-white dark:bg-gray-900/20 dark:text-gray-900"
                  : "bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300"
              }`}
            >
              {counts.all}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setCategory("APPROVALS")}
            className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[11px] font-semibold transition-all ${
              category === "APPROVALS"
                ? "bg-brand-600 text-white shadow-2xs"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200/80 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700/80"
            }`}
          >
            <span>Approvals</span>
            <span
              className={`rounded-md px-1 py-0.2 text-[9px] font-mono ${
                category === "APPROVALS"
                  ? "bg-white/25 text-white"
                  : "bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300"
              }`}
            >
              {counts.approvals}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setCategory("DISPATCHES")}
            className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[11px] font-semibold transition-all ${
              category === "DISPATCHES"
                ? "bg-emerald-600 text-white shadow-2xs"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200/80 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700/80"
            }`}
          >
            <span>Dispatches</span>
            <span
              className={`rounded-md px-1 py-0.2 text-[9px] font-mono ${
                category === "DISPATCHES"
                  ? "bg-white/25 text-white"
                  : "bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300"
              }`}
            >
              {counts.dispatches}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setCategory("GUARDRAILS")}
            className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[11px] font-semibold transition-all ${
              category === "GUARDRAILS"
                ? "bg-purple-600 text-white shadow-2xs"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200/80 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700/80"
            }`}
          >
            <span>Guardrails</span>
            <span
              className={`rounded-md px-1 py-0.2 text-[9px] font-mono ${
                category === "GUARDRAILS"
                  ? "bg-white/25 text-white"
                  : "bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300"
              }`}
            >
              {counts.guardrails}
            </span>
          </button>
        </div>
      </div>

      {/* Scrollable Timeline Stream (flex-1 + custom-scrollbar) */}
      <div className="mt-4 flex-1 overflow-y-auto custom-scrollbar pe-1">
        {filteredLogs.length === 0 ? (
          <div className="flex h-full min-h-[220px] flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 p-6 text-center dark:border-gray-800">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gray-100 text-gray-400 dark:bg-gray-800">
              <TimeIcon/>
            </div>
            <p className="mt-2.5 text-xs font-semibold text-gray-700 dark:text-gray-300">
              No events in this category
            </p>
            <p className="text-[11px] text-gray-500 dark:text-gray-400">
              Trigger an orchestration action to log state transitions.
            </p>
          </div>
        ) : (
          <ul className="space-y-3.5">
            {filteredLogs.map((event, eventIdx) => (
              <li
                key={`${event.id}-${eventIdx}`}
                className="relative flex gap-x-3"
              >
                {eventIdx !== filteredLogs.length - 1 ? (
                  <span
                    className="absolute top-4 start-3.5 -bottom-4 w-0.5 bg-gray-200 dark:bg-gray-800"
                    aria-hidden="true"
                  />
                ) : null}

                <div className="relative flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 shadow-2xs">
                  {getStatusIcon(event.status_badge)}
                </div>

                <div className="flex-auto rounded-xl border border-gray-100 bg-gray-50/70 p-3 dark:border-gray-800/80 dark:bg-gray-800/40 hover:border-gray-200 dark:hover:border-gray-700 transition-colors">
                  <div className="flex items-center justify-between gap-x-2">
                    <div className="text-xs font-bold text-gray-900 dark:text-white line-clamp-1">
                      {event.title}
                    </div>
                    <time className="shrink-0 font-mono text-[10px] text-gray-400">
                      {event.timestamp}
                    </time>
                  </div>

                  <p className="mt-1 text-[11px] text-gray-600 dark:text-gray-300 leading-relaxed">
                    {event.description}
                  </p>

                  <div className="mt-2.5 flex items-center justify-between pt-2 border-t border-gray-200/50 dark:border-gray-800/50 text-[10px]">
                    <span className="text-gray-400">
                      Actor:{" "}
                      <strong className="text-gray-700 dark:text-gray-200 font-semibold">
                        {event.actor}
                      </strong>
                    </span>
                    <span
                      className={`rounded-md border px-1.5 py-0.5 font-mono text-[9px] font-bold ${getBadgeColor(
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
        )}
      </div>

      {/* Sticky Bottom Footer (Non-shrinking) */}
      <div className="shrink-0 border-t border-gray-100 pt-3 mt-3 dark:border-gray-800">
        <Link
          href="/audit/logs"
          className="group flex items-center justify-between rounded-xl bg-gray-50 px-3 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-100 dark:bg-gray-800/60 dark:text-gray-300 dark:hover:bg-gray-800 transition-colors"
        >
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-brand-500"></span>
            <span>View Full SHA-256 Ledger</span>
          </span>
          <ArrowRightIcon className="text-gray-400 group-hover:text-brand-500 group-hover:translate-x-0.5 transition-all" />
        </Link>
      </div>
    </div>
  );
}
