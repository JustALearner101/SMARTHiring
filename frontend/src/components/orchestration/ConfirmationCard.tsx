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
  LockIcon,
  ShootingStarIcon,
} from "@/icons";
import { useAuth } from "@/context/AuthContext";
import { ActionItemDraft, ActionPlan } from "@/types/orchestration";
import React, { useMemo, useState } from "react";

interface ConfirmationCardProps {
  plan: ActionPlan;
  onApprove: (customizedPlan?: ActionPlan) => void;
  onReject: () => void;
  onEdit?: () => void;
  isApproving?: boolean;
}

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export default function ConfirmationCard({
  plan,
  onApprove,
  onReject,
  onEdit,
  isApproving = false,
}: ConfirmationCardProps) {
  const { role } = useAuth();
  const isHr = role === "HR";

  // Channel selections with Corporate Default (Email) for both parties
  const [candidateChannel, setCandidateChannel] = useState<"email" | "whatsapp">(() => {
    const candItem = plan.items.find(
      (i) => i.recipient_role.toLowerCase().includes("candidate") || i.channel === "whatsapp" || i.channel === "email"
    );
    return candItem?.channel === "whatsapp" ? "whatsapp" : "email";
  });

  const [interviewerChannel, setInterviewerChannel] = useState<"email" | "whatsapp">(() => {
    const interItem = plan.items.find(
      (i) => !i.recipient_role.toLowerCase().includes("candidate") && i.channel !== "calendar"
    );
    return interItem?.channel === "whatsapp" ? "whatsapp" : "email";
  });

  const [activeTab, setActiveTab] = useState<"candidate" | "interviewer" | "calendar">("candidate");
  const [isCopied, setIsCopied] = useState(false);

  const handleCopyLink = () => {
    navigator.clipboard.writeText(plan.proposed_slot.meeting_link);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  // Contact addresses
  const candEmail = plan.candidate_email || "belial110104@gmail.com";
  const candPhone = plan.candidate_phone || "+628345678907";
  const interEmail = plan.interviewer_email || "budi.santoso@company.com";
  const interPhone = plan.interviewer_phone || "+6281211112222";

  // Build reactive customized action items
  const customizedItems = useMemo<ActionItemDraft[]>(() => {
    const existingCand = plan.items.find(
      (i) => i.recipient_role.toLowerCase().includes("candidate") || i.channel === "whatsapp"
    );
    const existingInter = plan.items.find(
      (i) => !i.recipient_role.toLowerCase().includes("candidate") && i.channel !== "calendar"
    );
    const existingCal = plan.items.find((i) => i.channel === "calendar");

    // 1. Candidate Item
    const candidateItem: ActionItemDraft = {
      id: existingCand?.id || "item-candidate",
      action_type: candidateChannel === "email" ? "send_email" : "send_whatsapp",
      recipient_name: plan.candidate_name,
      recipient_role: "Candidate",
      recipient_contact: candidateChannel === "email" ? candEmail : candPhone,
      channel: candidateChannel,
      subject:
        candidateChannel === "email"
          ? existingCand?.subject || `[Invitation] Technical Interview: ${plan.candidate_name}`
          : undefined,
      content_preview:
        candidateChannel === "email"
          ? `Hello ${plan.candidate_name},\n\nYou are invited to attend the technical interview session (${plan.proposed_slot.title}) on:\n- Time: ${plan.proposed_slot.formatted_wib} (${plan.proposed_slot.formatted_wita})\n- Duration: ${plan.proposed_slot.duration_minutes} Minutes\n- Platform: ${plan.proposed_slot.location_type}\n- Link: ${plan.proposed_slot.meeting_link}\n\nPlease confirm your attendance by replying to this email.`
          : `Hello ${plan.candidate_name}, this is the Talent Acquisition team. We would like to invite you to a technical interview on ${plan.proposed_slot.formatted_wib} via ${plan.proposed_slot.location_type} (${plan.proposed_slot.meeting_link}). Please let us know if this time works for you.`,
      is_external: candidateChannel === "whatsapp" || candidateChannel === "email",
    };

    // 2. Interviewer Item
    const interviewerItem: ActionItemDraft = {
      id: existingInter?.id || "item-interviewer",
      action_type: interviewerChannel === "email" ? "send_email" : "send_whatsapp",
      recipient_name: plan.interviewer_name,
      recipient_role: plan.interviewer_role,
      recipient_contact: interviewerChannel === "email" ? interEmail : interPhone,
      channel: interviewerChannel,
      subject:
        interviewerChannel === "email"
          ? existingInter?.subject || `[Interview Schedule] ${plan.candidate_name} - ${plan.proposed_slot.title}`
          : undefined,
      content_preview:
        interviewerChannel === "email"
          ? `Hello ${plan.interviewer_name},\n\nA technical interview schedule with candidate ${plan.candidate_name} has been proposed:\n- Position: ${plan.candidate_position}\n- Time: ${plan.proposed_slot.formatted_wib}\n- Link: ${plan.proposed_slot.meeting_link}\n\nYour calendar has been reserved for this slot.`
          : `Hello ${plan.interviewer_name}, reminder: technical interview for candidate ${plan.candidate_name} is scheduled on ${plan.proposed_slot.formatted_wib} via ${plan.proposed_slot.location_type}. Link: ${plan.proposed_slot.meeting_link}`,
      is_external: false,
    };

    // 3. Calendar Item
    const calendarItem: ActionItemDraft = existingCal || {
      id: "item-calendar",
      action_type: "book_calendar",
      recipient_name: plan.interviewer_name,
      recipient_role: "Host",
      recipient_contact: plan.interviewer_name,
      channel: "calendar",
      subject: `Calendar: ${plan.proposed_slot.title}`,
      content_preview: `Reservasi slot kalender otomatis pada ${plan.proposed_slot.formatted_wib} (${plan.proposed_slot.duration_minutes} menit) di ${plan.proposed_slot.location_type}.`,
      is_external: false,
    };

    return [candidateItem, interviewerItem, calendarItem];
  }, [
    plan,
    candidateChannel,
    interviewerChannel,
    candEmail,
    candPhone,
    interEmail,
    interPhone,
  ]);

  const candidateDraft = customizedItems[0];
  const interviewerDraft = customizedItems[1];
  const calendarDraft = customizedItems[2];

  const handleApproveClick = () => {
    const updatedPlan: ActionPlan = {
      ...plan,
      is_high_impact: candidateChannel === "whatsapp" || plan.is_high_impact,
      items: customizedItems,
    };
    onApprove(updatedPlan);
  };

  return (
    <div className="rounded-2xl border-2 border-brand-500/30 bg-white p-5 xl:p-7 dark:border-brand-500/40 dark:bg-gray-900 shadow-theme-md transition-all">
      {/* Header Banner */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-gray-100 pb-4 dark:border-gray-800">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-500 text-white shadow-theme-xs">
            <BoltIcon className="text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-base font-bold text-gray-900 dark:text-white">
                Human-in-the-Loop Confirmation Card
              </h3>
              <span className="rounded-md bg-brand-50 px-2 py-0.5 text-[10px] font-mono font-bold text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
                APPROVAL Gate
              </span>
              <span className="inline-flex items-center gap-1.5 rounded-md bg-emerald-50 px-2 py-0.5 text-[10px] font-mono font-bold text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Live SMTP: Sumopod (SSL 465)
              </span>
            </div>
            <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
              AI has verified slot availability. Messages and calendar writes <strong>will not be executed</strong> until approved by HR.
            </p>
          </div>
        </div>

        {/* High-Impact Badge */}
        {(plan.is_high_impact || candidateChannel === "whatsapp") && (
          <div className="flex items-center gap-1.5 rounded-lg border border-warning-200 bg-warning-50 px-3 py-1.5 text-xs font-semibold text-warning-800 dark:border-warning-500/20 dark:bg-warning-500/15 dark:text-warning-300">
            <AlertIcon className="text-warning-600" />
            <span>High-Impact External Send</span>
          </div>
        )}
      </div>

      {/* Row 1: Meeting Agenda & Logistics (3 balanced columns) */}
      <div className="mt-5 grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-3">
        {/* WHAT: Agenda */}
        <div className="rounded-xl border border-gray-100 bg-gray-50/70 p-3.5 dark:border-gray-800 dark:bg-gray-800/40">
          <div className="flex items-center justify-between text-[10px] font-bold text-gray-400 uppercase tracking-wider">
            <span>WHAT · Session Agenda</span>
            <Badge color="primary" size="sm">Round {plan.negotiation_round} / {plan.max_rounds}</Badge>
          </div>
          <div className="mt-2 space-y-1">
            <div className="text-xs font-semibold text-gray-900 dark:text-white line-clamp-1">
              {plan.proposed_slot.title}
            </div>
            <div className="text-[11px] text-gray-500 dark:text-gray-400 flex items-center gap-2">
              <span>{plan.proposed_slot.duration_minutes} Menit</span>
              <span>&bull;</span>
              <span className="font-medium text-gray-700 dark:text-gray-300 truncate">{plan.candidate_position}</span>
            </div>
          </div>
        </div>

        {/* WHEN: Cross Timezone */}
        <div className="rounded-xl border border-gray-100 bg-gray-50/70 p-3.5 dark:border-gray-800 dark:bg-gray-800/40">
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block">
            WHEN · Cross Timezone
          </span>
          <div className="mt-2 space-y-0.5">
            <div className="text-xs font-semibold text-gray-900 dark:text-white">
              {plan.proposed_slot.formatted_wib}
            </div>
            <div className="text-[11px] font-mono text-gray-400">
              {plan.proposed_slot.formatted_wita}
            </div>
          </div>
        </div>

        {/* WHERE: Platform & Link */}
        <div className="rounded-xl border border-gray-100 bg-gray-50/70 p-3.5 dark:border-gray-800 dark:bg-gray-800/40">
          <div className="flex items-center justify-between text-[10px] font-bold text-gray-400 uppercase tracking-wider">
            <span>WHERE · Meeting Platform</span>
            <button
              type="button"
              onClick={handleCopyLink}
              className="inline-flex items-center gap-1 rounded-md bg-white px-2 py-0.5 text-[10px] font-medium text-gray-600 border border-gray-200 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 transition-colors"
              title="Salin Tautan Rapat"
            >
              <CopyIcon />
              <span>{isCopied ? "Tersalin!" : "Salin Link"}</span>
            </button>
          </div>
          <div className="mt-2">
            <div className="text-xs font-semibold text-gray-900 dark:text-white">
              {plan.proposed_slot.location_type}
            </div>
            <span className="text-[10px] font-mono text-gray-400 truncate block mt-0.5">
              {plan.proposed_slot.meeting_link}
            </span>
          </div>
        </div>
      </div>

      {/* Row 2: Notification Channels & Participant Routing (Spacious 2-column Executive Layout) */}
      <div className="mt-4 rounded-xl border border-brand-200/80 bg-brand-50/15 p-4 dark:border-brand-800/50 dark:bg-brand-900/10">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 pb-3 border-b border-brand-100 dark:border-brand-800/40">
          <div className="flex items-center gap-2">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-brand-500 text-[10px] font-bold text-white">
              2
            </span>
            <h4 className="text-xs font-bold text-gray-900 dark:text-white uppercase tracking-wider">
              Participant Channels &amp; Delivery Target
            </h4>
          </div>
          <div className="flex items-center gap-2 text-[10px] text-gray-500 dark:text-gray-400">
            <span className="rounded bg-brand-100 px-1.5 py-0.5 font-mono font-medium text-brand-700 dark:bg-brand-900/40 dark:text-brand-300">
              Standard: Email
            </span>
            <span>&bull;</span>
            <span className="font-mono text-gray-400">Pillar APPROVAL</span>
          </div>
        </div>

        <div className="mt-3.5 grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {/* Candidate Card */}
          <div className={`rounded-xl border p-4 transition-all ${
            candidateChannel === "email"
              ? "border-brand-200 bg-white shadow-xs dark:border-brand-800 dark:bg-gray-800/90"
              : "border-emerald-200 bg-white shadow-xs dark:border-emerald-800 dark:bg-gray-800/90"
          }`}>
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-3 min-w-0">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-indigo-600 text-sm font-bold text-white shadow-2xs">
                  {getInitials(plan.candidate_name)}
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-bold text-gray-900 dark:text-white truncate">
                      {plan.candidate_name}
                    </span>
                    <span className="rounded bg-gray-100 px-1.5 py-0.2 text-[9px] font-semibold text-gray-600 dark:bg-gray-700 dark:text-gray-300">
                      Candidate
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-500 dark:text-gray-400 truncate">
                    {plan.candidate_position}
                  </p>
                </div>
              </div>
            </div>

            {/* Segmented Pill Selector */}
            <div className="mt-3.5">
              <div className="flex rounded-lg bg-gray-100 p-1 dark:bg-gray-900">
                <button
                  type="button"
                  onClick={() => setCandidateChannel("email")}
                  className={`flex-1 flex items-center justify-center gap-1.5 rounded-md py-1.5 text-xs font-semibold transition-all ${
                    candidateChannel === "email"
                      ? "bg-white text-brand-700 shadow-xs dark:bg-gray-800 dark:text-brand-300"
                      : "text-gray-500 hover:text-gray-900 dark:hover:text-gray-200"
                  }`}
                  title="Default Standard (Email via Sumopod SMTP)"
                >
                  <EnvelopeIcon className="shrink-0" />
                  <span>Email (Default)</span>
                </button>
                <button
                  type="button"
                  onClick={() => setCandidateChannel("whatsapp")}
                  className={`flex-1 flex items-center justify-center gap-1.5 rounded-md py-1.5 text-xs font-semibold transition-all ${
                    candidateChannel === "whatsapp"
                      ? "bg-white text-emerald-700 shadow-xs dark:bg-gray-800 dark:text-emerald-300"
                      : "text-gray-500 hover:text-gray-900 dark:hover:text-gray-200"
                  }`}
                  title="WhatsApp Gateway (High-Impact External Send)"
                >
                  <ChatIcon className="shrink-0" />
                  <span>WhatsApp</span>
                </button>
              </div>

              {/* Destination Contact Handle Bar */}
              <div className="mt-2.5 flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 border border-gray-100 dark:bg-gray-900/60 dark:border-gray-800 text-xs">
                <div className="flex items-center gap-1.5 min-w-0">
                  <span className="text-gray-400 font-mono text-[11px]">Send to:</span>
                  <strong className="text-gray-900 dark:text-white font-mono truncate">
                    {candidateChannel === "email" ? candEmail : candPhone}
                  </strong>
                </div>
                <span className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-mono font-semibold ${
                  candidateChannel === "email"
                    ? "bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300"
                    : "bg-emerald-50 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300"
                }`}>
                  {candidateChannel === "email" ? "Sumopod SSL 465" : "WhatsApp Gateway"}
                </span>
              </div>
            </div>
          </div>

          {/* Interviewer Card */}
          <div className={`rounded-xl border p-4 transition-all ${
            interviewerChannel === "email"
              ? "border-brand-200 bg-white shadow-xs dark:border-brand-800 dark:bg-gray-800/90"
              : "border-emerald-200 bg-white shadow-xs dark:border-emerald-800 dark:bg-gray-800/90"
          }`}>
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-3 min-w-0">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 text-sm font-bold text-white shadow-2xs">
                  {getInitials(plan.interviewer_name)}
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-bold text-gray-900 dark:text-white truncate">
                      {plan.interviewer_name}
                    </span>
                    <span className="rounded bg-gray-100 px-1.5 py-0.2 text-[9px] font-semibold text-gray-600 dark:bg-gray-700 dark:text-gray-300">
                      User / HM
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-500 dark:text-gray-400 truncate">
                    {plan.interviewer_dept} &bull; {plan.interviewer_role}
                  </p>
                </div>
              </div>
            </div>

            {/* Segmented Pill Selector */}
            <div className="mt-3.5">
              <div className="flex rounded-lg bg-gray-100 p-1 dark:bg-gray-900">
                <button
                  type="button"
                  onClick={() => setInterviewerChannel("email")}
                  className={`flex-1 flex items-center justify-center gap-1.5 rounded-md py-1.5 text-xs font-semibold transition-all ${
                    interviewerChannel === "email"
                      ? "bg-white text-brand-700 shadow-xs dark:bg-gray-800 dark:text-brand-300"
                      : "text-gray-500 hover:text-gray-900 dark:hover:text-gray-200"
                  }`}
                  title="Default Standard (Email via Sumopod SMTP)"
                >
                  <EnvelopeIcon className="shrink-0" />
                  <span>Email (Default)</span>
                </button>
                <button
                  type="button"
                  onClick={() => setInterviewerChannel("whatsapp")}
                  className={`flex-1 flex items-center justify-center gap-1.5 rounded-md py-1.5 text-xs font-semibold transition-all ${
                    interviewerChannel === "whatsapp"
                      ? "bg-white text-emerald-700 shadow-xs dark:bg-gray-800 dark:text-emerald-300"
                      : "text-gray-500 hover:text-gray-900 dark:hover:text-gray-200"
                  }`}
                  title="WhatsApp Gateway"
                >
                  <ChatIcon className="shrink-0" />
                  <span>WhatsApp</span>
                </button>
              </div>

              {/* Destination Contact Handle Bar */}
              <div className="mt-2.5 flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 border border-gray-100 dark:bg-gray-900/60 dark:border-gray-800 text-xs">
                <div className="flex items-center gap-1.5 min-w-0">
                  <span className="text-gray-400 font-mono text-[11px]">Send to:</span>
                  <strong className="text-gray-900 dark:text-white font-mono truncate">
                    {interviewerChannel === "email" ? interEmail : interPhone}
                  </strong>
                </div>
                <span className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-mono font-semibold ${
                  interviewerChannel === "email"
                    ? "bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300"
                    : "bg-emerald-50 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300"
                }`}>
                  {interviewerChannel === "email" ? "Sumopod SSL 465" : "WhatsApp Gateway"}
                </span>
              </div>
            </div>
          </div>
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

      {/* Dynamic Message Draft Preview Tabs */}
      <div className="mt-5 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
        <div className="flex items-center border-b border-gray-200 bg-gray-50/80 dark:border-gray-800 dark:bg-gray-800/60 px-3 pt-2">
          {/* Candidate Tab */}
          <button
            type="button"
            onClick={() => setActiveTab("candidate")}
            className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-xs font-semibold transition-all ${
              activeTab === "candidate"
                ? "border-brand-500 text-brand-600 dark:text-brand-400"
                : "border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-300"
            }`}
          >
            {candidateChannel === "email" ? <EnvelopeIcon className="shrink-0" /> : <ChatIcon className="shrink-0" />}
            <span>Candidate ({candidateChannel === "email" ? "Email" : "WhatsApp"})</span>
            <span className={`rounded-full px-1.5 py-0.2 text-[9px] font-mono ${
              candidateChannel === "email"
                ? "bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300"
                : "bg-warning-100 text-warning-800 dark:bg-warning-900/30 dark:text-warning-300"
            }`}>
              {candidateChannel === "email" ? "Default" : "High-Impact"}
            </span>
          </button>

          {/* Interviewer Tab */}
          <button
            type="button"
            onClick={() => setActiveTab("interviewer")}
            className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-xs font-semibold transition-all ${
              activeTab === "interviewer"
                ? "border-brand-500 text-brand-600 dark:text-brand-400"
                : "border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-300"
            }`}
          >
            {interviewerChannel === "email" ? <EnvelopeIcon className="shrink-0" /> : <ChatIcon className="shrink-0"/>}
            <span>Interviewer ({interviewerChannel === "email" ? "Email" : "WhatsApp"})</span>
            <span className={`rounded-full px-1.5 py-0.2 text-[9px] font-mono ${
              interviewerChannel === "email"
                ? "bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300"
                : "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300"
            }`}>
              {interviewerChannel === "email" ? "Default" : "WhatsApp"}
            </span>
          </button>

          {/* Calendar Tab */}
          <button
            type="button"
            onClick={() => setActiveTab("calendar")}
            className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-xs font-semibold transition-all ${
              activeTab === "calendar"
                ? "border-brand-500 text-brand-600 dark:text-brand-400"
                : "border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-300"
            }`}
          >
            <CalenderIcon className="shrink-0" />
            <span>Calendar Booking</span>
          </button>
        </div>

        <div className="p-4 bg-white dark:bg-gray-900">
          {/* Candidate Preview */}
          {activeTab === "candidate" && (
            <div>
              <div className="flex flex-wrap items-center justify-between text-xs text-gray-500 mb-2 gap-2">
                <span>
                  Recipient: <strong>{candidateDraft.recipient_name}</strong> ({candidateDraft.recipient_contact})
                </span>
                <span className={`font-mono text-[10px] ${
                  candidateChannel === "email" ? "text-brand-600 dark:text-brand-400" : "text-emerald-600 dark:text-emerald-400"
                }`}>
                  Channel: {candidateChannel === "email" ? "Sumopod SMTP (smtp.sumopod.com:465 SSL)" : "WhatsApp Gateway"}
                </span>
              </div>
              {candidateDraft.subject && (
                <div className="mb-2 text-xs font-semibold text-gray-700 dark:text-gray-300">
                  Subject: {candidateDraft.subject}
                </div>
              )}
              <pre className="whitespace-pre-wrap rounded-lg bg-gray-50 p-3.5 text-xs text-gray-800 font-sans border border-gray-100 dark:border-gray-800 dark:bg-gray-800/40 dark:text-gray-200 leading-relaxed">
                {candidateDraft.content_preview}
              </pre>
            </div>
          )}

          {/* Interviewer Preview */}
          {activeTab === "interviewer" && (
            <div>
              <div className="flex flex-wrap items-center justify-between text-xs text-gray-500 mb-2 gap-2">
                <span>
                  Recipient: <strong>{interviewerDraft.recipient_name}</strong> ({interviewerDraft.recipient_contact})
                </span>
                <span className={`font-mono text-[10px] ${
                  interviewerChannel === "email" ? "text-brand-600 dark:text-brand-400" : "text-emerald-600 dark:text-emerald-400"
                }`}>
                  Channel: {interviewerChannel === "email" ? "Sumopod SMTP (smtp.sumopod.com:465 SSL)" : "WhatsApp Gateway"}
                </span>
              </div>
              {interviewerDraft.subject && (
                <div className="mb-2 text-xs font-semibold text-gray-700 dark:text-gray-300">
                  Subject: {interviewerDraft.subject}
                </div>
              )}
              <pre className="whitespace-pre-wrap rounded-lg bg-gray-50 p-3.5 text-xs text-gray-800 font-sans border border-gray-100 dark:border-gray-800 dark:bg-gray-800/40 dark:text-gray-200 leading-relaxed">
                {interviewerDraft.content_preview}
              </pre>
            </div>
          )}

          {/* Calendar Preview */}
          {activeTab === "calendar" && calendarDraft && (
            <div>
              <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
                <span>Target: <strong>Google Calendar &amp; PostgreSQL Calendar Event</strong></span>
                <span className="font-mono text-[10px] text-gray-400">Status: PENDING_WRITE</span>
              </div>
              <pre className="whitespace-pre-wrap rounded-lg bg-gray-50 p-3.5 text-xs text-gray-800 font-sans border border-gray-100 dark:border-gray-800 dark:bg-gray-800/40 dark:text-gray-200 leading-relaxed">
                {calendarDraft.content_preview}
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
            Click <strong>Approve &amp; Dispatch</strong> to approve. AI will provide <strong>60 seconds Undo Window</strong> before sending.
          </span>
        </div>

        <div className="flex items-center gap-2.5 justify-end">
          <Button variant="outline" size="md" onClick={onReject} disabled={!isHr || isApproving}>
            Reject Plan
          </Button>

          {onEdit && (
            <Button variant="secondary" size="md" onClick={onEdit} disabled={!isHr || isApproving}>
              Edit Draft
            </Button>
          )}

          <div className="flex items-center gap-2">
            {!isHr && (
              <span className="text-[11px] font-semibold text-warning-600 dark:text-warning-400">
                <LockIcon/>  
                HR Approval Only
              </span>
            )}
            <Button
              variant="primary"
              size="md"
              isLoading={isApproving}
              disabled={!isHr || isApproving}
              onClick={handleApproveClick}
              startIcon={<BoltIcon className="text-white" />}
            >
              {isHr ? "Approve (+60s Undo)" : "HR Approval Required"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
