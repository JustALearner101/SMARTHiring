"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/modal";
import Button from "@/components/ui/button/Button";
import {
  CalendarMatrixEvent,
  SlotConflictCheckRequest,
  SlotConflictCheckResult,
} from "@/types/orchestration";
import { checkSlotAvailability } from "@/data/mockThreadAndCalendarData";
import { AlertIcon, CheckCircleIcon, LockIcon } from "@/icons";

interface SlotConflictCheckerModalProps {
  isOpen: boolean;
  onClose: () => void;
  events: CalendarMatrixEvent[];
}

export default function SlotConflictCheckerModal({
  isOpen,
  onClose,
  events,
}: SlotConflictCheckerModalProps) {
  const [interviewerId, setInterviewerId] = useState("int-001");
  const [date, setDate] = useState("2026-10-30"); // Default Friday to test rule-jumatan
  const [time, setTime] = useState("12:00");
  const [duration, setDuration] = useState(60);
  const [result, setResult] = useState<SlotConflictCheckResult | null>(null);

  const interviewers = [
    { id: "int-001", name: "Budi Santoso (VP Eng - WIB)" },
    { id: "int-002", name: "Siti Rahmawati (Principal Eng - WIB)" },
    { id: "int-006", name: "I Made Sukadana (Regional Ops - WITA)" },
  ];

  const handleTest = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const req: SlotConflictCheckRequest = {
      interviewer_id: interviewerId,
      date,
      time,
      duration_minutes: duration,
      timezone: "WIB",
    };
    const checkRes = checkSlotAvailability(req, events);
    setResult(checkRes);
  };

  const setPreset = (pDate: string, pTime: string) => {
    setDate(pDate);
    setTime(pTime);
    const req: SlotConflictCheckRequest = {
      interviewer_id: interviewerId,
      date: pDate,
      time: pTime,
      duration_minutes: duration,
      timezone: "WIB",
    };
    const checkRes = checkSlotAvailability(req, events);
    setResult(checkRes);
  };

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
            Simulator instan untuk menguji apakah usulan slot melanggar aturan Sholat Jumat, jam kerja, atau bentrok agenda.
          </p>
        </div>
      </div>

      {/* Preset 1-Click Quick Tests */}
      <div className="mt-4">
        <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block mb-1.5">
          Preset Uji Coba Cepat (Hackathon Showcase):
        </span>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setPreset("2026-10-30", "12:00")}
            className="rounded-lg border border-warning-200 bg-warning-50 px-2.5 py-1 text-xs font-semibold text-warning-800 hover:bg-warning-100 dark:border-warning-800 dark:bg-warning-950/40 dark:text-warning-300"
          >
            ⚠️ Uji Blokir Sholat Jumat (Jumat 12:00)
          </button>
          <button
            type="button"
            onClick={() => setPreset("2026-10-29", "08:00")}
            className="rounded-lg border border-error-200 bg-error-50 px-2.5 py-1 text-xs font-semibold text-error-800 hover:bg-error-100 dark:border-error-800 dark:bg-error-950/40 dark:text-error-300"
          >
            ❌ Uji Luar Jam Kerja (08:00)
          </button>
          <button
            type="button"
            onClick={() => setPreset("2026-10-29", "10:00")}
            className="rounded-lg border border-success-200 bg-success-50 px-2.5 py-1 text-xs font-semibold text-success-800 hover:bg-success-100 dark:border-success-800 dark:bg-success-950/40 dark:text-success-300"
          >
            ✓ Uji Slot Valid (Kamis 10:00)
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
              {interviewers.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.name}
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
          className={`mt-4 rounded-xl border p-4 transition-all ${
            result.is_available
              ? "border-success-200 bg-success-50/70 dark:border-success-800 dark:bg-success-950/40"
              : "border-error-200 bg-error-50/70 dark:border-error-800 dark:bg-error-950/40"
          }`}
        >
          <div className="flex items-start gap-3">
            <div
              className={`mt-0.5 ${
                result.is_available
                  ? "text-success-600 dark:text-success-400"
                  : "text-error-600 dark:text-error-400"
              }`}
            >
              {result.is_available ? <CheckCircleIcon /> : <AlertIcon />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h4
                  className={`text-xs font-bold ${
                    result.is_available
                      ? "text-success-900 dark:text-success-200"
                      : "text-error-900 dark:text-error-200"
                  }`}
                >
                  {result.is_available ? "SLOT VALID & TERSEDIA" : "SLOT DITOLAK OLEH ATURAN OPERASIONAL"}
                </h4>
                {result.rule_code && (
                  <span className="rounded bg-white/80 dark:bg-gray-800 px-1.5 py-0.2 font-mono text-[10px] font-bold text-gray-800 dark:text-gray-200 shadow-xs">
                    {result.rule_code}
                  </span>
                )}
              </div>
              <p
                className={`mt-1 text-xs leading-relaxed ${
                  result.is_available
                    ? "text-success-800 dark:text-success-300"
                    : "text-error-800 dark:text-error-300"
                }`}
              >
                {result.message}
              </p>

              {result.suggested_alternatives && (
                <div className="mt-2.5 text-[11px] text-gray-600 dark:text-gray-400">
                  <span className="font-semibold block">Saran Jam Alternatif dari AI:</span>
                  <div className="mt-1 flex gap-1.5">
                    {result.suggested_alternatives.map((alt) => (
                      <button
                        key={alt}
                        type="button"
                        onClick={() => setPreset(date, alt)}
                        className="rounded bg-white dark:bg-gray-800 px-2 py-0.5 font-mono text-xs font-bold text-brand-600 dark:text-brand-400 shadow-xs hover:bg-brand-50"
                      >
                        {alt} WIB
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
