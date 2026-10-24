"use client";

import React from "react";
import { ThreadStatus } from "@/types/orchestration";

interface ThreadFiltersProps {
  searchQuery: string;
  onSearchChange: (val: string) => void;
  statusFilter: string;
  onStatusChange: (val: string) => void;
  channelFilter: string;
  onChannelChange: (val: string) => void;
}

export default function ThreadFilters({
  searchQuery,
  onSearchChange,
  statusFilter,
  onStatusChange,
  channelFilter,
  onChannelChange,
}: ThreadFiltersProps) {
  const statuses: { label: string; value: string }[] = [
    { label: "All Status", value: "ALL" },
    { label: "In Negotiation", value: "NEGOTIATING" },
    { label: "Scheduled (Done)", value: "SCHEDULED" },
    { label: "Deadlock Escalated (Urgent)", value: "DEADLOCK_ESCALATED" },
    { label: "Expired SLA", value: "EXPIRED" },
  ];

  const channels: { label: string; value: string }[] = [
    { label: "All Channels", value: "ALL" },
    { label: "WhatsApp", value: "whatsapp" },
    { label: "Email", value: "email" },
  ];

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      {/* Search Input */}
      <div className="relative flex-1 max-w-md">
        <span className="pointer-events-none absolute inset-y-0 start-0 flex items-center ps-3 text-gray-400">
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </span>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search by candidate name, position, or interviewer..."
          className="w-full rounded-xl border border-gray-200 bg-white py-2 ps-9 pe-4 text-xs text-gray-800 placeholder-gray-400 focus:border-brand-500 focus:outline-hidden dark:border-gray-800 dark:bg-gray-900 dark:text-white"
        />
      </div>

      {/* Filter Selects */}
      <div className="flex flex-wrap items-center gap-2">
        <select
          value={statusFilter}
          onChange={(e) => onStatusChange(e.target.value)}
          aria-label="Filter by Status"
          className="rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-medium text-gray-700 shadow-theme-xs focus:border-brand-500 focus:outline-hidden dark:border-gray-800 dark:bg-gray-900 dark:text-gray-300"
        >
          {statuses.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>

        <select
          value={channelFilter}
          onChange={(e) => onChannelChange(e.target.value)}
          aria-label="Filter by Channel"
          className="rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-medium text-gray-700 shadow-theme-xs focus:border-brand-500 focus:outline-hidden dark:border-gray-800 dark:bg-gray-900 dark:text-gray-300"
        >
          {channels.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
