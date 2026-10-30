"use client";

import React from "react";
import { Link } from "@/i18n/navigation";
import { ChatIcon, ArrowRightIcon } from "@/icons";
import Badge from "@/components/ui/badge/Badge";
import type { ActiveNegotiation } from "@/services/dashboardService";

interface ActiveNegotiationsProps {
  threads: ActiveNegotiation[];
}

export function ActiveNegotiations({ threads }: ActiveNegotiationsProps) {
  return (
    <div className="h-full rounded-2xl border border-gray-200 bg-white p-5 md:p-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
      <div className="flex items-center justify-between pb-4 border-b border-gray-100 dark:border-gray-800">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-purple-50 text-purple-600 dark:bg-purple-500/10 dark:text-purple-400">
            <ChatIcon/>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Active Schedule Negotiations
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Ongoing conversation regarding the scheduling of an interview
            </p>
          </div>
        </div>
        <Link
          href="/orchestration/threads"
          className="inline-flex items-center gap-1 text-xs font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400"
        >
          See All
          <ArrowRightIcon/>
        </Link>
      </div>

      {threads.length === 0 ? (
        <div className="py-8 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            There are no ongoing schedule negotiations.
          </p>
        </div>
      ) : (
        <div className="mt-4 space-y-3">
          {threads.map((t) => (
            <Link
              key={t.id}
              href="/orchestration/threads"
              className="block rounded-xl border border-gray-100 p-3.5 transition-colors hover:border-gray-200 hover:bg-gray-50/50 dark:border-gray-800 dark:hover:border-gray-700 dark:hover:bg-gray-800/50"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-sm text-gray-900 dark:text-white">
                    {t.candidate_name}
                  </span>
                  <Badge
                    color={t.channel === "whatsapp" ? "success" : "info"}
                    size="sm"
                  >
                    {t.channel.toUpperCase()}
                  </Badge>
                </div>
                <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                  Round {t.current_round}/{t.max_rounds}
                </span>
              </div>

              <p className="mt-1 text-xs text-gray-600 dark:text-gray-400 line-clamp-1">
                {t.last_message_preview}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

