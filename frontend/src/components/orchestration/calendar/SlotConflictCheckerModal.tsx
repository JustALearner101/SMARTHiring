"use client";

import React, { useEffect, useState } from "react";
import { Modal } from "@/components/ui/modal";
import Button from "@/components/ui/button/Button";
import {
  CalendarMatrixEvent,
  SlotConflictCheckRequest,
  SlotConflictCheckResult,
} from "@/types/orchestration";
import { InterviewerContact } from "@/types/master";
import { listContacts } from "@/services/masterService";
import { checkSlotConflict } from "@/services/orchestrationService";
import { AlertIcon, CheckCircleIcon, LockIcon, CheckLineIcon, CloseLineIcon } from "@/icons";

type ConflictTone = "success" | "warning" | "error";

function getConflictTone(status: SlotConflictCheckResult["status"]): ConflictTone {
  switch (status) {
    case "VALID":
      return "success";
    case "BLOCKED_FRIDAY_PRAYER":
    case "INSUFFICIENT_BUFFER":
      return "warning";
    default:
      return "error";
  }
}

const STATUS_LABELS: Record<SlotConflictCheckResult["status"], string> = {
  VALID: "VALID",
  CONFLICT_EXISTING_EVENT: "CONFLICT",
  BLOCKED_FRIDAY_PRAYER: "FRIDAY PRAYER BLOCK",
  OUTSIDE_WORKING_HOURS: "OUTSIDE WORKING HOURS",
  INSUFFICIENT_BUFFER: "INSUFFICIENT BUFFER",
};

const TONE_CONTAINER: Record<ConflictTone, string> = {
  success: "border-success-200 bg-success-50/70 dark:border-success-800 dark:bg-success-950/40",
  warning: "border-warning-200 bg-warning-50/70 dark:border-warning-800 dark:bg-warning-950/40",
  error: "border-error-200 bg-error-50/70 dark:border-error-800 dark:bg-error-950/40",
};

const TONE_ICON: Record<ConflictTone, string> = {
  success: "text-success-600 dark:text-success-400",
  warning: "text-warning-600 dark:text-warning-400",
  error: "text-error-600 dark:text-error-400",
};

const TONE_TITLE: Record<ConflictTone, string> = {
  success: "text-success-900 dark:text-success-200",
  warning: "text-warning-900 dark:text-warning-200",
  error: "text-error-900 dark:text-error-200",
};

const TONE_TEXT: Record<ConflictTone, string> = {
  success: "text-success-800 dark:text-success-300",
  warning: "text-warning-800 dark:text-warning-300",
  error: "text-error-800 dark:text-error-300",
};

const TONE_BADGE: Record<ConflictTone, string> = {
  success: "bg-success-100 text-success-800 dark:bg-success-500/20 dark:text-success-300",
  warning: "bg-warning-100 text-warning-800 dark:bg-warning-500/20 dark:text-warning-300",
  error: "bg-error-100 text-error-800 dark:bg-error-500/20 dark:text-error-300",
};

/** Backend alternatives may be "HH:MM" or a full "YYYY-MM-DD HH:MM TZ" string. */
function parseAlternative(
  alternative: string,
  fallbackDate: string
): { date: string; time: string } | null {
  const timeMatch = alternative.match(/(\d{1,2}:\d{2})/);
  if (!timeMatch) return null;
  const dateMatch = alternative.match(/(\d{4}-\d{2}-\d{2})/);
  return { date: dateMatch ? dateMatch[1] : fallbackDate, time: timeMatch[1] };
}

function alternativeLabel(alternative: string): string {
  return /^\d{1,2}:\d{2}$/.test(alternative) ? `${alternative} WIB` : alternative;
}

interface SlotConflictCheckerModalProps {
  isOpen: boolean;
  onClose: () => void;
  events: CalendarMatrixEvent[];
}

export default function SlotConflictCheckerModal({
  isOpen,
  onClose,
}: SlotConflictCheckerModalProps) {
  const [contacts, setContacts] = useState<InterviewerContact[]>([]);
  const [interviewerId, setInterviewerId] = useState("int-001");
  const [date, setDate] = useState("2026-10-30"); // Default Friday to test rule-jumatan
  const [time, setTime] = useState("12:00");
  const [duration, setDuration] = useState(60);
  const [result, setResult] = useState<SlotConflictCheckResult | null>(null);

  useEffect(() => {
    let cancelled = false;
    listContacts()
      .then((items) => {
        if (cancelled || !Array.isArray(items) || items.length === 0) return;
        setContacts(items);
        setInterviewerId((prev) =>
          items.some((c) => c.id === prev) ? prev : items[0].id
        );
      })
      .catch((error: unknown) => {
        console.error("Failed to fetch contacts for slot checker:", error);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const runCheck = async (req: SlotConflictCheckRequest) => {
    try {
      const apiResult = await checkSlotConflict(req);
      setResult(apiResult);
    } catch (error) {
      console.error("Failed to check slot conflict:", error);
    }
  };

  const handleTest = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    void runCheck({
      interviewer_id: interviewerId,
      date,
      time,
      duration_minutes: duration,
      timezone: "WIB",
    });
  };

  const setPreset = (pDate: string, pTime: string) => {
    setDate(pDate);
    setTime(pTime);
    void runCheck({
      interviewer_id: interviewerId,
      date: pDate,
      time: pTime,
      duration_minutes: duration,
      timezone: "WIB",
    });
  };

  const tone: ConflictTone = result ? getConflictTone(result.status) : "success";

  return (
    <Modal isOpen={isOpen} onClose={onClose} className="max-w-2xl p-6">
      <div className="flex items-start justify-between border-b border-gray-100 pb-4 dark:border-gray-800">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <LockIcon />
              <span>Test Slot Conflict & Rule Engine</span>
            </h3>
            <span className="rounded bg-brand-50 px-2 py-0.5 font-mono text-[10px] font-bold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
              PERMISSIONS & SOURCES
            </span>
          </div>
          <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
            An instant simulator to check whether a proposed time slot violates the rules regarding Friday prayers, work hours, or conflicts with other schedules.
          </p>
        </div>
      </div>

      {/* Preset 1-Click Quick Tests */}
      <div className="mt-4">
        <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block mb-1.5">
          Quick Test Presets:
        </span>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setPreset("2026-10-30", "12:00")}
            className="rounded-lg border border-warning-200 bg-warning-50 px-2.5 py-1 text-xs font-semibold text-warning-800 hover:bg-warning-100 dark:border-warning-800 dark:bg-warning-950/40 dark:text-warning-300"
          >
            <AlertIcon />
            Test Friday Prayer Block (Friday 12:00)
          </button>
          <button
            type="button"
            onClick={() => setPreset("2026-10-29", "08:00")}
            className="rounded-lg border border-error-200 bg-error-50 px-2.5 py-1 text-xs font-semibold text-error-800 hover:bg-error-100 dark:border-error-800 dark:bg-error-950/40 dark:text-error-300"
          >
            <CloseLineIcon />
            Test Outside Work Hours (08:00)
          </button>
          <button
            type="button"
            onClick={() => setPreset("2026-10-29", "10:00")}
            className="rounded-lg border border-success-200 bg-success-50 px-2.5 py-1 text-xs font-semibold text-success-800 hover:bg-success-100 dark:border-success-800 dark:bg-success-950/40 dark:text-success-300"
          >
            <CheckLineIcon />
            Test Valid Slot (Thursday 10:00)
          </button>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleTest} className="mt-4 space-y-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
              Interviewer:
            </label>
            <select
              value={interviewerId}
              onChange={(e) => setInterviewerId(e.target.value)}
              className="w-full rounded-xl border border-gray-300 bg-white p-2.5 text-xs text-gray-800 focus:border-brand-500 focus:outline-hidden dark:border-gray-700 dark:bg-gray-800 dark:text-white"
            >
              {contacts.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.name} ({i.role} - {i.timezone})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
              Tanggal (YYYY-MM-DD):
            </label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-full rounded-xl border border-gray-300 bg-white p-2.5 text-xs text-gray-800 focus:border-brand-500 focus:outline-hidden dark:border-gray-700 dark:bg-gray-800 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
              Jam Mulai (HH:mm):
            </label>
            <input
              type="time"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              className="w-full rounded-xl border border-gray-300 bg-white p-2.5 text-xs text-gray-800 focus:border-brand-500 focus:outline-hidden dark:border-gray-700 dark:bg-gray-800 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
              Durasi Wawancara:
            </label>
            <select
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="w-full rounded-xl border border-gray-300 bg-white p-2.5 text-xs text-gray-800 focus:border-brand-500 focus:outline-hidden dark:border-gray-700 dark:bg-gray-800 dark:text-white"
            >
              <option value={30}>30 Menit</option>
              <option value={45}>45 Menit</option>
              <option value={60}>60 Menit (1 Jam)</option>
              <option value={90}>90 Menit</option>
            </select>
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <Button size="sm" variant="outline" onClick={onClose} type="button">
            Tutup
          </Button>
          <Button size="sm" type="submit">
            Cek Validitas Slot Sekarang
          </Button>
        </div>
      </form>

      {/* Result Display */}
      {result && (
        <div
          className={`mt-4 rounded-xl border p-4 transition-all ${TONE_CONTAINER[tone]}`}
        >
          <div className="flex items-start gap-3">
            <div className={`mt-0.5 ${TONE_ICON[tone]}`}>
              {result.is_available ? <CheckCircleIcon /> : <AlertIcon />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h4 className={`text-xs font-bold ${TONE_TITLE[tone]}`}>
                  {result.is_available ? "SLOT VALID & TERSEDIA" : "SLOT DITOLAK OLEH ATURAN OPERASIONAL"}
                </h4>
                <span
                  className={`rounded px-1.5 py-0.2 font-mono text-[10px] font-bold shadow-xs ${TONE_BADGE[tone]}`}
                >
                  {STATUS_LABELS[result.status]}
                </span>
                {result.rule_code && (
                  <span className="rounded bg-white/80 dark:bg-gray-800 px-1.5 py-0.2 font-mono text-[10px] font-bold text-gray-800 dark:text-gray-200 shadow-xs">
                    {result.rule_code}
                  </span>
                )}
              </div>
              <p className={`mt-1 text-xs leading-relaxed ${TONE_TEXT[tone]}`}>
                {result.message}
              </p>

              {result.conflicting_event && (
                <p className={`mt-1 text-[11px] font-semibold ${TONE_TEXT[tone]}`}>
                  Bentrok dengan agenda: {result.conflicting_event}
                </p>
              )}

              {result.suggested_alternatives && result.suggested_alternatives.length > 0 && (
                <div className="mt-2.5 text-[11px] text-gray-600 dark:text-gray-400">
                  <span className="font-semibold block">Saran Jam Alternatif dari AI:</span>
                  <div className="mt-1 flex gap-1.5">
                    {result.suggested_alternatives.map((alt) => (
                      <button
                        key={alt}
                        type="button"
                        onClick={() => {
                          const parsed = parseAlternative(alt, date);
                          if (parsed) setPreset(parsed.date, parsed.time);
                        }}
                        className="rounded bg-white dark:bg-gray-800 px-2 py-0.5 font-mono text-xs font-bold text-brand-600 dark:text-brand-400 shadow-xs hover:bg-brand-50"
                      >
                        {alternativeLabel(alt)}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </Modal>
  );
}
