"use client";

import React from "react";
import { SimulatedEmail } from "@/types/simulator";
import { EnvelopeIcon } from "@/icons";

interface EmailListProps {
  emails: SimulatedEmail[];
  activeEmailId: string;
  onSelectEmail: (id: string) => void;
}

export default function EmailList({
  emails,
  activeEmailId,
  onSelectEmail,
}: EmailListProps) {
  if (emails.length === 0) {
    return (
      <div className="flex h-64 w-full md:w-80 flex-col items-center justify-center p-6 text-center text-gray-400 border-r border-gray-200 dark:border-gray-800">
        <EnvelopeIcon className="text-gray-300 dark:text-gray-600 mb-2" />
        <p className="text-xs">No emails in this folder</p>
      </div>
    );
  }

  return (
    <div className="w-full md:w-80 border-b md:border-b-0 md:border-r border-gray-200 bg-white overflow-y-auto max-h-[600px] dark:border-gray-800 dark:bg-gray-900">
      <div className="divide-y divide-gray-100 dark:divide-gray-800">
        {emails.map((email) => {
          const isActive = email.id === activeEmailId;
          return (
            <div
              key={email.id}
              onClick={() => onSelectEmail(email.id)}
              className={`cursor-pointer p-4 transition-colors ${
                isActive
                  ? "bg-brand-50/70 border-l-4 border-brand-500 dark:bg-brand-500/10"
                  : "hover:bg-gray-50 dark:hover:bg-gray-800/60"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-1.5 min-w-0">
                  {!email.is_read && (
                    <span className="h-2 w-2 shrink-0 rounded-full bg-brand-500" />
                  )}
                  <span
                    className={`truncate text-xs font-semibold ${
                      !email.is_read
                        ? "text-gray-900 dark:text-white"
                        : "text-gray-700 dark:text-gray-300"
                    }`}
                  >
                    {email.sender_name}
                  </span>
                </div>
                <span className="shrink-0 text-[10px] text-gray-400">
                  {email.sent_at}
                </span>
              </div>

              <h5
                className={`mt-1 text-xs truncate ${
                  !email.is_read
                    ? "font-semibold text-gray-900 dark:text-white"
                    : "text-gray-700 dark:text-gray-300"
                }`}
              >
                {email.subject}
              </h5>

              <p className="mt-1 line-clamp-2 text-[11px] text-gray-500 dark:text-gray-400">
                {email.body_text}
              </p>

              <div className="mt-2 flex flex-wrap gap-1">
                {email.tags.map((tag, idx) => (
                  <span
                    key={idx}
                    className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
                      tag === "High-Impact"
                        ? "bg-error-50 text-error-700 dark:bg-error-500/15 dark:text-error-400"
                        : tag === "Reschedule"
                        ? "bg-warning-50 text-warning-700 dark:bg-warning-500/15 dark:text-warning-400"
                        : "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300"
                    }`}
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
