"use client";

import Badge from "@/components/ui/badge/Badge";
import Button from "@/components/ui/button/Button";
import { Modal } from "@/components/ui/modal";
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
import { ActionItemDraft, ActionPlan, ProposedSlot } from "@/types/orchestration";
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
  onEdit: _onEdit,
  isApproving = false,
}: ConfirmationCardProps) {
  const { role } = useAuth();
  const isHr = role === "HR";

  // Derive initial channel from plan.items
  const initialCandItem = plan.items.find(
    (i) => i.recipient_role.toLowerCase().includes("candidate") || i.channel === "whatsapp"
  );
  const initialInterItem = plan.items.find(
    (i) => !i.recipient_role.toLowerCase().includes("candidate") && i.channel !== "calendar"
  );

  const [candidateChannel, setCandidateChannel] = useState<"email" | "whatsapp">(
    initialCandItem?.channel === "whatsapp" ? "whatsapp" : "email"
  );
  const [interviewerChannel, setInterviewerChannel] = useState<"email" | "whatsapp">(
    initialInterItem?.channel === "whatsapp" ? "whatsapp" : "email"
  );

  const [activeTabId, setActiveTabId] = useState<string>(() => plan.items[0]?.id || "item-01");
  const [isCopied, setIsCopied] = useState(false);

  // Modals for Bonus Pillars
  const [isEditSlotModalOpen, setIsEditSlotModalOpen] = useState(false);
  const [isHighImpactModalOpen, setIsHighImpactModalOpen] = useState(false);
  const [editDate, setEditDate] = useState(() => {
    try {
      return new Date(plan.proposed_slot.start_utc).toISOString().split("T")[0];
    } catch {
      return "2026-11-06";
    }
  });
  const [editTime, setEditTime] = useState("14:00");
  const [validationError, setValidationError] = useState<string | null>(null);

  // Active slot (supports local slot edits)
  const [currentSlot, setCurrentSlot] = useState<ProposedSlot>(plan.proposed_slot);

  const handleCopyLink = () => {
    navigator.clipboard.writeText(currentSlot.meeting_link);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  // Contact addresses
  const candEmail = plan.candidate_email || "candidate@example.com";
  const candPhone = plan.candidate_phone || "+6281234567890";
  const interEmail = plan.interviewer_email || "budi.santoso@company.com";
  const interPhone = plan.interviewer_phone || "+6281198765432";

  // Build reactive customized action items from backend plan.items
  const customizedItems = useMemo<ActionItemDraft[]>(() => {
    return plan.items.map((it) => {
      const isCand = it.recipient_role.toLowerCase().includes("candidate");
      const isInter =
        !isCand &&
        it.channel !== "calendar" &&
        (it.recipient_role.toLowerCase().includes("interviewer") ||
          it.recipient_role.toLowerCase().includes("host") ||
          it.recipient_name === plan.interviewer_name);

      if (isCand) {
        return {
          ...it,
          channel: candidateChannel,
          action_type: candidateChannel === "email" ? "send_email" : "send_whatsapp",
          recipient_contact: candidateChannel === "email" ? candEmail : candPhone,
          is_external: true,
          content_preview:
            candidateChannel === "email"
              ? it.content_preview
              : `Halo ${plan.candidate_name}, berikut informasi jadwal wawancara teknis pada ${currentSlot.formatted_wib} via ${currentSlot.location_type} (${currentSlot.meeting_link}). Mohon konfirmasi kesediaan Anda.`,
        };
      }

      if (isInter) {
        return {
          ...it,
          channel: interviewerChannel,
          action_type: interviewerChannel === "email" ? "send_email" : "send_whatsapp",
          recipient_contact: interviewerChannel === "email" ? interEmail : interPhone,
          content_preview:
            interviewerChannel === "email"
              ? it.content_preview
              : `Halo ${plan.interviewer_name}, reminder: jadwal pertemuan pada ${currentSlot.formatted_wib} di ${currentSlot.location_type}. Link: ${currentSlot.meeting_link}`,
        };
      }

      return it;
    });
  }, [
    plan.items,
    candidateChannel,
    interviewerChannel,
    candEmail,
    candPhone,
    interEmail,
    interPhone,
    plan.candidate_name,
    plan.interviewer_name,
    currentSlot,
  ]);

  const activeItem =
    customizedItems.find((i) => i.id === activeTabId) || customizedItems[0];

  const externalRecipients = useMemo(() => {
    return customizedItems.filter((i) => i.is_external);
  }, [customizedItems]);

  const isHighImpactAction =
    plan.is_high_impact ||
    candidateChannel === "whatsapp" ||
    externalRecipients.length > 0;

  // Handle Approve Click
  const handleApproveClick = () => {
    if (validationError) return;

    const updatedPlan: ActionPlan = {
      ...plan,
      proposed_slot: currentSlot,
      is_high_impact: isHighImpactAction,
      items: customizedItems,
    };

    // TC-CHB-22: Require extra confirmation modal for high-impact external sends
    if (isHighImpactAction) {
      setIsHighImpactModalOpen(true);
      return;
    }

    onApprove(updatedPlan);
  };

  const handleConfirmHighImpact = () => {
    setIsHighImpactModalOpen(false);
    const updatedPlan: ActionPlan = {
      ...plan,
      proposed_slot: currentSlot,
      is_high_impact: true,
      items: customizedItems,
    };
    onApprove(updatedPlan);
  };

  // TC-CHB-21: Secondary validator checks when user edits slot
  const handleSaveEditedSlot = () => {
    const dayOfWeek = new Date(editDate).getDay(); // 5 is Friday
    const [hh, mm] = editTime.split(":").map(Number);
    const timeVal = (hh || 0) * 60 + (mm || 0);

    // Friday prayer window: 11:30 (690m) to 13:00 (780m)
    if (dayOfWeek === 5 && timeVal >= 690 && timeVal < 780) {
      setValidationError(
        "Secondary Validator Alert (Rule Violation Blocked): Slot Friday 12:00 WIB overlaps with Friday prayer blackout [rule-jumatan] (11:30 - 13:00 WIB). Action execution blocked until a compliant slot is chosen."
      );
      setIsEditSlotModalOpen(false);
      return;
    }

    // Working hours: 09:00 (540m) to 17:00 (1020m)
    if (timeVal < 540 || timeVal > 960) {
      setValidationError(
        "Secondary Validator Alert (Rule Violation Blocked): Slot is outside official operational working hours (09:00 - 17:00 WIB) [rule-working-hours]. Action execution blocked."
      );
      setIsEditSlotModalOpen(false);
      return;
    }

    setValidationError(null);
    const dateObj = new Date(`${editDate}T${editTime}:00`);
    const dateStr = dateObj.toLocaleDateString("id-ID", {
      weekday: "long",
      day: "2-digit",
      month: "short",
      year: "numeric",
    });

    setCurrentSlot((prev) => ({
      ...prev,
      formatted_wib: `${dateStr}, ${editTime} WIB`,
      formatted_wita: `${dateStr}, ${String(hh + 1).padStart(2, "0")}:${String(mm).padStart(2, "0")} WITA`,
      formatted_wit: `${dateStr}, ${String(hh + 2).padStart(2, "0")}:${String(mm).padStart(2, "0")} WIT`,
    }));
    setIsEditSlotModalOpen(false);
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
                Live SMTP &amp; WhatsApp Gateways
              </span>
            </div>
            <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
              AI has verified slot availability. Messages and calendar writes <strong>will not be executed</strong> until approved by HR.
            </p>
          </div>
        </div>

        {/* High-Impact Badge */}
        {isHighImpactAction && (
          <div className="flex items-center gap-1.5 rounded-lg border border-warning-200 bg-warning-50 px-3 py-1.5 text-xs font-semibold text-warning-800 dark:border-warning-500/20 dark:bg-warning-500/15 dark:text-warning-300">
            <AlertIcon className="text-warning-600" />
            <span>High-Impact External Send</span>
          </div>
        )}
      </div>

      {/* Secondary Validator Error Alert Banner (e.g. TC-CHB-21) */}
      {validationError && (
        <div className="mt-4 rounded-xl border border-error-300 bg-error-50 p-3.5 dark:border-error-800/80 dark:bg-error-500/15">
          <div className="flex items-start gap-2.5">
            <AlertIcon className="text-error-600 dark:text-error-400 shrink-0 mt-0.5" />
            <div>
              <span className="text-xs font-bold text-error-900 dark:text-error-200 block">
                Secondary Validator Blocked Execution (Rule Violation)
              </span>
              <p className="mt-0.5 text-xs text-error-800 dark:text-error-300 leading-relaxed">
                {validationError}
              </p>
              <div className="mt-2 flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setEditTime("14:00");
                    handleSaveEditedSlot();
                  }}
                >
                  Auto-Shift to Safe Slot (14:00 WIB)
                </Button>
                <Button size="sm" variant="secondary" onClick={() => setIsEditSlotModalOpen(true)}>
                  Edit Slot Again
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

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
              {currentSlot.title}
            </div>
            <div className="text-[11px] text-gray-500 dark:text-gray-400 flex items-center gap-2">
              <span>{currentSlot.duration_minutes} Menit</span>
              <span>&bull;</span>
              <span className="font-medium text-gray-700 dark:text-gray-300 truncate">{plan.candidate_position}</span>
            </div>
          </div>
        </div>

        {/* WHEN: Cross Timezone */}
        <div className="rounded-xl border border-gray-100 bg-gray-50/70 p-3.5 dark:border-gray-800 dark:bg-gray-800/40">
          <div className="flex items-center justify-between text-[10px] font-bold text-gray-400 uppercase tracking-wider">
            <span>WHEN · Cross Timezone</span>
            <button
              type="button"
              onClick={() => setIsEditSlotModalOpen(true)}
              className="text-[10px] font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400 underline"
            >
              Edit Slot
            </button>
          </div>
          <div className="mt-2 space-y-0.5">
            <div className="text-xs font-semibold text-gray-900 dark:text-white">
              {currentSlot.formatted_wib}
            </div>
            <div className="text-[11px] font-mono text-gray-400">
              {currentSlot.formatted_wita}
            </div>
            {currentSlot.formatted_wit && (
              <div className="text-[11px] font-mono text-brand-600 dark:text-brand-400">
                {currentSlot.formatted_wit}
              </div>
            )}
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
              {currentSlot.location_type}
            </div>
            <span className="text-[10px] font-mono text-gray-400 truncate block mt-0.5">
              {currentSlot.meeting_link}
            </span>
          </div>
        </div>
      </div>

      {/* Row 2: Participant Channels & Delivery Target (Spacious 2-column Executive Layout) */}
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
              {customizedItems.length} Discrete Action Items
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

            {/* Segmented Pill Selector with Active WhatsApp (TC-CHB-12) */}
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
                  title="Official Email via Sumopod SMTP"
                >
                  <EnvelopeIcon className="shrink-0" />
                  <span>Email</span>
                </button>
                <button
                  type="button"
                  onClick={() => setCandidateChannel("whatsapp")}
                  className={`flex-1 flex items-center justify-center gap-1.5 rounded-md py-1.5 text-xs font-semibold transition-all ${
                    candidateChannel === "whatsapp"
                      ? "bg-white text-emerald-700 shadow-xs dark:bg-gray-800 dark:text-emerald-300"
                      : "text-gray-500 hover:text-gray-900 dark:hover:text-gray-200"
                  }`}
                  title="Candidate WhatsApp Gateway"
                >
                  <ChatIcon className="shrink-0 text-emerald-600 dark:text-emerald-400" />
                  <span>WhatsApp</span>
                  <span className="rounded bg-emerald-100 px-1 py-0.2 text-[9px] font-mono font-bold text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">
                    Live
                  </span>
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

            {/* Segmented Pill Selector with Active WhatsApp */}
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
                  title="Official Email via Sumopod SMTP"
                >
                  <EnvelopeIcon className="shrink-0" />
                  <span>Email</span>
                </button>
                <button
                  type="button"
                  onClick={() => setInterviewerChannel("whatsapp")}
                  className={`flex-1 flex items-center justify-center gap-1.5 rounded-md py-1.5 text-xs font-semibold transition-all ${
                    interviewerChannel === "whatsapp"
                      ? "bg-white text-emerald-700 shadow-xs dark:bg-gray-800 dark:text-emerald-300"
                      : "text-gray-500 hover:text-gray-900 dark:hover:text-gray-200"
                  }`}
                  title="Interviewer WhatsApp Notification"
                >
                  <ChatIcon className="shrink-0 text-emerald-600 dark:text-emerald-400" />
                  <span>WhatsApp</span>
                  <span className="rounded bg-emerald-100 px-1 py-0.2 text-[9px] font-mono font-bold text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">
                    Live
                  </span>
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

      {/* Validation Badges: Secondary Validator & Guardrail (TC-CHB-02 conditional) */}
      <div className="mt-4 grid grid-cols-1 gap-2.5 sm:grid-cols-2">
        <div className="flex items-start gap-2.5 rounded-xl border border-success-200/80 bg-success-50/50 p-3 text-xs dark:border-success-500/20 dark:bg-success-500/10">
          <CheckCircleIcon className="text-success-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-success-900 dark:text-success-300">
              Secondary Validator Agent: Verified
            </span>
            <p className="mt-0.5 text-[11px] text-success-700 dark:text-success-400 leading-relaxed">
              {validationError || plan.validator_notes}
            </p>
          </div>
        </div>

        {/* Prompt Injection Scanner (Alerts prominently when an injection is detected and disregarded) */}
        <div
          className={`flex items-start gap-2.5 rounded-xl border p-3 text-xs ${
            plan.guardrail_passed
              ? "border-brand-200/80 bg-brand-50/50 dark:border-brand-500/20 dark:bg-brand-500/10"
              : "border-error-300 bg-error-50 dark:border-error-500/40 dark:bg-error-500/15"
          }`}
        >
          {plan.guardrail_passed ? (
            <ShootingStarIcon className="text-brand-600 shrink-0 mt-0.5" />
          ) : (
            <AlertIcon className="text-error-600 dark:text-error-400 shrink-0 mt-0.5" />
          )}
          <div>
            <span
              className={`font-semibold ${
                plan.guardrail_passed
                  ? "text-brand-900 dark:text-brand-300"
                  : "text-error-900 dark:text-error-200 font-bold"
              }`}
            >
              {plan.guardrail_passed
                ? "Prompt Injection Scanner: Clean"
                : "Prompt Injection Scanner: Embedded Instruction Detected & Disregarded"}
            </span>
            <p
              className={`mt-0.5 text-[11px] leading-relaxed ${
                plan.guardrail_passed
                  ? "text-brand-700 dark:text-brand-400"
                  : "text-error-800 dark:text-error-300 font-medium"
              }`}
            >
              {plan.guardrail_notes}
            </p>
          </div>
        </div>
      </div>

      {/* Dynamic Action Items Preview Tabs (Renders ALL discrete action items) */}
      <div className="mt-5 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
        <div className="flex items-center overflow-x-auto border-b border-gray-200 bg-gray-50/80 dark:border-gray-800 dark:bg-gray-800/60 px-3 pt-2">
          {customizedItems.map((item, idx) => {
            const isSelected = activeTabId === item.id;
            const isEmail = item.channel === "email";
            const isWa = item.channel === "whatsapp";
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setActiveTabId(item.id)}
                className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-xs font-semibold whitespace-nowrap transition-all ${
                  isSelected
                    ? "border-brand-500 text-brand-600 dark:text-brand-400 bg-white/70 dark:bg-gray-900/60 rounded-t-lg"
                    : "border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-300"
                }`}
              >
                {isEmail ? (
                  <EnvelopeIcon className="shrink-0" />
                ) : isWa ? (
                  <ChatIcon className="shrink-0" />
                ) : (
                  <CalenderIcon className="shrink-0" />
                )}
                <span>
                  {item.action_type === "book_calendar"
                    ? "Calendar Booking"
                    : item.recipient_name || `Action ${idx + 1}`}
                </span>
                {item.is_external && (
                  <span className="rounded-full px-1.5 py-0.2 text-[9px] font-mono bg-warning-100 text-warning-800 dark:bg-warning-900/30 dark:text-warning-300">
                    External
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Selected Tab Preview Body */}
        <div className="p-4 bg-white dark:bg-gray-900">
          {activeItem && (
            <div>
              <div className="flex flex-wrap items-center justify-between text-xs text-gray-500 mb-2 gap-2">
                <span>
                  Target / Recipient: <strong>{activeItem.recipient_name}</strong>{" "}
                  {activeItem.recipient_contact && `(${activeItem.recipient_contact})`}
                </span>
                <span className="font-mono text-[10px] text-brand-600 dark:text-brand-400">
                  {activeItem.channel === "email"
                    ? "Sumopod SMTP (smtp.sumopod.com:465 SSL)"
                    : activeItem.channel === "whatsapp"
                    ? "WhatsApp Gateway (+62 Enterprise)"
                    : "Google Calendar & PostgreSQL"}
                </span>
              </div>
              {activeItem.subject && (
                <div className="mb-2 text-xs font-semibold text-gray-800 dark:text-gray-200">
                  Subject: {activeItem.subject}
                </div>
              )}
              <pre className="whitespace-pre-wrap rounded-lg bg-gray-50 p-3.5 text-xs text-gray-800 font-sans border border-gray-100 dark:border-gray-800 dark:bg-gray-800/40 dark:text-gray-200 leading-relaxed">
                {activeItem.content_preview}
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
            Click <strong>Approve &amp; Dispatch</strong> to approve. AI provides a <strong>60-second Undo Window</strong> before sending.
          </span>
        </div>

        <div className="flex items-center gap-2.5 justify-end">
          <Button variant="outline" size="md" onClick={onReject} disabled={!isHr || isApproving}>
            Reject Plan
          </Button>

          <Button
            variant="secondary"
            size="md"
            onClick={() => setIsEditSlotModalOpen(true)}
            disabled={!isHr || isApproving}
          >
            Edit Slot
          </Button>

          <div className="flex items-center gap-2">
            {!isHr && (
              <span className="text-[11px] font-semibold text-warning-600 dark:text-warning-400 flex items-center gap-1">
                <LockIcon />
                HR Approval Only
              </span>
            )}
            <Button
              variant="primary"
              size="md"
              isLoading={isApproving}
              disabled={!isHr || isApproving || Boolean(validationError)}
              onClick={handleApproveClick}
              startIcon={<BoltIcon className="text-white" />}
            >
              {isHr ? "Approve (+60s Undo)" : "HR Approval Required"}
            </Button>
          </div>
        </div>
      </div>

      {/* Modal: Edit Slot (TC-CHB-21) */}
      <Modal
        isOpen={isEditSlotModalOpen}
        onClose={() => setIsEditSlotModalOpen(false)}
        className="max-w-md p-6"
      >
        <div className="flex items-center justify-between border-b border-gray-100 pb-3 dark:border-gray-800">
          <h3 className="text-sm font-bold text-gray-900 dark:text-white">
            Edit Proposed Meeting Slot
          </h3>
        </div>

        <div className="mt-4 space-y-3">
          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
              Meeting Date:
            </label>
            <input
              type="date"
              value={editDate}
              onChange={(e) => setEditDate(e.target.value)}
              className="w-full rounded-lg border border-gray-300 p-2 text-xs dark:border-gray-700 dark:bg-gray-800 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
              Meeting Time (WIB):
            </label>
            <input
              type="time"
              value={editTime}
              onChange={(e) => setEditTime(e.target.value)}
              className="w-full rounded-lg border border-gray-300 p-2 text-xs dark:border-gray-700 dark:bg-gray-800 dark:text-white"
            />
          </div>

          <div className="pt-2 border-t border-gray-100 dark:border-gray-800">
            <span className="text-[11px] text-gray-500 dark:text-gray-400 block mb-1.5">
              Quick Test Slot Presets (Pillar PERMISSIONS &amp; BONUS):
            </span>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => {
                  setEditDate("2026-11-06"); // Friday
                  setEditTime("12:00");
                }}
                className="rounded-md bg-error-50 px-2 py-1 text-[11px] font-semibold text-error-700 dark:bg-error-500/15 dark:text-error-300 border border-error-200 dark:border-error-500/30"
              >
                Test Friday 12:00 WIB (Prayer Conflict)
              </button>
              <button
                type="button"
                onClick={() => {
                  setEditDate("2026-11-06");
                  setEditTime("14:00");
                }}
                className="rounded-md bg-success-50 px-2 py-1 text-[11px] font-semibold text-success-700 dark:bg-success-500/15 dark:text-success-300 border border-success-200 dark:border-success-500/30"
              >
                Safe Friday 14:00 WIB
              </button>
            </div>
          </div>
        </div>

        <div className="mt-5 flex justify-end gap-2 border-t border-gray-100 pt-3 dark:border-gray-800">
          <Button size="sm" variant="outline" onClick={() => setIsEditSlotModalOpen(false)}>
            Cancel
          </Button>
          <Button size="sm" variant="primary" onClick={handleSaveEditedSlot}>
            Apply &amp; Validate Slot
          </Button>
        </div>
      </Modal>

      {/* Modal: High-Impact External Send Confirmation (TC-CHB-22) */}
      <Modal
        isOpen={isHighImpactModalOpen}
        onClose={() => setIsHighImpactModalOpen(false)}
        className="max-w-lg p-6"
      >
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-warning-500 text-white shadow-theme-xs">
            <AlertIcon className="text-white" />
          </div>
          <div>
            <h3 className="text-base font-bold text-gray-900 dark:text-white">
              High-Impact External Send Confirmation
            </h3>
            <p className="mt-1 text-xs text-gray-600 dark:text-gray-400">
              This action plan involves external communications to candidates or external email domains. Please verify the recipient list below before dispatching:
            </p>
          </div>
        </div>

        <div className="mt-4 space-y-2 rounded-xl bg-gray-50 p-3.5 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700 max-h-48 overflow-y-auto">
          {externalRecipients.map((rec) => (
            <div
              key={rec.id}
              className="flex items-center justify-between rounded-lg bg-white p-2 text-xs shadow-2xs dark:bg-gray-800"
            >
              <div>
                <span className="font-bold text-gray-900 dark:text-white">
                  {rec.recipient_name}
                </span>{" "}
                <span className="text-gray-500 font-mono">({rec.recipient_contact})</span>
                <div className="text-[10px] text-gray-400">{rec.recipient_role}</div>
              </div>
              <span className="rounded bg-brand-50 px-2 py-0.5 text-[10px] font-mono font-semibold text-brand-700 dark:bg-brand-900/40 dark:text-brand-300">
                {rec.channel.toUpperCase()}
              </span>
            </div>
          ))}
        </div>

        <div className="mt-5 flex justify-end gap-2 border-t border-gray-100 pt-3 dark:border-gray-800">
          <Button size="sm" variant="outline" onClick={() => setIsHighImpactModalOpen(false)}>
            Review Again
          </Button>
          <Button size="sm" variant="primary" onClick={handleConfirmHighImpact}>
            Confirm High-Impact Dispatch
          </Button>
        </div>
      </Modal>
    </div>
  );
}
