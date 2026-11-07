"use client";

import React from "react";
import { Link } from "@/i18n/navigation";
import { BoltIcon, ArrowRightIcon } from "@/icons";
import Badge from "@/components/ui/badge/Badge";
import type { PendingApproval } from "@/services/dashboardService";

interface PendingApprovalsProps {
  items: PendingApproval[];
}

export function PendingApprovals({ items }: PendingApprovalsProps) {
  return (
    <div className="h-full rounded-2xl border border-gray-200 bg-white p-5 md:p-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
      <div className="flex items-center justify-between pb-4 border-b border-gray-100 dark:border-gray-800">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-warning-50 text-warning-600 dark:bg-warning-500/10 dark:text-warning-400">
            <BoltIcon/>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Waiting for HR Approval
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              AI Orchestrator Action Plans requiring human approval
            </p>
          </div>
        </div>
        <Link
          href={items.length > 0 ? `/orchestration/scheduling?planId=${items[0].id}` : "/orchestration/scheduling"}
          className="inline-flex items-center gap-1 text-xs font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400"
        >
          Review All
          <ArrowRightIcon/>
        </Link>
      </div>

      {items.length === 0 ? (
        <div className="py-8 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            There are currently no action plans awaiting approval.
          </p>
        </div>
      ) : (
        <div className="mt-4 space-y-3">
          {items.map((item) => (
            <div
              key={item.id}
              className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between rounded-xl border border-gray-100 p-3.5 transition-colors hover:border-gray-200 dark:border-gray-800 dark:hover:border-gray-700"
            >
              <div className="space-y-0.5 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-semibold text-sm text-gray-900 dark:text-white">
                    {item.candidate_name}
                  </span>
                  {item.is_high_impact && (
                    <Badge color="error" size="sm">
                      High Impact
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                  {item.position}
                </p>
                <p className="text-xs text-brand-600 dark:text-brand-400 font-medium truncate">
                  {item.proposed_slot} · {item.items_count} action
                </p>
              </div>

              <Link
                href={`/orchestration/scheduling?planId=${item.id}`}
                className="w-full sm:w-auto text-center shrink-0 rounded-lg bg-brand-500 px-3 py-2 sm:py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-brand-600 transition-colors"
                title="Review proposed schedule and action items for approval"
              >
                Review &amp; Approve
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

