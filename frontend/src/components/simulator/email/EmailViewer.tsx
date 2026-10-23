"use client";

import React, { useState } from "react";
import { SimulatedEmail } from "@/types/simulator";
import {
  EnvelopeIcon,
  PaperPlaneIcon,
  CalenderIcon,
  VideoIcon,
  BoltIcon,
} from "@/icons";

interface EmailViewerProps {
  email?: SimulatedEmail;
  onSendReply: (emailId: string, replyText: string) => void;
}

export default function EmailViewer({ email, onSendReply }: EmailViewerProps) {
  const [replyText, setReplyText] = useState("");
  const [isSending, setIsSending] = useState(false);

  if (!email) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center p-12 text-center text-gray-400">
        <EnvelopeIcon className="text-gray-300 dark:text-gray-600 mb-3" />
        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400">
          Select an email to view details
        </h4>
        <p className="mt-1 text-xs text-gray-400">
          Choose a message from the list on the left
        </p>
      </div>
    );
  }

  const handleQuickReply = (presetText: string) => {
    setReplyText(presetText);
  };

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!replyText.trim() || isSending) return;

    setIsSending(true);
    onSendReply(email.id, replyText.trim());
    setReplyText("");
    setTimeout(() => {
      setIsSending(false);
    }, 600);
  };

  return (
    <div className="flex flex-1 flex-col overflow-y-auto bg-white p-5 md:p-6 dark:bg-gray-900">
      {/* Email Subject Header */}
      <div className="border-b border-gray-100 pb-4 dark:border-gray-800">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-base font-semibold text-gray-900 dark:text-white">
            {email.subject}
          </h2>
          <span className="text-xs text-gray-400">{email.sent_at}</span>
        </div>

        {/* Sender & Recipient Metadata */}
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-500 font-bold text-white shadow-xs">
              AI
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-gray-900 dark:text-white">
                  {email.sender_name}
                </span>
                <span className="rounded bg-brand-50 px-2 py-0.5 text-[10px] font-semibold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
                  {email.sender_role}
                </span>
              </div>
              <p className="text-[11px] text-gray-500 dark:text-gray-400">
                From: &lt;{email.sender_email}&gt;
              </p>
            </div>
          </div>

          <div className="text-right text-[11px] text-gray-500 dark:text-gray-400">
            <span>To: {email.recipient_name} &lt;{email.recipient_email}&gt;</span>
          </div>
        </div>
      </div>

      {/* Meeting Card Banner (if applicable) */}
      {email.meeting_details && (
        <div className="mt-4 rounded-xl border border-brand-200 bg-brand-50/50 p-4 dark:border-brand-500/30 dark:bg-brand-500/5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-brand-800 dark:text-brand-200">
              <CalenderIcon className="text-brand-600" />
              <span>Synced Interview Session</span>
            </span>
            <span className="rounded-full bg-white px-2 py-0.5 font-mono text-[10px] text-gray-600 shadow-2xs dark:bg-gray-800 dark:text-gray-300">
              Ref: {email.meeting_details.calendar_ref}
            </span>
          </div>

          <div className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div className="rounded-lg bg-white p-2.5 dark:bg-gray-800/80">
              <span className="block text-[10px] uppercase tracking-wider text-gray-400">
                Date
              </span>
              <span className="font-medium text-gray-800 dark:text-white">
                {email.meeting_details.date_formatted}
              </span>
            </div>

            <div className="rounded-lg bg-white p-2.5 dark:bg-gray-800/80">
              <span className="block text-[10px] uppercase tracking-wider text-gray-400">
                Time (WIB / WITA)
              </span>
              <span className="font-medium text-gray-800 dark:text-white">
                {email.meeting_details.time_wib}
              </span>
              <span className="block text-[10px] text-gray-500">
                {email.meeting_details.time_wita}
              </span>
            </div>

            <div className="rounded-lg bg-white p-2.5 dark:bg-gray-800/80">
              <span className="block text-[10px] uppercase tracking-wider text-gray-400">
                Video Conference
              </span>
              <a
                href={email.meeting_details.meeting_link}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 font-medium text-brand-600 hover:underline dark:text-brand-400"
              >
                <VideoIcon/>
                <span>Join Meeting</span>
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Email Body Content */}
      <div className="mt-5 whitespace-pre-wrap text-xs md:text-sm leading-relaxed text-gray-800 dark:text-gray-200">
        {email.body_text}
      </div>

      <hr className="my-6 border-gray-100 dark:border-gray-800" />

      {/* Quick Reply & Reply Form */}
      <div className="mt-auto">
        <div className="mb-2 flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-xs font-semibold text-gray-700 dark:text-gray-300">
            <BoltIcon className="text-brand-500" />
            <span>Hiring Manager Quick Response Presets:</span>
          </span>
          <span className="text-[11px] text-gray-400">Click to fill reply text</span>
        </div>

        {/* 1-Click HM Presets */}
        <div className="mb-3 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() =>
              handleQuickReply(
                "Halo, saya menyetujui perubahan jadwal ke hari Kamis pukul 14:00 - 15:00 WIB. Sudah saya tandai di kalender saya."
              )
            }
            className="rounded-lg border border-success-200 bg-success-50 px-2.5 py-1 text-xs font-medium text-success-700 hover:bg-success-100 dark:border-success-500/30 dark:bg-success-500/10 dark:text-success-300"
          >
            Agree to Reschedule (Kamis 14:00 WIB)
          </button>

          <button
            type="button"
            onClick={() =>
              handleQuickReply(
                "Jadwal wawancara pada hari Rabu pukul 10:00 WIB sudah terkonfirmasi. Saya akan bergabung tepat waktu."
              )
            }
            className="rounded-lg border border-brand-200 bg-brand-50 px-2.5 py-1 text-xs font-medium text-brand-700 hover:bg-brand-100 dark:border-brand-500/30 dark:bg-brand-500/10 dark:text-brand-300"
          >
            Confirm Original Slot (Rabu 10:00 WIB)
          </button>

          <button
            type="button"
            onClick={() =>
              handleQuickReply(
                "Mohon maaf, pada waktu tersebut saya ada emergency deployment. Mohon koordinasikan ulang ke hari Jumat sore."
              )
            }
            className="rounded-lg border border-warning-200 bg-warning-50 px-2.5 py-1 text-xs font-medium text-warning-700 hover:bg-warning-100 dark:border-warning-500/30 dark:bg-warning-500/10 dark:text-warning-300"
          >
            Propose Alternate Friday Slot
          </button>
        </div>

        {/* Reply Composer */}
        <form onSubmit={handleSend} className="space-y-2">
          <textarea
            rows={3}
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            placeholder="Type official reply to SmartHiring AI Orchestrator..."
            className="w-full rounded-xl border border-gray-300 bg-gray-50 p-3 text-xs text-gray-800 placeholder-gray-400 focus:border-brand-500 focus:bg-white focus:outline-hidden focus:ring-1 focus:ring-brand-500 dark:border-gray-700 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
          />

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={!replyText.trim() || isSending}
              className="inline-flex items-center gap-1.5 rounded-xl bg-brand-500 px-4 py-2 text-xs font-semibold text-white shadow-xs transition-colors hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <PaperPlaneIcon/>
              <span>{isSending ? "Sending..." : "Send Reply"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
