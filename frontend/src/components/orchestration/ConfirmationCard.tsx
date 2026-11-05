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

  const planItems = useMemo(() => plan.items ?? [], [plan.items]);
  const sourcesCited = plan.sources_cited ?? [];

  // Derive initial items from plan.items (WhatsApp taken out -> Email only)
  const initialCandItem = planItems.find(
    (i) => i.recipient_role.toLowerCase().includes("candidate")
  );
  const hasCandidateItem = Boolean(initialCandItem);

  // Kanal pengiriman dikunci ke Official Email (Sumopod SMTP)
  const candidateChannel = "email" as const;
  const interviewerChannel = "email" as const;

  const [activeTabId, setActiveTabId] = useState<string>(() => planItems[0]?.id || "item-01");
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

  // Active slot (supports local slot edits & meeting platform/link edits)
  const [currentSlot, setCurrentSlot] = useState<ProposedSlot>(plan.proposed_slot);
  const [slotEdited, setSlotEdited] = useState(false);

  // Editable draft overrides per action item id (TC-SCHED-18)
  const [editedDrafts, setEditedDrafts] = useState<Record<string, string>>({});

  const MEETING_PLATFORM_OPTIONS = [
    "Google Meet",
    "Microsoft Teams",
    "Zoom Meeting",
    "On-Site / Custom",
  ] as const;

  const DEFAULT_PLATFORM_LINKS: Record<string, string> = {
    "Google Meet": "https://meet.google.com/hkt-ops-2026",
    "Microsoft Teams": "https://teams.microsoft.com/l/meetup-join/heketon-ops-2026",
    "Zoom Meeting": "https://zoom.us/j/98234123890",
    "On-Site / Custom": "Ruang Rapat Utama HQ Jakarta",
  };

  const detectPlatformFromUrl = (url: string, currentPlatform: string): string => {
    const lower = url.toLowerCase();
    if (lower.includes("teams.microsoft.com") || lower.includes("teams.live.com")) {
      return "Microsoft Teams";
    }
    if (lower.includes("meet.google.com")) {
      return "Google Meet";
    }
    if (lower.includes("zoom.us") || lower.includes("zoom.com")) {
      return "Zoom Meeting";
    }
    return currentPlatform;
  };

  const handlePlatformChange = (newPlatform: string) => {
    setCurrentSlot((prev) => {
      const isDefaultLink = Object.values(DEFAULT_PLATFORM_LINKS).includes(
        prev.meeting_link.trim()
      );
      const nextLink = isDefaultLink
        ? DEFAULT_PLATFORM_LINKS[newPlatform] || prev.meeting_link
        : prev.meeting_link;
      const nextTitle = prev.title.startsWith("Follow-Up Meeting:")
        ? `Follow-Up Meeting: ${newPlatform}`
        : prev.title;

      return {
        ...prev,
        title: nextTitle,
        location_type: newPlatform,
        meeting_link: nextLink,
      };
    });
    setSlotEdited(true);
  };

  const handleMeetingLinkChange = (newLink: string) => {
    setCurrentSlot((prev) => {
      const detectedPlatform = detectPlatformFromUrl(newLink, prev.location_type);
      const nextTitle = prev.title.startsWith("Follow-Up Meeting:")
        ? `Follow-Up Meeting: ${detectedPlatform}`
        : prev.title;

      return {
        ...prev,
        title: nextTitle,
        location_type: detectedPlatform,
        meeting_link: newLink,
      };
    });
    setSlotEdited(true);
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(currentSlot.meeting_link);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  // Contact addresses & timezones
  const candEmail = plan.candidate_email || "candidate@example.com";
  const candTz = (plan.candidate_timezone || "WIB").toUpperCase();
  const interEmail = plan.interviewer_email || "budi.santoso@company.com";
  const interTz = (plan.interviewer_timezone || "WIB").toUpperCase();

  // Build reactive customized action items from backend plan.items
  const customizedItems = useMemo<ActionItemDraft[]>(() => {
    const candSlotDisplay =
      candTz === "WITA"
        ? currentSlot.formatted_wita
        : candTz === "WIT"
        ? currentSlot.formatted_wit || currentSlot.formatted_wib
        : currentSlot.formatted_wib;
    const interSlotDisplay =
      interTz === "WITA"
        ? currentSlot.formatted_wita
        : interTz === "WIT"
        ? currentSlot.formatted_wit || currentSlot.formatted_wib
        : currentSlot.formatted_wib;
    const allTzDisplay = [
      currentSlot.formatted_wib,
      currentSlot.formatted_wita,
      currentSlot.formatted_wit,
    ]
      .filter(Boolean)
      .join(" = ");

    return planItems.map((it) => {
      const isCand = it.recipient_role.toLowerCase().includes("candidate");
      const isInter =
        !isCand &&
        it.channel !== "calendar" &&
        (it.recipient_role.toLowerCase().includes("interviewer") ||
          it.recipient_role.toLowerCase().includes("host") ||
          it.recipient_name === plan.interviewer_name);

      const manualDraft = editedDrafts[it.id];

      if (isCand) {
        const defaultCandPreview =
          candidateChannel === it.channel && !slotEdited
            ? it.content_preview
            : `Halo ${plan.candidate_name},\n\nKami mengundang Anda untuk mengikuti User Technical Interview posisi ${plan.candidate_position} bersama ${plan.interviewer_name}:\n- Jadwal Waktu Lokal Anda (${candTz}): ${candSlotDisplay}\n- Konversi Zona Waktu: ${allTzDisplay}\n- Durasi: ${currentSlot.duration_minutes} Menit\n- Lokasi / Tautan: ${currentSlot.location_type} (${currentSlot.meeting_link})\n\nMohon konfirmasi ketersediaan Anda. Terima kasih,\nTim HR`;

        return {
          ...it,
          channel: candidateChannel,
          action_type: "send_email",
          recipient_contact: candEmail,
          is_external: true,
          content_preview: manualDraft !== undefined ? manualDraft : defaultCandPreview,
        };
      }

      if (isInter) {
        const isNotulenDraft =
          it.subject?.toLowerCase().includes("notulen") ||
          it.content_preview.toLowerCase().includes("notulen");

        let updatedNotulenPreview = it.content_preview;
        if (isNotulenDraft && slotEdited) {
          const baseLines = it.content_preview
            .split("\n")
            .filter((line) => !line.startsWith("- Lokasi / Tautan:"))
            .map((line) =>
              line.startsWith("- Jadwal Follow-Up")
                ? `- Jadwal Follow-Up (${interTz}): ${interSlotDisplay} (${allTzDisplay})\n- Lokasi / Tautan: ${currentSlot.location_type} (${currentSlot.meeting_link})`
                : line
            );
          updatedNotulenPreview = baseLines.join("\n");
          if (!updatedNotulenPreview.includes("- Lokasi / Tautan:")) {
            updatedNotulenPreview += `\n- Lokasi / Tautan: ${currentSlot.location_type} (${currentSlot.meeting_link})`;
          }
        }

        const defaultInterPreview =
          interviewerChannel === it.channel && !slotEdited
            ? it.content_preview
            : isNotulenDraft
            ? updatedNotulenPreview
            : `Yth. ${plan.interviewer_name},\n\nBerikut undangan User Technical Interview bersama kandidat ${plan.candidate_name} (${plan.candidate_position}):\n- Jadwal (${interTz}): ${interSlotDisplay}\n- Konversi Zona Waktu: ${allTzDisplay}\n- Durasi: ${currentSlot.duration_minutes} Menit\n- Lokasi / Tautan: ${currentSlot.location_type} (${currentSlot.meeting_link})\n\nSalam,\nHR & Talent Acquisition`;

        return {
          ...it,
          channel: interviewerChannel,
          action_type: "send_email",
          recipient_contact: interEmail,
          content_preview: manualDraft !== undefined ? manualDraft : defaultInterPreview,
        };
      }

      if (it.channel === "calendar" && slotEdited && manualDraft === undefined) {
        return {
          ...it,
          subject: `${currentSlot.title} (${currentSlot.location_type})`,
          content_preview: `Reservasi slot kalender pada ${interSlotDisplay} (${allTzDisplay}) di ${currentSlot.location_type} (${currentSlot.meeting_link}) — ${currentSlot.duration_minutes} Menit.`,
        };
      }

      return manualDraft !== undefined ? { ...it, content_preview: manualDraft } : it;
    });
  }, [
    planItems,
    candidateChannel,
    interviewerChannel,
    candEmail,
    candTz,
    interEmail,
    interTz,
    plan.candidate_name,
    plan.candidate_position,
    plan.interviewer_name,
    currentSlot,
    slotEdited,
    editedDrafts,
  ]);

  const activeItem =
    customizedItems.find((i) => i.id === activeTabId) || customizedItems[0];

  const externalRecipients = useMemo(() => {
    return customizedItems.filter((i) => i.is_external);
  }, [customizedItems]);

  const isHighImpactAction =
    plan.is_high_impact ||
    hasCandidateItem ||
    externalRecipients.length > 0;

  // Handle Approve Click
  const handleApproveClick = () => {
    const updatedPlan: ActionPlan = {
      ...plan,
      proposed_slot: currentSlot,
      is_high_impact: isHighImpactAction,
      items: customizedItems,
    };

    // If a slot rule violation was forced (TC-CHB-21), submit directly to backend
    // so Secondary Validator Guard rejects with 409 and records VALIDATION_VIOLATION_BLOCKED in AuditLog
    if (validationError) {
      onApprove(updatedPlan);
      return;
    }

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
  const applyEditedSlot = (targetDateStr: string, targetTimeStr: string) => {
    const [hh, mm] = targetTimeStr.split(":").map(Number);
    const safeH = Number.isFinite(hh) ? hh : 14;
    const safeM = Number.isFinite(mm) ? mm : 0;
    const timeVal = safeH * 60 + safeM;

    // Construct ISO UTC timestamp from WIB (+07:00)
    const wibIso = `${targetDateStr}T${String(safeH).padStart(2, "0")}:${String(safeM).padStart(2, "0")}:00+07:00`;
    const startUtcDate = new Date(wibIso);
    const endUtcDate = new Date(startUtcDate.getTime() + (currentSlot.duration_minutes || 60) * 60 * 1000);
    const dayOfWeek = startUtcDate.getUTCDay(); // At 02:00-10:00 UTC, UTC day == WIB day (5 is Friday)

    const dateObj = new Date(`${targetDateStr}T${String(safeH).padStart(2, "0")}:${String(safeM).padStart(2, "0")}:00`);
    const dateStr = dateObj.toLocaleDateString("en-US", {
      weekday: "long",
      day: "2-digit",
      month: "short",
      year: "numeric",
    });

    setCurrentSlot((prev) => ({
      ...prev,
      start_utc: !Number.isNaN(startUtcDate.getTime()) ? startUtcDate.toISOString() : prev.start_utc,
      end_utc: !Number.isNaN(endUtcDate.getTime()) ? endUtcDate.toISOString() : prev.end_utc,
      formatted_wib: `${dateStr}, ${String(safeH).padStart(2, "0")}:${String(safeM).padStart(2, "0")} WIB`,
      formatted_wita: `${dateStr}, ${String((safeH + 1) % 24).padStart(2, "0")}:${String(safeM).padStart(2, "0")} WITA`,
      formatted_wit: `${dateStr}, ${String((safeH + 2) % 24).padStart(2, "0")}:${String(safeM).padStart(2, "0")} WIT`,
    }));
    setSlotEdited(true);

    // Friday prayer window: 11:30 (690m) to 13:00 (780m)
    if (dayOfWeek === 5 && timeVal >= 690 && timeVal < 780) {
      setValidationError(
        `Secondary Validator Alert (Rule Violation Detected): Slot Friday ${targetTimeStr} WIB overlaps with Friday prayer blackout [rule-jumatan] (11:30 - 13:00 WIB). Approving this slot will be blocked by the Secondary Validator and logged to Audit Logs.`
      );
      setIsEditSlotModalOpen(false);
      return;
    }

    // Working hours: 09:00 (540m) to 17:00 (1020m)
    if (timeVal < 540 || timeVal >= 1020) {
      setValidationError(
        `Secondary Validator Alert (Rule Violation Detected): Slot ${targetTimeStr} WIB is outside official operational working hours (09:00 - 17:00 WIB) [rule-working-hours]. Approving this slot will be blocked by the Secondary Validator and logged to Audit Logs.`
      );
      setIsEditSlotModalOpen(false);
      return;
    }

    setValidationError(null);
    setIsEditSlotModalOpen(false);
  };

  const handleSaveEditedSlot = () => {
    applyEditedSlot(editDate, editTime);
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
                Live SMTP Email Gateway
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
                    applyEditedSlot(editDate, "14:00");
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

        {/* WHERE: Platform & Link (Interactive Selector + Custom URL Input) */}
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
          <div className="mt-2 space-y-1.5">
            <select
              value={
                MEETING_PLATFORM_OPTIONS.includes(
                  currentSlot.location_type as (typeof MEETING_PLATFORM_OPTIONS)[number]
                )
                  ? currentSlot.location_type
                  : "On-Site / Custom"
              }
              disabled={!isHr || isApproving}
              onChange={(e) => handlePlatformChange(e.target.value)}
              aria-label="Meeting Platform"
              className="w-full rounded-lg border border-gray-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-gray-900 focus:border-brand-500 focus:outline-hidden focus:ring-2 focus:ring-brand-500/15 dark:border-gray-700 dark:bg-gray-800 dark:text-white"
            >
              {MEETING_PLATFORM_OPTIONS.map((platform) => (
                <option key={platform} value={platform}>
                  {platform}
                </option>
              ))}
            </select>
            <input
              type="text"
              value={currentSlot.meeting_link}
              disabled={!isHr || isApproving}
              onChange={(e) => handleMeetingLinkChange(e.target.value)}
              placeholder="Paste link Google Meet / Microsoft Teams / Zoom..."
              aria-label="Meeting Link URL"
              className="w-full rounded-lg border border-gray-200 bg-white px-2.5 py-1 text-[11px] font-mono text-gray-700 placeholder-gray-400 focus:border-brand-500 focus:outline-hidden focus:ring-2 focus:ring-brand-500/15 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200"
            />
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
          </div>
        </div>

        <div className={`mt-3.5 grid grid-cols-1 ${hasCandidateItem ? "md:grid-cols-2" : ""} gap-3.5`}>
          {/* Candidate Card (only shown when plan includes a candidate action item) */}
          {hasCandidateItem && (
            <div className="rounded-xl border border-brand-200 bg-white p-4 shadow-xs transition-all dark:border-brand-800 dark:bg-gray-800/90">
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

              {/* Official Email Channel Indicator (WhatsApp Taken Out) */}
              <div className="mt-3.5">
                <div className="flex rounded-lg bg-gray-100 p-1 dark:bg-gray-900">
                  <div
                    className="flex-1 flex items-center justify-center gap-1.5 rounded-md bg-white py-1.5 text-xs font-semibold text-brand-700 shadow-xs dark:bg-gray-800 dark:text-brand-300"
                    title="Official Email via Sumopod SMTP"
                  >
                    <EnvelopeIcon className="shrink-0" />
                    <span>Email</span>
                  </div>
                </div>

                {/* Destination Contact Handle Bar */}
                <div className="mt-2.5 flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 border border-gray-100 dark:bg-gray-900/60 dark:border-gray-800 text-xs">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <span className="text-gray-400 font-mono text-[11px]">Send to:</span>
                    <strong className="text-gray-900 dark:text-white font-mono truncate">
                      {candEmail}
                    </strong>
                  </div>
                  <span className="shrink-0 rounded bg-brand-50 px-1.5 py-0.5 text-[10px] font-mono font-semibold text-brand-700 dark:bg-brand-900/40 dark:text-brand-300">
                    Sumopod SSL 465
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Interviewer Card */}
          <div className="rounded-xl border border-brand-200 bg-white p-4 shadow-xs transition-all dark:border-brand-800 dark:bg-gray-800/90">
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

            {/* Official Email Channel Indicator (WhatsApp Taken Out) */}
            <div className="mt-3.5">
              <div className="flex rounded-lg bg-gray-100 p-1 dark:bg-gray-900">
                <div
                  className="flex-1 flex items-center justify-center gap-1.5 rounded-md bg-white py-1.5 text-xs font-semibold text-brand-700 shadow-xs dark:bg-gray-800 dark:text-brand-300"
                  title="Official Email via Sumopod SMTP"
                >
                  <EnvelopeIcon className="shrink-0" />
                  <span>Email</span>
                </div>
              </div>

              {/* Destination Contact Handle Bar */}
              <div className="mt-2.5 flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 border border-gray-100 dark:bg-gray-900/60 dark:border-gray-800 text-xs">
                <div className="flex items-center gap-1.5 min-w-0">
                  <span className="text-gray-400 font-mono text-[11px]">Send to:</span>
                  <strong className="text-gray-900 dark:text-white font-mono truncate">
                    {interEmail}
                  </strong>
                </div>
                <span className="shrink-0 rounded bg-brand-50 px-1.5 py-0.5 text-[10px] font-mono font-semibold text-brand-700 dark:bg-brand-900/40 dark:text-brand-300">
                  Sumopod SSL 465
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

        {/* Selected Tab Preview Body (TC-SCHED-18: Editable Message Drafts) */}
        <div className="p-4 bg-white dark:bg-gray-900">
          {activeItem && (
            <div>
              <div className="flex flex-wrap items-center justify-between text-xs text-gray-500 mb-2 gap-2">
                <span>
                  Target / Recipient: <strong>{activeItem.recipient_name}</strong>{" "}
                  {activeItem.recipient_contact && `(${activeItem.recipient_contact})`}
                </span>
                <div className="flex items-center gap-2">
                  {editedDrafts[activeItem.id] !== undefined && (
                    <button
                      type="button"
                      onClick={() =>
                        setEditedDrafts((prev) => {
                          const next = { ...prev };
                          delete next[activeItem.id];
                          return next;
                        })
                      }
                      className="text-[10px] font-semibold text-brand-600 hover:underline dark:text-brand-400"
                    >
                      Reset Draft
                    </button>
                  )}
                  <span className="font-mono text-[10px] text-brand-600 dark:text-brand-400">
                    {activeItem.channel === "email"
                      ? "Sumopod SMTP (smtp.sumopod.com:465 SSL)"
                      : activeItem.channel === "whatsapp"
                      ? "WhatsApp Gateway (+62 Enterprise)"
                      : "Google Calendar & PostgreSQL"}
                  </span>
                </div>
              </div>
              {activeItem.subject && (
                <div className="mb-2 text-xs font-semibold text-gray-800 dark:text-gray-200">
                  Subject: {activeItem.subject}
                </div>
              )}
              <textarea
                rows={7}
                value={activeItem.content_preview}
                disabled={!isHr || isApproving}
                onChange={(e) => {
                  const val = e.target.value;
                  setEditedDrafts((prev) => ({
                    ...prev,
                    [activeItem.id]: val,
                  }));
                }}
                aria-label={`Message draft for ${activeItem.recipient_name}`}
                className="w-full whitespace-pre-wrap rounded-lg bg-gray-50 p-3.5 text-xs text-gray-800 font-sans border border-gray-200 focus:border-brand-500 focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-brand-500/15 dark:border-gray-800 dark:bg-gray-800/40 dark:text-gray-200 leading-relaxed transition-colors"
              />
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
            {sourcesCited.length} valid sources
          </span>
        </div>

        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {sourcesCited.map((src) => (
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
      <div className="mt-6 flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between pt-4 border-t border-gray-100 dark:border-gray-800">
        <div className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400">
          <AlertIcon className="text-warning-500 shrink-0" />
          <span>
            Click <strong>Approve &amp; Dispatch</strong> to approve. AI provides a <strong>60-second Undo Window</strong> before sending.
          </span>
        </div>

        <div className="flex items-center gap-2.5 justify-end shrink-0 flex-wrap sm:flex-nowrap">
          <Button
            variant="outline"
            size="md"
            onClick={onReject}
            disabled={!isHr || isApproving}
            className="shrink-0 whitespace-nowrap"
          >
            Reject Plan
          </Button>

          <Button
            variant="secondary"
            size="md"
            onClick={() => setIsEditSlotModalOpen(true)}
            disabled={!isHr || isApproving}
            className="shrink-0 whitespace-nowrap"
          >
            Edit Slot
          </Button>

          <div className="flex items-center gap-2 shrink-0">
            {!isHr && (
              <span className="text-[11px] font-semibold text-warning-600 dark:text-warning-400 flex items-center gap-1 whitespace-nowrap">
                <LockIcon />
                HR Approval Only
              </span>
            )}
            <Button
              variant="primary"
              size="md"
              isLoading={isApproving}
              disabled={!isHr || isApproving}
              onClick={handleApproveClick}
              startIcon={<BoltIcon className="text-white shrink-0" />}
              className="shrink-0 whitespace-nowrap"
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
              Quick Test Slot Presets (&amp; BONUS):
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
