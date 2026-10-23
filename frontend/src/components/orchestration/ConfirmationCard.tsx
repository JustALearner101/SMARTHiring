"use client";

import Badge from "@/components/ui/badge/Badge";
import Button from "@/components/ui/button/Button";
import {
  AlertIcon,
  BoltIcon,
  CalenderIcon,
  ChatIcon,
  CheckCircleIcon,
  CopyIcon,
  EnvelopeIcon,
  InfoIcon,
  ShootingStarIcon,
} from "@/icons";
import { ActionPlan } from "@/types/orchestration";
import React, { useState } from "react";

interface ConfirmationCardProps {
  plan: ActionPlan;
  onApprove: () => void;
  onReject: () => void;
  onEdit?: () => void;
  isApproving?: boolean;
}

export default function ConfirmationCard({
  plan,
  onApprove,
  onReject,
  onEdit,
  isApproving = false,
}: ConfirmationCardProps) {
  const [activeTab, setActiveTab] = useState<"email" | "whatsapp" | "calendar">("whatsapp");
  const [isCopied, setIsCopied] = useState(false);

  const handleCopyLink = () => {
    navigator.clipboard.writeText(plan.proposed_slot.meeting_link);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  const emailDraft = plan.items.find((i) => i.channel === "email");
  const waDraft = plan.items.find((i) => i.channel === "whatsapp");
  const calDraft = plan.items.find((i) => i.channel === "calendar");

  return (
    <div className="rounded-2xl border-2 border-brand-500/30 bg-white p-5 xl:p-7 dark:border-brand-500/40 dark:bg-gray-900 shadow-theme-md transition-all">
      {/* Header Banner */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-gray-100 pb-4 dark:border-gray-800">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-500 text-white shadow-theme-xs">
            <BoltIcon className="text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-gray-900 dark:text-white">
                Human-in-the-Loop Confirmation Card
              </h3>
              <span className="rounded-md bg-brand-50 px-2 py-0.5 text-[10px] font-mono font-bold text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
                APPROVAL Gate
              </span>
            </div>
            <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
              AI has verified the schedule&apos;s availability. Messages and calendar reservations <strong>will not be sent</strong> before approved by HR.
            </p>
          </div>
        </div>

        {/* High-Impact Badge */}
        {plan.is_high_impact && (
          <div className="flex items-center gap-1.5 rounded-lg border border-warning-200 bg-warning-50 px-3 py-1.5 text-xs font-semibold text-warning-800 dark:border-warning-500/20 dark:bg-warning-500/15 dark:text-warning-300">
            <AlertIcon className="text-warning-600" />
            <span>High-Impact External Send</span>
          </div>
        )}
      </div>

      {/* Structured Details: Who, What, When, Where */}
      <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {/* WHO */}
        <div className="rounded-xl border border-gray-100 bg-gray-50/70 p-3.5 dark:border-gray-800 dark:bg-gray-800/40">
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
            WHO (Related Parties)
          </span>
          <div className="mt-1.5 space-y-1">
            <div className="text-xs font-semibold text-gray-800 dark:text-white">
              Candidate: <span className="text-brand-600 dark:text-brand-400">{plan.candidate_name}</span>
            </div>
            <div className="text-[11px] text-gray-500 dark:text-gray-400">
              Interviewer: <span className="font-medium text-gray-700 dark:text-gray-300">{plan.interviewer_name}</span> ({plan.interviewer_role})
            </div>
          </div>
        </div>

        {/* WHAT */}
        <div className="rounded-xl border border-gray-100 bg-gray-50/70 p-3.5 dark:border-gray-800 dark:bg-gray-800/40">
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
            WHAT (Session Agenda)
          </span>
          <div className="mt-1.5 space-y-1">
            <div className="text-xs font-semibold text-gray-800 dark:text-white line-clamp-1">
              {plan.proposed_slot.title}
            </div>
            <div className="flex items-center gap-1.5 text-[11px] text-gray-500">
              <Badge color="primary" size="sm">Putaran {plan.negotiation_round} / {plan.max_rounds}</Badge>
              <span>{plan.proposed_slot.duration_minutes} Menit</span>
            </div>
          </div>
        </div>

        {/* WHEN */}
        <div className="rounded-xl border border-gray-100 bg-gray-50/70 p-3.5 dark:border-gray-800 dark:bg-gray-800/40">
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
            WHEN (Cross Timezone)
          </span>
          <div className="mt-1.5 space-y-0.5">
            <div className="text-xs font-semibold text-gray-800 dark:text-white">
              {plan.proposed_slot.formatted_wib}
            </div>
            <div className="text-[11px] font-mono text-gray-400">
              {plan.proposed_slot.formatted_wita}
            </div>
          </div>
        </div>

        {/* WHERE */}
        <div className="rounded-xl border border-gray-100 bg-gray-50/70 p-3.5 dark:border-gray-800 dark:bg-gray-800/40">
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
            WHERE (Meeting Platform)
          </span>
          <div className="mt-1.5 flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-800 dark:text-white">
              {plan.proposed_slot.location_type}
            </span>
            <button
              type="button"
              onClick={handleCopyLink}
              className="inline-flex items-center gap-1 rounded-md bg-white px-2 py-1 text-[10px] font-medium text-gray-600 border border-gray-200 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300"
              title="Salin Tautan Rapat"
            >
              <CopyIcon/>
              <span>{isCopied ? "Tersalin!" : "Salin"}</span>
            </button>
          </div>
          <span className="text-[10px] font-mono text-gray-400 truncate block mt-1">
            {plan.proposed_slot.meeting_link}
          </span>
        </div>
      </div>

      {/* Validation Badges: Secondary Validator & Guardrail */}
      <div className="mt-4 grid grid-cols-1 gap-2.5 sm:grid-cols-2">
        <div className="flex items-start gap-2.5 rounded-xl border border-success-200/80 bg-success-50/50 p-3 text-xs dark:border-success-500/20 dark:bg-success-500/10">
          <CheckCircleIcon className="text-success-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-success-900 dark:text-success-300">
              Secondary Validator Agent: Passed Verification
            </span>
            <p className="mt-0.5 text-[11px] text-success-700 dark:text-success-400 leading-relaxed">
              {plan.validator_notes}
            </p>
          </div>
        </div>

        <div className="flex items-start gap-2.5 rounded-xl border border-brand-200/80 bg-brand-50/50 p-3 text-xs dark:border-brand-500/20 dark:bg-brand-500/10">
          <ShootingStarIcon className="text-brand-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-brand-900 dark:text-brand-300">
              Prompt Injection Scanner: Clean
            </span>
            <p className="mt-0.5 text-[11px] text-brand-700 dark:text-brand-400 leading-relaxed">
              {plan.guardrail_notes}
            </p>
          </div>
        </div>
      </div>

      {/* Message Draft Preview Tabs */}
      <div className="mt-5 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
        <div className="flex items-center border-b border-gray-200 bg-gray-50/80 dark:border-gray-800 dark:bg-gray-800/60 px-3 pt-2">
          <button
            type="button"
            onClick={() => setActiveTab("whatsapp")}
            className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-xs font-semibold transition-all ${
              activeTab === "whatsapp"
                ? "border-brand-500 text-brand-600 dark:text-brand-400"
                : "border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-300"
            }`}
          >
            <ChatIcon />
            <span>Draft WhatsApp (Candidate)</span>
            <span className="rounded-full bg-success-100 px-1.5 py-0.2 text-[9px] text-success-700 font-mono">
              High-Impact
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("email")}
            className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-xs font-semibold transition-all ${
              activeTab === "email"
                ? "border-brand-500 text-brand-600 dark:text-brand-400"
                : "border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-300"
            }`}
          >
            <EnvelopeIcon />
            <span>Draft Email (Hiring Manager)</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("calendar")}
            className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-xs font-semibold transition-all ${
              activeTab === "calendar"
                ? "border-brand-500 text-brand-600 dark:text-brand-400"
                : "border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-300"
            }`}
          >
            <CalenderIcon />
            <span>Schedule Booking</span>
          </button>
        </div>

        <div className="p-4 bg-white dark:bg-gray-900">
          {activeTab === "whatsapp" && waDraft && (
            <div>
              <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
                <span>Receiver: <strong>{waDraft.recipient_name}</strong> ({waDraft.recipient_contact})</span>
                <span className="font-mono text-[10px] text-success-600">Channel: WhatsApp Gateway</span>
              </div>
              <pre className="whitespace-pre-wrap rounded-lg bg-gray-50 p-3.5 text-xs text-gray-800 font-sans border border-gray-100 dark:border-gray-800 dark:bg-gray-800/40 dark:text-gray-200 leading-relaxed">
                {waDraft.content_preview}
              </pre>
            </div>
          )}

          {activeTab === "email" && emailDraft && (
            <div>
              <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
                <span>Receiver: <strong>{emailDraft.recipient_name}</strong> &lt;{emailDraft.recipient_contact}&gt;</span>
                <span className="font-mono text-[10px] text-brand-600">Channel: Internal Email (SMTP/Resend)</span>
              </div>
              <div className="mb-2 text-xs font-semibold text-gray-700 dark:text-gray-300">
                Subject: {emailDraft.subject}
              </div>
              <pre className="whitespace-pre-wrap rounded-lg bg-gray-50 p-3.5 text-xs text-gray-800 font-sans border border-gray-100 dark:border-gray-800 dark:bg-gray-800/40 dark:text-gray-200 leading-relaxed">
                {emailDraft.content_preview}
              </pre>
            </div>
          )}

          {activeTab === "calendar" && calDraft && (
            <div>
              <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
                <span>Target: <strong>Google Calendar & Calendar Event</strong></span>
                <span className="font-mono text-[10px] text-gray-400">Status: PENDING_WRITE</span>
              </div>
              <pre className="whitespace-pre-wrap rounded-lg bg-gray-50 p-3.5 text-xs text-gray-800 font-sans border border-gray-100 dark:border-gray-800 dark:bg-gray-800/40 dark:text-gray-200 leading-relaxed">
                {calDraft.content_preview}
              </pre>
            </div>
          )}
        </div>
      </div>

      {/* Pillar SOURCES: Cited Sources Panel */}
      <div className="mt-5 rounded-xl border border-gray-200 bg-gray-50/60 p-4 dark:border-gray-800 dark:bg-gray-800/30">
        <div className="flex items-center justify-between mb-2.5">
          <div className="flex items-center gap-1.5">
            <InfoIcon className="text-brand-500" />
            <h4 className="text-xs font-bold text-gray-800 dark:text-white uppercase tracking-wider">
              Cited Sources by AI
            </h4>
          </div>
          <span className="text-[10px] text-gray-400">
            {plan.sources_cited.length} valid sources
          </span>
        </div>

        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {plan.sources_cited.map((src) => (
            <div
              key={src.id}
              className="rounded-lg border border-gray-200 bg-white p-2.5 dark:border-gray-700 dark:bg-gray-800 shadow-2xs"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-[10px] font-bold text-brand-600 dark:text-brand-400">
                  {src.ref_code}
                </span>
                <span className="rounded-md bg-gray-100 px-1 py-0.5 text-[9px] text-gray-500 dark:bg-gray-700 dark:text-gray-300">
                  {src.source_type}
                </span>
              </div>
              <div className="mt-1 text-xs font-semibold text-gray-800 dark:text-gray-200 line-clamp-1">
                {src.title}
              </div>
              <p className="mt-0.5 text-[10px] text-gray-500 dark:text-gray-400 leading-normal line-clamp-2">
                {src.detail}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Human Approval Action Bar */}
      <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between pt-4 border-t border-gray-100 dark:border-gray-800">
        <div className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400">
          <AlertIcon className="text-warning-500 shrink-0" />
          <span>
            Click <strong>Approve & Dispatch</strong> to approve. AI will provide <strong>60 seconds Undo Window</strong> before sending.
          </span>
        </div>

        <div className="flex items-center gap-2.5 justify-end">
          <Button variant="outline" size="md" onClick={onReject}>
            Reject Plan
          </Button>

          {onEdit && (
            <Button variant="secondary" size="md" onClick={onEdit}>
              Edit Draft
            </Button>
          )}

          <Button
            variant="primary"
            size="md"
            isLoading={isApproving}
            onClick={onApprove}
            startIcon={<BoltIcon className="text-white" />}
          >
            Approve & Dispatch (+60s Undo)
          </Button>
        </div>
      </div>
    </div>
  );
}
