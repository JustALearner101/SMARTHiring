"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import { CalendarMatrixEvent } from "@/types/orchestration";
import { InterviewerContact, OperationalPolicy } from "@/types/master";
import { listCalendarEvents } from "@/services/orchestrationService";
import { getOperationalPolicy, listContacts } from "@/services/masterService";
import TimezoneMatrixHeader from "@/components/orchestration/calendar/TimezoneMatrixHeader";
import OperationalPolicyBanner from "@/components/orchestration/calendar/OperationalPolicyBanner";
import CalendarMatrixView from "@/components/orchestration/calendar/CalendarMatrixView";
import SlotConflictCheckerModal from "@/components/orchestration/calendar/SlotConflictCheckerModal";
import { Modal } from "@/components/ui/modal";
import Button from "@/components/ui/button/Button";
import { BoltIcon, CheckCircleIcon, ShootingStarIcon } from "@/icons";
import { useRouter } from "@/i18n/navigation";
import { getMondayOfDate } from "@/utils/calendarTimezone";

interface SelectedSlotInfo {
  date: string;
  time: string;
  interviewerId: string;
  interviewerName: string;
  interviewerRole: string;
}

export default function CalendarMatrixPage() {
  const router = useRouter();
  const [selectedTimezone, setSelectedTimezone] = useState<"WIB" | "WITA" | "WIT">("WIB");
  const [events, setEvents] = useState<CalendarMatrixEvent[]>([]);
  const [interviewers, setInterviewers] = useState<InterviewerContact[]>([]);
  const [selectedInterviewerId, setSelectedInterviewerId] = useState<string>("");
  const [currentWeekStart, setCurrentWeekStart] = useState<Date>(() =>
    getMondayOfDate(new Date())
  );
  const [policy, setPolicy] = useState<OperationalPolicy | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [lastSyncedAt, setLastSyncedAt] = useState<Date | null>(null);

  const [isTesterOpen, setIsTesterOpen] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState<SelectedSlotInfo | null>(null);
  const [isSlotActionOpen, setIsSlotActionOpen] = useState(false);

  // Keep a ref to avoid stale closure in polling intervals
  const isFetchingRef = useRef(false);

  // Fetch calendar events
  const loadCalendar = useCallback(async (isBackground = false) => {
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;

    if (isBackground) {
      setIsSyncing(true);
    } else {
      setIsLoading(true);
    }

    try {
      const apiEvents = await listCalendarEvents();
      setEvents(Array.isArray(apiEvents) ? apiEvents : []);
      setLastSyncedAt(new Date());
    } catch (error) {
      console.error("Failed to fetch calendar events:", error);
    } finally {
      setIsLoading(false);
      setIsSyncing(false);
      isFetchingRef.current = false;
    }
  }, []);

  // Fetch master contacts and operational policy once on mount
  useEffect(() => {
    let isCancelled = false;

    const loadMasterData = async () => {
      try {
        const [contactsData, policyData] = await Promise.allSettled([
          listContacts(),
          getOperationalPolicy(),
        ]);

        if (isCancelled) return;

        if (contactsData.status === "fulfilled" && Array.isArray(contactsData.value)) {
          setInterviewers(contactsData.value);
          if (contactsData.value.length > 0) {
            setSelectedInterviewerId(contactsData.value[0].id);
          }
        }

        if (policyData.status === "fulfilled" && policyData.value) {
          setPolicy(policyData.value);
        }
      } catch (error) {
        console.error("Failed to load master metadata:", error);
      }
    };

    void loadMasterData();
    void loadCalendar(false);

    return () => {
      isCancelled = true;
    };
  }, [loadCalendar]);

  // Real-time synchronization: Smart Polling every 15s + Window Focus revalidation
  useEffect(() => {
    const POLL_INTERVAL_MS = 15000;

    const intervalId = setInterval(() => {
      if (typeof document !== "undefined" && document.visibilityState === "visible") {
        void loadCalendar(true);
      }
    }, POLL_INTERVAL_MS);

    const handleVisibilityOrFocus = () => {
      if (typeof document !== "undefined" && document.visibilityState === "visible") {
        void loadCalendar(true);
      }
    };

    window.addEventListener("focus", handleVisibilityOrFocus);
    document.addEventListener("visibilitychange", handleVisibilityOrFocus);

    return () => {
      clearInterval(intervalId);
      window.removeEventListener("focus", handleVisibilityOrFocus);
      document.removeEventListener("visibilitychange", handleVisibilityOrFocus);
    };
  }, [loadCalendar]);

  // When an available slot is clicked in the grid, open the quick slot action dialog
  const handleSelectSlot = (
    date: string,
    time: string,
    interviewer?: { id: string; name: string; role: string }
  ) => {
    const matched = interviewers.find(
      (i) => i.id === (interviewer?.id || selectedInterviewerId)
    );
    setSelectedSlot({
      date,
      time,
      interviewerId: interviewer?.id || matched?.id || selectedInterviewerId || "",
      interviewerName: interviewer?.name || matched?.name || "Pewawancara",
      interviewerRole: interviewer?.role || matched?.role || "Interviewer",
    });
    setIsSlotActionOpen(true);
  };

  const handleNavigateToScheduling = () => {
    if (!selectedSlot) return;
    const isoString = `${selectedSlot.date}T${selectedSlot.time}:00`;
    setIsSlotActionOpen(false);
    router.push(
      `/orchestration/scheduling?slot_start=${encodeURIComponent(
        isoString
      )}&interviewer_id=${encodeURIComponent(
        selectedSlot.interviewerId
      )}&interviewer_name=${encodeURIComponent(selectedSlot.interviewerName)}`
    );
  };

  return (
    <div className="space-y-6">
      <PageBreadcrumb pageTitle="Calendar Matrix" />
      {/* Dynamic & Real-time Weekly Matrix View */}
      <CalendarMatrixView
        events={events}
        selectedTimezone={selectedTimezone}
        interviewers={interviewers}
        selectedInterviewerId={selectedInterviewerId}
        onSelectInterviewer={setSelectedInterviewerId}
        currentWeekStart={currentWeekStart}
        onChangeWeek={setCurrentWeekStart}
        policy={policy}
        isLoading={isLoading}
        isSyncing={isSyncing}
        onRefresh={() => void loadCalendar(true)}
        lastSyncedAt={lastSyncedAt}
        onSelectSlot={handleSelectSlot}
      />

      {/* Quick Slot Action Modal (Cross-Page Orchestration) */}
      {selectedSlot && (
        <Modal
          isOpen={isSlotActionOpen}
          onClose={() => setIsSlotActionOpen(false)}
          className="max-w-md p-6"
        >
          <div className="flex items-center gap-3 border-b border-gray-100 pb-3 dark:border-gray-800">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-500 text-white shadow-theme-xs">
              <BoltIcon />
            </div>
            <div>
              <h3 className="text-sm font-bold text-gray-900 dark:text-white">
                Slot Kalender Tersedia
              </h3>
              <p className="text-[11px] text-gray-500 dark:text-gray-400">
                Quick Interview Actions (Cross-Page Orchestration)
              </p>
            </div>
          </div>

          <div className="mt-4 space-y-3 rounded-xl border border-gray-200/80 bg-gray-50/60 p-4 text-xs dark:border-gray-800 dark:bg-gray-800/40">
            <div className="flex items-center justify-between">
              <span className="text-gray-500 dark:text-gray-400">Pewawancara:</span>
              <span className="font-bold text-gray-900 dark:text-white">
                {selectedSlot.interviewerName}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-500 dark:text-gray-400">Posisi:</span>
              <span className="text-gray-700 dark:text-gray-300">
                {selectedSlot.interviewerRole}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-500 dark:text-gray-400">
                Waktu ({selectedTimezone}):
              </span>
              <span className="font-mono font-bold text-brand-600 dark:text-brand-400">
                {selectedSlot.date} pukul {selectedSlot.time} {selectedTimezone}
              </span>
            </div>
            <div className="flex items-center gap-1.5 pt-1 text-[11px] text-success-700 dark:text-success-400">
              <CheckCircleIcon />
              <span>Tidak ada konflik jadwal atau pelanggaran aturan operasional.</span>
            </div>
          </div>

          <div className="mt-5 flex flex-col gap-2.5">
            <Button
              variant="primary"
              size="sm"
              onClick={handleNavigateToScheduling}
              startIcon={<ShootingStarIcon className="text-white" />}
              className="w-full justify-center"
            >
              Jadwalkan via Orchestrator
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setIsSlotActionOpen(false);
                setIsTesterOpen(true);
              }}
              className="w-full justify-center"
            >
              Uji Aturan Operasional (Conflict Checker)
            </Button>
          </div>
        </Modal>
      )}

      {/* Quick Conflict Checker Modal */}
      <SlotConflictCheckerModal
        isOpen={isTesterOpen}
        onClose={() => setIsTesterOpen(false)}
        events={events}
      />
    </div>
  );
}
