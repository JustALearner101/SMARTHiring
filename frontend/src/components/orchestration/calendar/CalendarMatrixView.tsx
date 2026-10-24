"use client";

import React, { useState } from "react";
import { CalendarMatrixEvent } from "@/types/orchestration";
import { AlertIcon, CheckCircleIcon, TimeIcon } from "@/icons";

interface CalendarMatrixViewProps {
  events: CalendarMatrixEvent[];
  selectedTimezone: "WIB" | "WITA" | "WIT";
  onSelectSlot?: (date: string, time: string) => void;
}

export default function CalendarMatrixView({
  events,
  selectedTimezone,
  onSelectSlot,
}: CalendarMatrixViewProps) {
  const [selectedInterviewerId, setSelectedInterviewerId] = useState<string>("int-001");
  const [selectedEvent, setSelectedEvent] = useState<CalendarMatrixEvent | null>(null);

  const interviewers = [
    { id: "int-001", name: "Budi Santoso", role: "VP of Engineering", dept: "Engineering", baseTz: "WIB" },
    { id: "int-002", name: "Siti Rahmawati", role: "Principal Engineer", dept: "Engineering", baseTz: "WIB" },
    { id: "int-006", name: "I Made Sukadana", role: "Regional Operations Director", dept: "Operations", baseTz: "WITA" },
  ];

  const currentInterviewer =
    interviewers.find((i) => i.id === selectedInterviewerId) || interviewers[0];

  // Week days for late October 2026: Mon 26 Oct - Fri 30 Oct 2026
  const weekDays = [
    { label: "Senin", dateStr: "2026-10-26", dayNum: "26 Okt" },
    { label: "Selasa", dateStr: "2026-10-27", dayNum: "27 Okt" },
    { label: "Rabu", dateStr: "2026-10-28", dayNum: "28 Okt" },
    { label: "Kamis", dateStr: "2026-10-29", dayNum: "29 Okt" },
    { label: "Jumat", dateStr: "2026-10-30", dayNum: "30 Okt", isFriday: true },
  ];

  const hours = [
    "08:00",
    "09:00",
    "10:00",
    "11:00",
    "12:00",
    "13:00",
    "14:00",
    "15:00",
    "16:00",
    "17:00",
  ];

  // Filter events for the selected interviewer
  const interviewerEvents = events.filter(
    (e) => e.interviewer_id === selectedInterviewerId
  );

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
      {/* Top Controls & Interviewer Filter */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-gray-100 pb-4 dark:border-gray-800">
        <div className="flex items-center gap-3">
          <label className="text-xs font-bold text-gray-700 dark:text-gray-300">
            Pilih Interviewer:
          </label>
          <select
            value={selectedInterviewerId}
            onChange={(e) => setSelectedInterviewerId(e.target.value)}
            className="rounded-xl border border-gray-200 bg-white px-3 py-1.5 text-xs font-bold text-brand-700 shadow-theme-xs focus:border-brand-500 focus:outline-hidden dark:border-gray-800 dark:bg-gray-800 dark:text-brand-300"
          >
            {interviewers.map((i) => (
              <option key={i.id} value={i.id}>
                {i.name} — {i.role} ({i.baseTz})
              </option>
            ))}
          </select>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-3 text-[11px]">
          <span className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
            <span className="h-2.5 w-2.5 rounded-full bg-brand-500" />
            Interview Terjadwal (AI)
          </span>
          <span className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
            <span className="h-2.5 w-2.5 rounded-full bg-purple-500" />
            Rapat Internal
          </span>
          <span className="flex items-center gap-1.5 font-bold text-warning-700 dark:text-warning-400">
            <span className="h-2.5 w-2.5 rounded-full bg-warning-500" />
            [rule-jumatan] Sholat Jumat
          </span>
        </div>
      </div>

      {/* Week Grid */}
      <div className="mt-4 overflow-x-auto">
        <div className="min-w-[700px]">
          {/* Header Row: Days */}
          <div className="grid grid-cols-6 border-b border-gray-200 dark:border-gray-800 pb-2 text-center text-xs font-bold text-gray-700 dark:text-gray-300">
            <div className="text-start ps-2 font-mono text-gray-400">
              Jam ({selectedTimezone})
            </div>
            {weekDays.map((d) => (
              <div
                key={d.dateStr}
                className={`py-1 rounded-lg ${
                  d.isFriday
                    ? "bg-warning-50/60 dark:bg-warning-500/10 text-warning-900 dark:text-warning-200 font-extrabold"
                    : ""
                }`}
              >
                <span>{d.label}</span>
                <span className="block text-[11px] font-normal text-gray-400">
                  {d.dayNum}
                </span>
              </div>
            ))}
          </div>

          {/* Time Rows */}
          <div className="divide-y divide-gray-100 dark:divide-gray-800/60 text-xs">
            {hours.map((hour) => {
              const hourNum = parseInt(hour.split(":")[0]);
              const isNonWorking = hourNum < 9 || hourNum >= 17;

              return (
                <div
                  key={hour}
                  className={`grid grid-cols-6 items-stretch min-h-[58px] ${
                    isNonWorking
                      ? "bg-gray-50/70 dark:bg-gray-800/30 text-gray-400"
                      : ""
                  }`}
                >
                  {/* Time label */}
                  <div className="ps-2 py-2 font-mono text-[11px] text-gray-400 border-e border-gray-100 dark:border-gray-800">
                    {hour}
                  </div>

                  {/* 5 Day Cells */}
                  {weekDays.map((d) => {
                    // Check if this cell is Friday Prayer block (11:30 - 13:00 on Friday)
                    const isFridayPrayerHour =
                      d.isFriday && (hour === "11:00" || hour === "12:00");

                    // Find events matching this day and hour
                    const cellEvents = interviewerEvents.filter((e) => {
                      const eDate = e.start.split("T")[0];
                      const eHour = parseInt(e.start.split("T")[1].split(":")[0]);
                      return eDate === d.dateStr && eHour === hourNum;
                    });

                    return (
                      <div
                        key={d.dateStr}
                        onClick={() =>
                          !isFridayPrayerHour &&
                          !isNonWorking &&
                          onSelectSlot &&
                          onSelectSlot(d.dateStr, hour)
                        }
                        className={`p-1 border-e border-gray-100 dark:border-gray-800 relative transition-all ${
                          isFridayPrayerHour
                            ? "bg-warning-100/40 dark:bg-warning-900/20 cursor-not-allowed"
                            : isNonWorking
                            ? "cursor-not-allowed"
                            : "hover:bg-brand-50/30 cursor-pointer"
                        }`}
                      >
                        {/* Friday Prayer Block Banner */}
                        {isFridayPrayerHour && hour === "11:00" && (
                          <div className="absolute inset-x-1 inset-y-1 z-10 flex flex-col justify-center rounded-lg border border-dashed border-warning-400 bg-warning-50 p-2 text-center text-[10px] font-bold text-warning-800 shadow-xs dark:border-warning-700 dark:bg-warning-950/60 dark:text-warning-300">
                            <span className="flex items-center justify-center gap-1">
                              <AlertIcon />
                              <span>BLOCKED</span>
                            </span>
                            <span className="text-[9px] font-mono mt-0.5">
                              [rule-jumatan] Sholat Jumat
                            </span>
                          </div>
                        )}

                        {/* Existing Events */}
                        {cellEvents.map((evt) => {
                          const isInterview = evt.event_type === "SCHEDULED_INTERVIEW";
                          const isMeeting = evt.event_type === "TEAM_MEETING";
                          const isOOO = evt.event_type === "OUT_OF_OFFICE";

                          if (evt.event_type === "FRIDAY_PRAYER_BLOCK") return null;

                          return (
                            <div
                              key={evt.id}
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedEvent(evt);
                              }}
                              className={`rounded-lg p-1.5 text-[10px] leading-tight shadow-xs transition-transform hover:scale-[1.02] ${
                                isInterview
                                  ? "bg-brand-500 text-white font-semibold"
                                  : isMeeting
                                  ? "bg-purple-100 text-purple-900 dark:bg-purple-900/40 dark:text-purple-200 border border-purple-200 dark:border-purple-800"
                                  : "bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-300"
                              }`}
                            >
                              <div className="flex items-center gap-1 truncate">
                                {isInterview && <CheckCircleIcon />}
                                <span className="truncate">{evt.title}</span>
                              </div>
                              <span className="mt-0.5 block font-mono text-[9px] opacity-80">
                                {evt.start.split("T")[1].slice(0, 5)} -{" "}
                                {evt.end.split("T")[1].slice(0, 5)}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Selected Event Details Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-sm rounded-2xl border border-gray-200 bg-white p-5 shadow-theme-lg dark:border-gray-800 dark:bg-gray-900">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3 dark:border-gray-800">
              <h4 className="text-sm font-bold text-gray-900 dark:text-white">
                Detail Agenda Kalender
              </h4>
              <button
                onClick={() => setSelectedEvent(null)}
                className="text-gray-400 hover:text-gray-600 text-xs"
              >
                Tutup
              </button>
            </div>
            <div className="mt-3 space-y-2 text-xs">
              <div>
                <span className="text-gray-400 block text-[10px]">Judul:</span>
                <span className="font-bold text-gray-900 dark:text-white">
                  {selectedEvent.title}
                </span>
              </div>
              <div>
                <span className="text-gray-400 block text-[10px]">Interviewer:</span>
                <span className="text-gray-700 dark:text-gray-300">
                  {currentInterviewer.name} ({currentInterviewer.dept})
                </span>
              </div>
              <div>
                <span className="text-gray-400 block text-[10px]">Waktu:</span>
                <span className="font-mono text-brand-600 dark:text-brand-400">
                  {selectedEvent.start.replace("T", " ")} s/d {selectedEvent.end.split("T")[1]}
                </span>
              </div>
              {selectedEvent.description && (
                <div>
                  <span className="text-gray-400 block text-[10px]">Keterangan:</span>
                  <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                    {selectedEvent.description}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
