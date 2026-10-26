"use client";

import React, { useEffect, useState } from "react";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import { NegotiationThread } from "@/types/orchestration";
import {
  getNegotiationThread,
  listNegotiationThreads,
  replyNegotiationThread,
} from "@/services/orchestrationService";
import ThreadStatsCards from "@/components/orchestration/threads/ThreadStatsCards";
import ThreadFilters from "@/components/orchestration/threads/ThreadFilters";
import ThreadTable from "@/components/orchestration/threads/ThreadTable";
import ThreadDetailModal from "@/components/orchestration/threads/ThreadDetailModal";

export default function TriageThreadsPage() {
  const [threads, setThreads] = useState<NegotiationThread[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [channelFilter, setChannelFilter] = useState("ALL");
  const [selectedThread, setSelectedThread] = useState<NegotiationThread | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Hydrate the thread list strictly from the backend API
  useEffect(() => {
    let isCancelled = false;

    const loadThreads = async () => {
      try {
        const page = await listNegotiationThreads({ page_size: 50 });
        if (isCancelled) return;
        setThreads(Array.isArray(page?.items) ? page.items : []);
      } catch (error) {
        console.error("Failed to fetch negotiation threads:", error);
      }
    };

    void loadThreads();

    return () => {
      isCancelled = true;
    };
  }, []);

  // Filter threads
  const filteredThreads = threads.filter((t) => {
    const matchesSearch =
      t.candidate_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.candidate_position.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.interviewer_name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "ALL" || t.status === statusFilter;
    const matchesChannel = channelFilter === "ALL" || t.candidate_channel === channelFilter;
    return matchesSearch && matchesStatus && matchesChannel;
  });

  const handleOpenThread = (thread: NegotiationThread) => {
    setSelectedThread(thread);
    setIsModalOpen(true);

    // Refresh message history from the backend
    void (async () => {
      try {
        const fresh = await getNegotiationThread(thread.id);
        const merged: NegotiationThread = {
          ...thread,
          ...fresh,
          messages: fresh.messages.length > 0 ? fresh.messages : thread.messages,
        };
        setThreads((prev) => prev.map((t) => (t.id === merged.id ? merged : t)));
        setSelectedThread((current) =>
          current && current.id === merged.id ? merged : current
        );
      } catch (error) {
        console.error("Failed to fetch thread detail:", error);
      }
    })();
  };

  const handleTakeoverSubmit = async (threadId: string, replyText: string) => {
    const target = threads.find((t) => t.id === threadId);
    if (!target) return;

    try {
      const message = await replyNegotiationThread(threadId, {
        content: replyText,
        sender_role: "HR_ADMIN",
        channel: target.candidate_channel,
      });

      const applyReply = (t: NegotiationThread): NegotiationThread => {
        if (t.id !== threadId) return t;
        return {
          ...t,
          status: "SCHEDULED",
          last_message_preview: `HR Takeover: "${replyText.slice(0, 60)}..."`,
          last_activity_at: message.sent_at || new Date().toISOString(),
          messages: [...t.messages, message],
        };
      };

      setThreads((prev) => prev.map(applyReply));
      setSelectedThread((current) => (current ? applyReply(current) : current));
    } catch (error) {
      console.error("Failed to send thread reply:", error);
    }
  };

  return (
    <div className="space-y-6">
      <PageBreadcrumb pageTitle="Triage Threads" />

      {/* Header Card */}
      <div className="rounded-2xl border border-gray-200 bg-white p-5 xl:p-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-gray-100 pb-4 dark:border-gray-800">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-theme-xl font-bold text-gray-900 dark:text-white">
                Active Triage & Negotiation Threads
              </h3>
              <span className="rounded bg-warning-50 px-2 py-0.5 font-mono text-[10px] font-bold text-warning-700 dark:bg-warning-500/15 dark:text-warning-300">
                Pilar LIMITS
              </span>
            </div>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Pemantauan alur negosiasi jadwal asinkron otomatis antara AI, Kandidat (WhatsApp/Email), dan Interviewer dengan batas maksimal 3 putaran.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center rounded-full bg-warning-50 px-3 py-1 text-xs font-semibold text-warning-700 dark:bg-warning-500/15 dark:text-warning-400">
              Max 3x Loop Enforced
            </span>
          </div>
        </div>

        {/* 4 Summary Metric Cards */}
        <div className="mt-6">
          <ThreadStatsCards threads={threads} />
        </div>
      </div>

      {/* Threads Table & Filters */}
      <div className="space-y-4">
        <ThreadFilters
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          statusFilter={statusFilter}
          onStatusChange={setStatusFilter}
          channelFilter={channelFilter}
          onChannelChange={setChannelFilter}
        />

        <ThreadTable
          threads={filteredThreads}
          onSelectThread={handleOpenThread}
        />
      </div>

      {/* Detail & Takeover Modal */}
      <ThreadDetailModal
        key={selectedThread?.id ?? "no-thread"}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        thread={selectedThread}
        onTakeoverSubmit={handleTakeoverSubmit}
      />
    </div>
  );
}
