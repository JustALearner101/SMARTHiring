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
import { AlertIcon, CheckCircleIcon, TimeIcon, ArrowRightIcon } from "@/icons";

interface ThreadTableProps {
  threads: NegotiationThread[];
  onSelectThread: (thread: NegotiationThread) => void;
}

export default function ThreadTable({
  threads,
  onSelectThread,
}: ThreadTableProps) {
  const getStatusBadge = (status: NegotiationThread["status"]) => {
    switch (status) {
      case "NEGOTIATING":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-semibold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
            <span className="h-1.5 w-1.5 rounded-full bg-brand-500 animate-pulse" />
            In Negotiation
          </span>
        );
      case "SCHEDULED":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-success-50 px-2.5 py-0.5 text-xs font-semibold text-success-700 dark:bg-success-500/15 dark:text-success-400">
            <CheckCircleIcon />
            Scheduled
          </span>
        );
      case "DEADLOCK_ESCALATED":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-error-50 px-2.5 py-0.5 text-xs font-bold text-error-700 dark:bg-error-500/15 dark:text-error-400 animate-bounce">
            <AlertIcon />
            Deadlock Escalated
          </span>
        );
      case "EXPIRED":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-600 dark:bg-gray-800 dark:text-gray-400">
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
      <div className="overflow-x-auto">
        <Table>
          <TableHeader className="border-b border-gray-100 dark:border-gray-800">
            <TableRow>
              <TableCell isHeader className="py-3 px-4 text-start text-xs font-semibold text-gray-500 dark:text-gray-400">
                Candidate
              </TableCell>
              <TableCell isHeader className="py-3 px-4 text-start text-xs font-semibold text-gray-500 dark:text-gray-400">
                Interviewer
              </TableCell>
              <TableCell isHeader className="py-3 px-4 text-start text-xs font-semibold text-gray-500 dark:text-gray-400">
                Negotiation Round (LIMITS)
              </TableCell>
              <TableCell isHeader className="py-3 px-4 text-start text-xs font-semibold text-gray-500 dark:text-gray-400">
                Status
              </TableCell>
              <TableCell isHeader className="py-3 px-4 text-start text-xs font-semibold text-gray-500 dark:text-gray-400">
                Last Activity
              </TableCell>
              <TableCell isHeader className="py-3 px-4 text-end text-xs font-semibold text-gray-500 dark:text-gray-400">
                Action
              </TableCell>
            </TableRow>
          </TableHeader>
          <TableBody className="divide-y divide-gray-100 dark:divide-gray-800">
            {threads.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="py-8 text-center text-xs text-gray-500">
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
                    <TableCell className="py-3.5 px-4">
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
                    <TableCell className="py-3.5 px-4">
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
                    <TableCell className="py-3.5 px-4">
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
                    <TableCell className="py-3.5 px-4">
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
                    <TableCell className="py-3.5 px-4 text-end">
                      {isDeadlock ? (
                        <button
                          onClick={() => onSelectThread(thread)}
                          className="inline-flex items-center gap-1 rounded-xl bg-error-600 px-3 py-1.5 text-xs font-bold text-white shadow-theme-xs hover:bg-error-700 transition-colors"
                        >
                          <AlertIcon />
                          <span>Intervene Now</span>
                        </button>
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
    </div>
  );
}
