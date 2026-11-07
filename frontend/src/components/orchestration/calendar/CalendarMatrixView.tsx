"use client";

import React, { useMemo, useState } from "react";
import { CalendarMatrixEvent } from "@/types/orchestration";
import { InterviewerContact, OperationalPolicy } from "@/types/master";
import { AlertIcon, CheckCircleIcon, ChevronLeftIcon } from "@/icons";
import {
  addWeeks,
  formatWeekRangeLabel,
  getMondayOfDate,
  getWeekDays,
  parseUtcToTimezone,
} from "@/utils/calendarTimezone";

interface CalendarMatrixViewProps {
  events: CalendarMatrixEvent[];
  selectedTimezone: "WIB" | "WITA" | "WIT";
  interviewers?: InterviewerContact[];
  selectedInterviewerId?: string;
  onSelectInterviewer?: (id: string) => void;
  currentWeekStart: Date;
  onChangeWeek: (newWeekStart: Date) => void;
  policy?: OperationalPolicy | null;
  isLoading?: boolean;
  isSyncing?: boolean;
  onRefresh?: () => void;
  lastSyncedAt?: Date | null;
  onSelectSlot?: (
    date: string,
    time: string,
    interviewer?: { id: string; name: string; role: string }
  ) => void;
}

export default function CalendarMatrixView({
  events,
  selectedTimezone,
  interviewers = [],
  selectedInterviewerId,
  onSelectInterviewer,
  currentWeekStart,
  onChangeWeek,
  policy,
  isLoading = false,
  isSyncing = false,
  onRefresh,
  lastSyncedAt,
  onSelectSlot,
}: CalendarMatrixViewProps) {
  const [internalInterviewerId, setInternalInterviewerId] = useState<string>("");
  const [selectedEvent, setSelectedEvent] = useState<CalendarMatrixEvent | null>(null);

  // Dynamic interviewer options derived purely from backend contacts & events
  const interviewerOptions = useMemo(() => {
    const list = interviewers.map((i) => ({
      id: i.id,
      name: i.name,
      role: i.role,
      dept: i.department,
      baseTz: i.timezone,
    }));

    // Append any interviewer ID present in events but absent from contacts
    const seenIds = new Set(list.map((i) => i.id));
    for (const ev of events) {
      if (ev.interviewer_id && !seenIds.has(ev.interviewer_id)) {
        list.push({
          id: ev.interviewer_id,
          name: `Interviewer #${ev.interviewer_id}`,
          role: "Calendar Owner",
          dept: "—",
          baseTz: selectedTimezone,
        });
        seenIds.add(ev.interviewer_id);
      }
    }

    return list;
  }, [interviewers, events, selectedTimezone]);

  const activeInterviewerId = selectedInterviewerId || internalInterviewerId;
  const currentInterviewer =
    interviewerOptions.find((i) => i.id === activeInterviewerId) ||
    interviewerOptions[0] ||
    null;

  const handleInterviewerChange = (id: string) => {
    setInternalInterviewerId(id);
    if (onSelectInterviewer) {
      onSelectInterviewer(id);
    }
  };

  // Dynamic 5-day week based on currentWeekStart
  const weekDays = useMemo(() => getWeekDays(currentWeekStart), [currentWeekStart]);
  const weekRangeLabel = useMemo(
    () => formatWeekRangeLabel(currentWeekStart),
    [currentWeekStart]
  );

  // Dynamic Operational Rules from backend policy
  const workStartHour = policy?.work_start_time
    ? parseInt(policy.work_start_time.slice(0, 2), 10)
    : 9;
  const workEndHour = policy?.work_end_time
    ? parseInt(policy.work_end_time.slice(0, 2), 10)
    : 17;

  // Grid hours from 08:00 to 17:00
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

  // Filter events belonging to selected interviewer
  const interviewerEvents = useMemo(() => {
    if (!currentInterviewer) return [];
    return events.filter((e) => e.interviewer_id === currentInterviewer.id);
  }, [events, currentInterviewer]);

  // Check if given hour is inside Friday prayer blackout (11:30 - 13:00)
  const isFridayPrayerHour = (isFriday: boolean, hour: string) => {
    if (!isFriday) return false;
    return hour === "11:00" || hour === "12:00";
  };

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
      {/* Top Controls: Interviewer Selector & Week Navigation & Live Sync Indicator */}
      <div className="flex flex-col gap-4 border-b border-gray-100 pb-4 dark:border-gray-800 lg:flex-row lg:items-center lg:justify-between">
        {/* Left: Dynamic Interviewer Filter */}
        <div className="flex flex-col gap-1.5 sm:flex-row sm:items-center sm:gap-3 w-full lg:w-auto min-w-0">
          <label className="text-xs font-bold text-gray-700 dark:text-gray-300 shrink-0">
            Pewawancara:
          </label>
          <select
            value={currentInterviewer?.id || ""}
            onChange={(e) => handleInterviewerChange(e.target.value)}
            disabled={interviewerOptions.length === 0}
            className="w-full sm:w-auto max-w-full sm:max-w-md truncate rounded-xl border border-gray-200 bg-white px-3 py-2 sm:py-1.5 text-xs font-bold text-brand-700 shadow-theme-xs focus:border-brand-500 focus:outline-hidden disabled:opacity-60 dark:border-gray-800 dark:bg-gray-800 dark:text-brand-300"
          >
            {interviewerOptions.length === 0 ? (
              <option value="">Memuat data pewawancara...</option>
            ) : (
              interviewerOptions.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.name} — {i.role} ({i.baseTz})
                </option>
              ))
            )}
          </select>
        </div>

        {/* Center: Dynamic Week Navigation */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onChangeWeek(addWeeks(currentWeekStart, -1))}
            title="Minggu Sebelumnya"
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-600 transition-colors hover:bg-gray-50 dark:border-gray-800 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            <ChevronLeftIcon className="h-4 w-4" />
          </button>

          <span className="min-w-[170px] text-center font-mono text-xs font-bold text-gray-900 dark:text-white">
            {weekRangeLabel}
          </span>

          <button
            type="button"
            onClick={() => onChangeWeek(addWeeks(currentWeekStart, 1))}
            title="Minggu Berikutnya"
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-600 transition-colors hover:bg-gray-50 dark:border-gray-800 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            <ChevronLeftIcon className="h-4 w-4 rotate-180" />
          </button>

          <button
            type="button"
            onClick={() => onChangeWeek(getMondayOfDate(new Date()))}
            className="ms-1 rounded-lg border border-brand-200 bg-brand-50/60 px-2.5 py-1 text-[11px] font-bold text-brand-700 transition-colors hover:bg-brand-100 dark:border-brand-800 dark:bg-brand-950/40 dark:text-brand-300"
          >
            Today
          </button>
        </div>

        {/* Right: Live Sync Status & Manual Refresh */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span
              className={`h-2 w-2 rounded-full ${
                isSyncing ? "bg-amber-500 animate-ping" : "bg-success-500"
              }`}
            />
            <span className="text-[11px] font-semibold text-gray-500 dark:text-gray-400">
              {isSyncing ? (
                "Sinkronisasi..."
              ) : (
                <>
                  Live Sync
                  {lastSyncedAt && (
                    <span className="ms-1 font-mono text-[10px] text-gray-400">
                      ({lastSyncedAt.toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit", second: "2-digit" })})
                    </span>
                  )}
                </>
              )}
            </span>
          </div>

          {onRefresh && (
            <button
              type="button"
              onClick={onRefresh}
              disabled={isSyncing}
              title="Perbarui Jadwal Kalender"
              className="flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-2.5 py-1 text-[11px] font-semibold text-gray-700 shadow-theme-xs transition-colors hover:bg-gray-50 disabled:opacity-50 dark:border-gray-800 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
            >
              <svg
                className={`h-3 w-3 ${isSyncing ? "animate-spin text-brand-500" : ""}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              <span>Refresh</span>
            </button>
          )}
        </div>
      </div>

      {/* Legend & Summary Bar */}
      <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-[11px]">
        <div className="flex flex-wrap items-center gap-3">
          <span className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
            <span className="h-2.5 w-2.5 rounded-full bg-brand-500" />
            Scheduled Interview 
          </span>
          <span className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
            <span className="h-2.5 w-2.5 rounded-full bg-purple-500" />
            Internal Meeting
          </span>
          <span className="flex items-center gap-1.5 font-bold text-warning-700 dark:text-warning-400">
            <span className="h-2.5 w-2.5 rounded-full bg-warning-500" />
            Friday Prayer Block (11:30 - 13:00)
          </span>
        </div>

        <span className="font-mono text-[10px] text-gray-400">
          Zona Waktu Aktif: <strong className="text-brand-600 dark:text-brand-400">{selectedTimezone}</strong>
        </span>
      </div>

      {/* Week Grid */}
      <div className="relative mt-4 overflow-x-auto">
        {/* Loading overlay */}
        {isLoading && (
          <div className="absolute inset-0 z-20 flex items-center justify-center bg-white/70 backdrop-blur-xs dark:bg-gray-900/70">
            <div className="flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-4 py-2 shadow-theme-sm dark:border-gray-800 dark:bg-gray-800">
              <span className="h-3 w-3 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
              <span className="text-xs font-semibold text-gray-700 dark:text-gray-300">
                Memuat data kalender real-time...
              </span>
            </div>
          </div>
        )}

        <div className="min-w-[700px]">
          {/* Header Row: Days */}
          <div className="grid grid-cols-6 border-b border-gray-200 pb-2 text-center text-xs font-bold text-gray-700 dark:border-gray-800 dark:text-gray-300">
            <div className="ps-2 text-start font-mono text-gray-400">
              Time ({selectedTimezone})
            </div>
            {weekDays.map((d) => (
              <div
                key={d.dateStr}
                className={`rounded-lg py-1 transition-colors ${
                  d.isToday
                    ? "border border-brand-300 bg-brand-50/70 font-extrabold text-brand-900 dark:border-brand-800 dark:bg-brand-950/40 dark:text-brand-200"
                    : d.isFriday
                    ? "bg-warning-50/60 font-extrabold text-warning-900 dark:bg-warning-500/10 dark:text-warning-200"
                    : ""
                }`}
              >
                <div className="flex items-center justify-center gap-1">
                  <span>{d.label}</span>
                  {d.isToday && (
                    <span className="rounded bg-brand-500 px-1 py-0.2 text-[8px] font-bold text-white uppercase">
                      Today
                    </span>
                  )}
                </div>
                <span className="block text-[11px] font-normal text-gray-400">
                  {d.dayNum}
                </span>
              </div>
            ))}
          </div>

          {/* Time Rows */}
          <div className="divide-y divide-gray-100 text-xs dark:divide-gray-800/60">
            {hours.map((hour) => {
              const hourNum = parseInt(hour.split(":")[0], 10);
              const isNonWorking = hourNum < workStartHour || hourNum >= workEndHour;

              return (
                <div
                  key={hour}
                  className={`grid min-h-[58px] grid-cols-6 items-stretch ${
                    isNonWorking
                      ? "bg-gray-50/70 text-gray-400 dark:bg-gray-800/30"
                      : ""
                  }`}
                >
                  {/* Time label */}
                  <div className="border-e border-gray-100 ps-2 py-2 font-mono text-[11px] text-gray-400 dark:border-gray-800">
                    {hour}
                  </div>

                  {/* 5 Day Cells */}
                  {weekDays.map((d) => {
                    const isFridayBlocked = isFridayPrayerHour(d.isFriday, hour);

                    // Accurate timezone-aware matching
                    const cellEvents = interviewerEvents.filter((e) => {
                      const tzParsed = parseUtcToTimezone(e.start, selectedTimezone);
                      return tzParsed.dateStr === d.dateStr && tzParsed.hour === hourNum;
                    });

                    return (
                      <div
                        key={d.dateStr}
                        onClick={() => {
                          if (
                            currentInterviewer &&
                            !isFridayBlocked &&
                            !isNonWorking &&
                            cellEvents.length === 0 &&
                            onSelectSlot
                          ) {
                            onSelectSlot(d.dateStr, hour, {
                              id: currentInterviewer.id,
                              name: currentInterviewer.name,
                              role: currentInterviewer.role,
                            });
                          }
                        }}
                        className={`group relative border-e border-gray-100 p-1 transition-all dark:border-gray-800 ${
                          isFridayBlocked
                            ? "cursor-not-allowed bg-warning-100/40 dark:bg-warning-900/20"
                            : isNonWorking
                            ? "cursor-not-allowed"
                            : cellEvents.length > 0
                            ? ""
                            : currentInterviewer
                            ? "cursor-pointer hover:bg-brand-50/40 dark:hover:bg-brand-500/10"
                            : "cursor-not-allowed"
                        }`}
                      >
                        {/* Friday Prayer Block Banner */}
                        {isFridayBlocked && hour === "11:00" && (
                          <div className="absolute inset-x-1 inset-y-1 z-10 flex flex-col justify-center rounded-lg border border-dashed border-warning-400 bg-warning-50 p-2 text-center text-[10px] font-bold text-warning-800 shadow-xs dark:border-warning-700 dark:bg-warning-950/60 dark:text-warning-300">
                            <span className="flex items-center justify-center gap-1">
                              <AlertIcon />
                              <span>BLOCKED</span>
                            </span>
                            <span className="mt-0.5 font-mono text-[9px]">
                              Salat Jumat (11:30–13:00)
                            </span>
                          </div>
                        )}

                        {/* Empty Slot Hover Hint */}
                        {!isFridayBlocked &&
                          !isNonWorking &&
                          cellEvents.length === 0 &&
                          currentInterviewer && (
                            <div className="hidden h-full items-center justify-center text-[10px] font-semibold text-brand-600 group-hover:flex dark:text-brand-400">
                              + Choose a Slot
                            </div>
                          )}

                        {/* Existing Events */}
                        {cellEvents.map((evt) => {
                          const isInterview = evt.event_type === "SCHEDULED_INTERVIEW";
                          const isMeeting = evt.event_type === "TEAM_MEETING";

                          if (evt.event_type === "FRIDAY_PRAYER_BLOCK") return null;

                          const startTz = parseUtcToTimezone(evt.start, selectedTimezone);
                          const endTz = parseUtcToTimezone(evt.end, selectedTimezone);

                          return (
                            <div
                              key={evt.id}
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedEvent(evt);
                              }}
                              className={`cursor-pointer rounded-lg p-1.5 text-[10px] leading-tight shadow-xs transition-transform hover:scale-[1.02] ${
                                isInterview
                                  ? "bg-brand-500 font-semibold text-white"
                                  : isMeeting
                                  ? "border border-purple-200 bg-purple-100 text-purple-900 dark:border-purple-800 dark:bg-purple-900/40 dark:text-purple-200"
                                  : "bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-300"
                              }`}
                            >
                              <div className="flex items-center gap-1 truncate">
                                {isInterview && <CheckCircleIcon />}
                                <span className="truncate">{evt.title}</span>
                              </div>
                              <span className="mt-0.5 block font-mono text-[9px] opacity-80">
                                {startTz.timeStr} - {endTz.timeStr}
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
                type="button"
                onClick={() => setSelectedEvent(null)}
                className="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              >
                Tutup
              </button>
            </div>
            <div className="mt-3 space-y-2.5 text-xs">
              <div>
                <span className="block text-[10px] text-gray-400">Judul Agenda:</span>
                <span className="font-bold text-gray-900 dark:text-white">
                  {selectedEvent.title}
                </span>
              </div>
              <div>
                <span className="block text-[10px] text-gray-400">Pewawancara:</span>
                <span className="text-gray-700 dark:text-gray-300">
                  {currentInterviewer
                    ? `${currentInterviewer.name} (${currentInterviewer.dept})`
                    : `Interviewer #${selectedEvent.interviewer_id}`}
                </span>
              </div>
              <div>
                <span className="block text-[10px] text-gray-400">
                  Waktu ({selectedTimezone}):
                </span>
                <span className="font-mono font-bold text-brand-600 dark:text-brand-400">
                  {parseUtcToTimezone(selectedEvent.start, selectedTimezone).displayDateTime}{" "}
                  s/d {parseUtcToTimezone(selectedEvent.end, selectedTimezone).timeStr}{" "}
                  {selectedTimezone}
                </span>
              </div>
              {selectedEvent.candidate_name && (
                <div>
                  <span className="block text-[10px] text-gray-400">Kandidat:</span>
                  <span className="font-semibold text-gray-800 dark:text-gray-200">
                    {selectedEvent.candidate_name}
                  </span>
                </div>
              )}
              {selectedEvent.rule_code && (
                <div>
                  <span className="block text-[10px] text-gray-400">Rule Code:</span>
                  <span className="rounded bg-gray-100 px-1.5 py-0.5 font-mono text-[10px] font-bold text-gray-700 dark:bg-gray-800 dark:text-gray-300">
                    {selectedEvent.rule_code}
                  </span>
                </div>
              )}
              {selectedEvent.description && (
                <div>
                  <span className="block text-[10px] text-gray-400">Deskripsi:</span>
                  <p className="leading-relaxed text-gray-600 dark:text-gray-400">
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
