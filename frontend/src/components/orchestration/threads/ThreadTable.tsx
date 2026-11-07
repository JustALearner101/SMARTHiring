"use client";

import React from "react";
import { NegotiationThread } from "@/types/orchestration";
import {
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { AlertIcon, CheckCircleIcon, TimeIcon, ArrowRightIcon, BoltIcon } from "@/icons";
import { Link } from "@/i18n/navigation";
import TablePagination from "@/components/common/TablePagination";

interface ThreadTableProps {
  threads: NegotiationThread[];
  onSelectThread: (thread: NegotiationThread) => void;
  currentPage?: number;
  pageSize?: number;
  totalItems?: number;
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  pageSizeOptions?: number[];
  isLoading?: boolean;
}

export default function ThreadTable({
  threads,
  onSelectThread,
  currentPage,
  pageSize,
  totalItems,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions,
  isLoading = false,
}: ThreadTableProps) {
  const getStatusBadge = (status: NegotiationThread["status"]) => {
    switch (status) {
      case "NEGOTIATING":
        return (
          <span className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-semibold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
            <span className="h-1.5 w-1.5 rounded-full bg-brand-500 animate-pulse" />
            In Negotiation
          </span>
        );
      case "SCHEDULED":
        return (
          <span className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full bg-success-50 px-2.5 py-0.5 text-xs font-semibold text-success-700 dark:bg-success-500/15 dark:text-success-400">
            <CheckCircleIcon />
            Scheduled
          </span>
        );
      case "DEADLOCK_ESCALATED":
        return (
          <span className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full bg-error-50 px-2.5 py-0.5 text-xs font-bold text-error-700 dark:bg-error-500/15 dark:text-error-400">
            <AlertIcon />
            Deadlock Escalated
          </span>
        );
      case "EXPIRED":
        return (
          <span className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-600 dark:bg-gray-800 dark:text-gray-400">
            <TimeIcon />
            SLA Expired
          </span>
        );
    }
  };

  const getChannelBadge = (channel: NegotiationThread["candidate_channel"]) => {
    if (channel === "whatsapp") {
      return (
        <span className="inline-flex items-center gap-1 rounded bg-success-50 px-1.5 py-0.5 text-[10px] font-bold text-success-700 dark:bg-success-500/15 dark:text-success-400">
          WhatsApp
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 rounded bg-brand-50 px-1.5 py-0.5 text-[10px] font-bold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
        Email
      </span>
    );
  };

  return (
    <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
      {/* 1. Mobile Card List View (< md) */}
      <div className="block md:hidden divide-y divide-gray-100 dark:divide-gray-800">
        {threads.length === 0 ? (
          <div className="py-8 text-center text-xs text-gray-500 dark:text-gray-400">
            No negotiation threads match the selected filters.
          </div>
        ) : (
          threads.map((thread) => {
            const isMax = thread.current_round >= thread.max_rounds;
            const isDeadlock = thread.status === "DEADLOCK_ESCALATED";

            return (
              <div
                key={thread.id}
                className={`p-4 transition-colors ${
                  isDeadlock ? "bg-error-50/20 dark:bg-error-500/5" : ""
                }`}
              >
                {/* Header: Candidate & Status Badge */}
                <div className="flex items-start justify-between gap-2.5">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-sm font-bold text-gray-900 dark:text-white">
                        {thread.candidate_name}
                      </span>
                      {getChannelBadge(thread.candidate_channel)}
                    </div>
                    <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400 truncate">
                      {thread.candidate_position}
                    </p>
                  </div>
                  <div className="shrink-0">
                    {getStatusBadge(thread.status)}
                  </div>
                </div>

                {/* Info Grid: Interviewer & Negotiation Round */}
                <div className="mt-3 grid grid-cols-2 gap-2.5 rounded-xl bg-gray-50/80 p-2.5 dark:bg-gray-800/40 border border-gray-100 dark:border-gray-800">
                  <div className="min-w-0">
                    <span className="text-[10px] font-semibold uppercase text-gray-400">
                      Interviewer
                    </span>
                    <p className="text-xs font-medium text-gray-900 dark:text-white truncate">
                      {thread.interviewer_name}
                    </p>
                    <p className="text-[10px] text-gray-500 dark:text-gray-400 truncate">
                      {thread.interviewer_dept} •{" "}
                      <span className="font-mono font-semibold text-brand-600 dark:text-brand-400">
                        {thread.interviewer_timezone}
                      </span>
                    </p>
                  </div>

                  <div>
                    <span className="text-[10px] font-semibold uppercase text-gray-400">
                      Negotiation Round
                    </span>
                    <div className="mt-1 flex items-center gap-1">
                      {[1, 2, 3].map((step) => {
                        const isFilled = step <= thread.current_round;
                        let color = "bg-gray-200 dark:bg-gray-700";
                        if (isFilled) {
                          if (isDeadlock || isMax) color = "bg-error-500";
                          else if (thread.current_round === 2) color = "bg-warning-500";
                          else color = "bg-success-500";
                        }
                        return (
                          <span
                            key={step}
                            className={`h-1.5 w-5 rounded-full transition-all ${color}`}
                          />
                        );
                      })}
                    </div>
                    <p className="mt-0.5 text-[10px] font-semibold text-gray-600 dark:text-gray-400">
                      R{thread.current_round}/{thread.max_rounds} Max
                      {isMax && (
                        <span className="ms-1 font-bold text-error-600 dark:text-error-400">
                          (LIMIT)
                        </span>
                      )}
                    </p>
                  </div>
                </div>

                {/* Last Activity Preview */}
                <div className="mt-2.5">
                  <span className="text-[10px] font-semibold uppercase text-gray-400">
                    Last Activity
                  </span>
                  <p className="text-xs text-gray-800 dark:text-gray-200 line-clamp-2 mt-0.5">
                    {thread.last_message_preview}
                  </p>
                  <span className="mt-0.5 block text-[10px] text-gray-400">
                    {new Date(thread.last_activity_at).toLocaleTimeString("id-ID", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}{" "}
                    WIB
                  </span>
                </div>

                {/* Actions */}
                <div className="mt-3.5 flex items-center gap-2">
                  {isDeadlock ? (
                    <>
                      <Link
                        href={`/orchestration/scheduling?thread_id=${thread.id}&action=triage&candidate_id=${thread.candidate_id}&interviewer_id=${thread.interviewer_id}&interviewer_name=${encodeURIComponent(thread.interviewer_name)}`}
                        className="flex-1 inline-flex items-center justify-center gap-1 rounded-xl bg-brand-600 px-3 py-2 text-xs font-bold text-white shadow-theme-xs hover:bg-brand-700 transition-colors"
                      >
                        <BoltIcon/>
                        <span>Schedule Triage</span>
                      </Link>
                      <button
                        onClick={() => onSelectThread(thread)}
                        className="inline-flex items-center justify-center gap-1 rounded-xl bg-error-600 px-3 py-2 text-xs font-bold text-white shadow-theme-xs hover:bg-error-700 transition-colors"
                      >
                        <AlertIcon />
                        <span>Intervene</span>
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => onSelectThread(thread)}
                      className="w-full inline-flex items-center justify-center gap-1.5 rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-semibold text-gray-700 shadow-theme-xs hover:bg-gray-50 dark:border-gray-800 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 transition-colors"
                    >
                      <span>View Thread</span>
                      <ArrowRightIcon />
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* 2. Desktop Table View (>= md) */}
      <div className="hidden md:block overflow-x-auto">
        <Table className="min-w-[850px]">
          <TableHeader className="border-b border-gray-100 dark:border-gray-800">
            <TableRow>
              <TableCell isHeader className="py-3 px-4 text-start text-xs font-semibold text-gray-500 dark:text-gray-400 whitespace-nowrap">
                Candidate
              </TableCell>
              <TableCell isHeader className="py-3 px-4 text-start text-xs font-semibold text-gray-500 dark:text-gray-400 whitespace-nowrap">
                Interviewer
              </TableCell>
              <TableCell isHeader className="py-3 px-4 text-start text-xs font-semibold text-gray-500 dark:text-gray-400 whitespace-nowrap">
                Negotiation Round (LIMITS)
              </TableCell>
              <TableCell isHeader className="py-3 px-4 text-start text-xs font-semibold text-gray-500 dark:text-gray-400 whitespace-nowrap">
                Status
              </TableCell>
              <TableCell isHeader className="py-3 px-4 text-start text-xs font-semibold text-gray-500 dark:text-gray-400 whitespace-nowrap">
                Last Activity
              </TableCell>
              <TableCell isHeader className="py-3 px-4 text-end text-xs font-semibold text-gray-500 dark:text-gray-400 whitespace-nowrap">
                Action
              </TableCell>
            </TableRow>
          </TableHeader>
          <TableBody className="divide-y divide-gray-100 dark:divide-gray-800">
            {threads.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="py-8 text-center text-xs text-gray-500 dark:text-gray-400">
                  No negotiation threads match the selected filters.
                </TableCell>
              </TableRow>
            ) : (
              threads.map((thread) => {
                const isMax = thread.current_round >= thread.max_rounds;
                const isDeadlock = thread.status === "DEADLOCK_ESCALATED";

                return (
                  <TableRow
                    key={thread.id}
                    className={`transition-colors hover:bg-gray-50/60 dark:hover:bg-gray-800/40 ${
                      isDeadlock ? "bg-error-50/20 dark:bg-error-500/5" : ""
                    }`}
                  >
                    {/* Candidate */}
                    <TableCell className="py-3.5 px-4 whitespace-nowrap">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-gray-900 dark:text-white">
                            {thread.candidate_name}
                          </span>
                          {getChannelBadge(thread.candidate_channel)}
                        </div>
                        <p className="mt-0.5 text-[11px] text-gray-500 dark:text-gray-400 truncate max-w-[200px]">
                          {thread.candidate_position}
                        </p>
                      </div>
                    </TableCell>

                    {/* Interviewer */}
                    <TableCell className="py-3.5 px-4 whitespace-nowrap">
                      <div>
                        <span className="text-xs font-medium text-gray-900 dark:text-white">
                          {thread.interviewer_name}
                        </span>
                        <div className="mt-0.5 flex items-center gap-1.5 text-[11px] text-gray-500 dark:text-gray-400">
                          <span>{thread.interviewer_dept}</span>
                          <span>•</span>
                          <span className="font-mono font-semibold text-brand-600 dark:text-brand-400">
                            {thread.interviewer_timezone}
                          </span>
                        </div>
                      </div>
                    </TableCell>

                    {/* Round Indicator */}
                    <TableCell className="py-3.5 px-4 whitespace-nowrap">
                      <div className="space-y-1">
                        <div className="flex items-center gap-1">
                          {[1, 2, 3].map((step) => {
                            const isFilled = step <= thread.current_round;
                            let color = "bg-gray-200 dark:bg-gray-700";
                            if (isFilled) {
                              if (isDeadlock || isMax) color = "bg-error-500";
                              else if (thread.current_round === 2) color = "bg-warning-500";
                              else color = "bg-success-500";
                            }
                            return (
                              <span
                                key={step}
                                className={`h-2 w-6 rounded-full transition-all ${color}`}
                              />
                            );
                          })}
                        </div>
                        <p className="text-[10px] font-semibold text-gray-600 dark:text-gray-400">
                          Round {thread.current_round} of {thread.max_rounds} Max
                          {isMax && (
                            <span className="ms-1 font-bold text-error-600 dark:text-error-400">
                              (LIMIT REACHED)
                            </span>
                          )}
                        </p>
                      </div>
                    </TableCell>

                    {/* Status */}
                    <TableCell className="py-3.5 px-4 whitespace-nowrap">
                      {getStatusBadge(thread.status)}
                    </TableCell>

                    {/* Last Activity */}
                    <TableCell className="py-3.5 px-4">
                      <div className="max-w-[240px]">
                        <p className="text-xs text-gray-800 dark:text-gray-200 line-clamp-1">
                          {thread.last_message_preview}
                        </p>
                        <span className="mt-0.5 block text-[10px] text-gray-400">
                          {new Date(thread.last_activity_at).toLocaleTimeString("id-ID", {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}{" "}
                          WIB
                        </span>
                      </div>
                    </TableCell>

                    {/* Action */}
                    <TableCell className="py-3.5 px-4 text-end whitespace-nowrap">
                      {isDeadlock ? (
                        <div className="flex items-center justify-end gap-1.5">
                          <Link
                            href={`/orchestration/scheduling?thread_id=${thread.id}&action=triage&candidate_id=${thread.candidate_id}&interviewer_id=${thread.interviewer_id}&interviewer_name=${encodeURIComponent(thread.interviewer_name)}`}
                            className="inline-flex items-center gap-1 rounded-xl bg-brand-600 px-2.5 py-1.5 text-xs font-bold text-white shadow-theme-xs hover:bg-brand-700 transition-colors"
                          >
                            <BoltIcon/>
                            <span>Schedule Triage</span>
                          </Link>
                          <button
                            onClick={() => onSelectThread(thread)}
                            className="inline-flex items-center gap-1 rounded-xl bg-error-600 px-2.5 py-1.5 text-xs font-bold text-white shadow-theme-xs hover:bg-error-700 transition-colors"
                          >
                            <AlertIcon />
                            <span>Intervene</span>
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => onSelectThread(thread)}
                          className="inline-flex items-center gap-1 rounded-xl border border-gray-200 bg-white px-3 py-1.5 text-xs font-semibold text-gray-700 shadow-theme-xs hover:border-gray-300 hover:bg-gray-50 dark:border-gray-800 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 transition-colors"
                        >
                          <span>View Thread</span>
                          <ArrowRightIcon />
                        </button>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>

      {/* 3. Table Pagination */}
      {totalItems !== undefined && onPageChange && (
        <TablePagination
          currentPage={currentPage ?? 1}
          totalPages={Math.max(1, Math.ceil((totalItems || 0) / (pageSize || 10)))}
          totalItems={totalItems}
          pageSize={pageSize || 10}
          onPageChange={onPageChange}
          onPageSizeChange={onPageSizeChange}
          pageSizeOptions={pageSizeOptions ?? [5, 10, 20, 50]}
          isLoading={isLoading}
        />
      )}
    </div>
  );
}
