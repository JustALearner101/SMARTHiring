"use client";

import React from "react";
import { Link } from "@/i18n/navigation";
import {
  EnvelopeIcon,
  PaperPlaneIcon,
  BoltIcon,
  TimeIcon,
  UserIcon,
} from "@/icons";

interface EmailSidebarProps {
  currentFolder: "inbox" | "sent" | "starred";
  onSelectFolder: (folder: "inbox" | "sent" | "starred") => void;
  selectedInterviewer: string;
  onSelectInterviewer: (name: string) => void;
  inboxCount: number;
  sentCount: number;
  onReset: () => void;
}

export default function EmailSidebar({
  currentFolder,
  onSelectFolder,
  selectedInterviewer,
  onSelectInterviewer,
  inboxCount,
  sentCount,
  onReset,
}: EmailSidebarProps) {
  return (
    <div className="flex w-full md:w-64 flex-col border-b md:border-b-0 md:border-r border-gray-200 bg-gray-50/70 p-4 dark:border-gray-800 dark:bg-gray-900/40">
      {/* Account Selector*/}
      <div className="mb-5 rounded-xl border border-gray-200 bg-white p-3 dark:border-gray-800 dark:bg-gray-800 shadow-2xs">
        <label className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 flex items-center gap-1.5">
          <UserIcon className="text-brand-500" />
          <span>Active Webmail Account:</span>
        </label>
        <select
          value={selectedInterviewer}
          onChange={(e) => onSelectInterviewer(e.target.value)}
          className="mt-2 w-full rounded-lg border border-gray-300 bg-white px-2.5 py-1.5 text-xs font-medium text-gray-800 focus:border-brand-500 focus:outline-hidden dark:border-gray-700 dark:bg-gray-900 dark:text-white"
        >
          <option value="Budi Santoso">Budi Santoso (VP Eng, WIB)</option>
          <option value="Budi Raharjo">Budi Raharjo (Finance, WITA)</option>
        </select>
        <span className="mt-1.5 block text-[10px] text-gray-500 dark:text-gray-400">
          Domain: company.internal
        </span>
      </div>

      {/* Folders */}
      <div className="space-y-1">
        <button
          onClick={() => onSelectFolder("inbox")}
          className={`flex w-full items-center justify-between rounded-lg px-3 py-2 text-xs font-medium transition-colors ${
            currentFolder === "inbox"
              ? "bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-300 font-semibold"
              : "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
          }`}
        >
          <div className="flex items-center gap-2.5">
            <EnvelopeIcon/>
            <span>Inbox</span>
          </div>
          {inboxCount > 0 && (
            <span className="rounded-full bg-brand-500 px-2 py-0.5 text-[10px] font-semibold text-white">
              {inboxCount}
            </span>
          )}
        </button>

        <button
          onClick={() => onSelectFolder("sent")}
          className={`flex w-full items-center justify-between rounded-lg px-3 py-2 text-xs font-medium transition-colors ${
            currentFolder === "sent"
              ? "bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-300 font-semibold"
              : "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
          }`}
        >
          <div className="flex items-center gap-2.5">
            <PaperPlaneIcon/>
            <span>Sent Messages</span>
          </div>
          {sentCount > 0 && (
            <span className="text-[10px] text-gray-400">
              {sentCount}
            </span>
          )}
        </button>
      </div>

      <hr className="my-5 border-gray-200 dark:border-gray-800" />

      {/* Simulator Quick Links & Reset */}
      <div className="mt-auto space-y-2">
        <Link
          href="/simulator/whatsapp"
          className="flex w-full items-center justify-between rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-800 transition-colors hover:bg-emerald-100 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-300"
        >
          <span>Switch to WhatsApp Simulator</span>
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
        </Link>

        <Link
          href="/orchestration/scheduling"
          className="flex w-full items-center justify-between rounded-lg border border-brand-200 bg-brand-50 px-3 py-2 text-xs font-semibold text-brand-800 transition-colors hover:bg-brand-100 dark:border-brand-500/30 dark:bg-brand-500/10 dark:text-brand-300"
        >
          <div className="flex items-center gap-1.5">
            <BoltIcon/>
            <span>AI Orchestrator</span>
          </div>
          <span className="text-[10px] text-brand-600 dark:text-brand-400">&rarr;</span>
        </Link>

        <button
          onClick={onReset}
          className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-800 dark:bg-gray-800 dark:text-gray-300"
        >
          <TimeIcon/>
          <span>Reset Demo Data</span>
        </button>
      </div>
    </div>
  );
}
