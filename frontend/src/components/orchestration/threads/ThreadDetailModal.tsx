"use client";

import React, { useState } from "react";
import { NegotiationThread } from "@/types/orchestration";
import { Modal } from "@/components/ui/modal";
import Button from "@/components/ui/button/Button";
import { AlertIcon, CheckCircleIcon, CloseIcon, LockIcon } from "@/icons";

interface ThreadDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  thread: NegotiationThread | null;
  onTakeoverSubmit: (threadId: string, replyText: string) => void;
}

export default function ThreadDetailModal({
  isOpen,
  onClose,
  thread,
  onTakeoverSubmit,
}: ThreadDetailModalProps) {
  const [manualReply, setManualReply] = useState("");
  const [isSent, setIsSent] = useState(false);

  if (!thread) return null;

  const isDeadlock = thread.status === "DEADLOCK_ESCALATED";

  const handleSendTakeover = (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualReply.trim()) return;
    onTakeoverSubmit(thread.id, manualReply);
    setIsSent(true);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} className="max-w-3xl p-6">
      {/* Header */}
      <div className="flex items-start justify-between border-b border-gray-100 pb-4 dark:border-gray-800">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-gray-900 dark:text-white">
              Triage Thread: {thread.candidate_name}
            </h3>
            <span className="rounded bg-brand-50 px-2 py-0.5 text-[10px] font-bold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
              {thread.candidate_channel.toUpperCase()}
            </span>
          </div>
          <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
            {thread.candidate_position} • Interviewer: {thread.interviewer_name} ({thread.interviewer_role})
          </p>
        </div>

        <div className="flex items-center gap-2 pe-8">
          <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-1 text-xs font-semibold text-gray-700 dark:bg-gray-800 dark:text-gray-300">
            Round {thread.current_round} / {thread.max_rounds} (LIMITS)
          </span>
        </div>
      </div>

      {/* Escalation Alert Box */}
      {isDeadlock && (
        <div className="mt-4 rounded-xl border border-error-200 bg-error-50 p-4 dark:border-error-800/60 dark:bg-error-500/10">
          <div className="flex items-start gap-3">
            <div className="text-error-600 dark:text-error-400 mt-0.5">
              <AlertIcon />
            </div>
            <div>
              <h4 className="text-xs font-bold text-error-800 dark:text-error-300">
                Pilar LIMITS: Deadlock Reached — AI Autonomous Loop Halted
              </h4>
              <p className="mt-1 text-xs text-error-700 dark:text-error-400 leading-relaxed">
                {thread.escalation_reason ||
                  "Kandidat telah menolak 3 kali slot yang diajukan AI secara berturut-turut. Sesuai aturan akuntabilitas, sistem menghentikan negosiasi otomatis dan meminta intervensi manusia (HR Takeover)."}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Message Timeline */}
      <div className="mt-4 max-h-[380px] overflow-y-auto space-y-3.5 pe-1">
        {thread.messages.map((msg, index) => {
          const isAI = msg.sender_role === "AI_ORCHESTRATOR";
          const isCandidate = msg.sender_role === "CANDIDATE";

          return (
            <div key={msg.id} className="space-y-1">
              {/* Round Divider */}
              {(index === 0 || thread.messages[index - 1].round_number !== msg.round_number) && (
                <div className="flex items-center gap-2 py-1">
                  <div className="h-px flex-1 bg-gray-200 dark:bg-gray-800" />
                  <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-bold text-gray-600 dark:bg-gray-800 dark:text-gray-400">
                    NEGOTIATION ROUND {msg.round_number}
                  </span>
                  <div className="h-px flex-1 bg-gray-200 dark:bg-gray-800" />
                </div>
              )}

              {/* Message Bubble */}
              <div className={`flex flex-col ${isCandidate ? "items-end" : "items-start"}`}>
                <div className="flex items-center gap-1.5 px-1 text-[10px] text-gray-400">
                  <span className="font-semibold text-gray-600 dark:text-gray-300">
                    {msg.sender_name}
                  </span>
                  <span>•</span>
                  <span>
                    {new Date(msg.sent_at).toLocaleTimeString("id-ID", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>

                <div
                  className={`mt-1 max-w-[85%] rounded-2xl p-3.5 text-xs leading-relaxed ${
                    isCandidate
                      ? "rounded-tr-none bg-brand-500 text-white shadow-theme-xs"
                      : "rounded-tl-none border border-gray-200 bg-gray-50 text-gray-800 dark:border-gray-800 dark:bg-gray-800 dark:text-gray-200 shadow-theme-xs"
                  }`}
                >
                  <p>{msg.content}</p>

                  {/* Proposed Slot & Source Citation */}
                  {msg.proposed_slot && (
                    <div className="mt-2.5 rounded-xl border border-brand-200 bg-brand-50/80 p-2 text-[11px] text-brand-900 dark:border-brand-800 dark:bg-brand-950/40 dark:text-brand-200">
                      <span className="font-semibold block">Proposed Slot:</span>
                      <span>{msg.proposed_slot}</span>
                      {msg.source_citation && (
                        <span className="mt-1 inline-block rounded bg-brand-200/60 px-1.5 py-0.2 font-mono text-[10px] font-bold text-brand-800 dark:bg-brand-800/60 dark:text-brand-300">
                          {msg.source_citation}
                        </span>
                      )}
                    </div>
                  )}

                  {msg.is_rejection && (
                    <span className="mt-2 inline-flex items-center gap-1 rounded bg-error-100 px-1.5 py-0.5 text-[10px] font-bold text-error-800 dark:bg-error-900/60 dark:text-error-300">
                      <AlertIcon />
                      Declined / Reschedule Requested
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Human Takeover Section */}
      {isDeadlock && !isSent && (
        <form onSubmit={handleSendTakeover} className="mt-4 border-t border-gray-100 pt-4 dark:border-gray-800">
          <label className="block text-xs font-bold text-gray-800 dark:text-white mb-1.5 flex items-center gap-1.5">
            <LockIcon />
            <span>Human-in-the-Loop Override (Kirim Pesan Manual ke Kandidat):</span>
          </label>
          <textarea
            rows={2}
            value={manualReply}
            onChange={(e) => setManualReply(e.target.value)}
            placeholder="Tulis pesan penyelesaian dari HR (misal: memberikan slot khusus atau nomor kontak langsung)..."
            className="w-full rounded-xl border border-gray-300 bg-white p-3 text-xs text-gray-800 placeholder-gray-400 focus:border-brand-500 focus:outline-hidden dark:border-gray-700 dark:bg-gray-800 dark:text-white"
          />
          <div className="mt-3 flex items-center justify-end gap-2">
            <Button size="sm" variant="outline" onClick={onClose}>
              Batal
            </Button>
            <Button size="sm" type="submit" disabled={!manualReply.trim()}>
              Send HR Resolution via {thread.candidate_channel.toUpperCase()}
            </Button>
          </div>
        </form>
      )}

      {isSent && (
        <div className="mt-4 rounded-xl bg-success-50 p-3 text-center text-xs font-semibold text-success-800 dark:bg-success-500/10 dark:text-success-300">
          ✓ Pesan intervensi HR berhasil dikirim! Status thread telah diselesaikan secara manual.
        </div>
      )}

      {!isDeadlock && (
        <div className="mt-4 flex justify-end border-t border-gray-100 pt-4 dark:border-gray-800">
          <Button size="sm" variant="outline" onClick={onClose}>
            Tutup
          </Button>
        </div>
      )}
    </Modal>
  );
}
