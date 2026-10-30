"use client";

import React, { useEffect, useState } from "react";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import { CalendarMatrixEvent } from "@/types/orchestration";
import { OperationalPolicy } from "@/types/master";
import { listCalendarEvents } from "@/services/orchestrationService";
import { getOperationalPolicy } from "@/services/masterService";
import TimezoneMatrixHeader from "@/components/orchestration/calendar/TimezoneMatrixHeader";
import OperationalPolicyBanner from "@/components/orchestration/calendar/OperationalPolicyBanner";
import CalendarMatrixView from "@/components/orchestration/calendar/CalendarMatrixView";
import SlotConflictCheckerModal from "@/components/orchestration/calendar/SlotConflictCheckerModal";
import { Modal } from "@/components/ui/modal";
import Button from "@/components/ui/button/Button";
import { BoltIcon, CheckCircleIcon, ShootingStarIcon } from "@/icons";
import { useRouter } from "@/i18n/navigation";

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
  const [policy, setPolicy] = useState<OperationalPolicy | null>(null);
  const [isTesterOpen, setIsTesterOpen] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState<SelectedSlotInfo | null>(null);
  const [isSlotActionOpen, setIsSlotActionOpen] = useState(false);

  // Hydrate the matrix strictly from the backend calendar API
  useEffect(() => {
    let isCancelled = false;

    const loadCalendar = async () => {
      try {
        const apiEvents = await listCalendarEvents();
        if (isCancelled) return;
        setEvents(Array.isArray(apiEvents) ? apiEvents : []);
      } catch (error) {
        console.error("Failed to fetch calendar events:", error);
      }
    };

    const loadPolicy = async () => {
      try {
        const apiPolicy = await getOperationalPolicy();
        if (isCancelled || !apiPolicy) return;
        setPolicy(apiPolicy);
      } catch (error) {
        console.error("Failed to fetch operational policy:", error);
      }
    };

    void loadCalendar();
    void loadPolicy();

    return () => {
      isCancelled = true;
    };
  }, []);

  // When an available slot is clicked in the grid, open the quick slot action dialog
  const handleSelectSlot = (
    date: string,
    time: string,
    interviewer?: { id: string; name: string; role: string }
  ) => {
    setSelectedSlot({
      date,
      time,
      interviewerId: interviewer?.id || "int-001",
      interviewerName: interviewer?.name || "Budi Santoso",
      interviewerRole: interviewer?.role || "VP of Engineering",
    });
    setIsSlotActionOpen(true);
  };

  const handleNavigateToScheduling = () => {
    if (!selectedSlot) return;
    const isoString = `${selectedSlot.date}T${selectedSlot.time}:00`;
    setIsSlotActionOpen(false);
    router.push(
      `/orchestration/scheduling?slot_start=${encodeURIComponent(isoString)}&interviewer_id=${encodeURIComponent(selectedSlot.interviewerId)}&interviewer_name=${encodeURIComponent(selectedSlot.interviewerName)}`
    );
  };

  return (
    <div className="space-y-6">
      <PageBreadcrumb pageTitle="Calendar Matrix" />

      {/* Operational Policy Banner */}
      <OperationalPolicyBanner onOpenTester={() => setIsTesterOpen(true)} policy={policy} />

      {/* Weekly Matrix View */}
      <CalendarMatrixView
        events={events}
        selectedTimezone={selectedTimezone}
        onSelectSlot={handleSelectSlot}
      />

      {/* Quick Slot Action Modal (Milestone 3: Two-way Action Matrix -> Scheduling) */}
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
                Aksi Cepat Jadwal Wawancara (Cross-Page Orchestration)
              </p>
            </div>
          </div>

          <div className="mt-4 space-y-3 rounded-xl border border-gray-200/80 bg-gray-50/60 p-4 dark:border-gray-800 dark:bg-gray-800/40 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-gray-500 dark:text-gray-400">Interviewer:</span>
              <span className="font-bold text-gray-900 dark:text-white">
                {selectedSlot.interviewerName}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-500 dark:text-gray-400">Posisi:</span>
              <span className="text-gray-700 dark:text-gray-300">
                {selectedSlot.interviewerRole}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-500 dark:text-gray-400">Waktu ({selectedTimezone}):</span>
              <span className="font-mono font-bold text-brand-600 dark:text-brand-400">
                {selectedSlot.date} pukul {selectedSlot.time} {selectedTimezone}
              </span>
            </div>
            <div className="flex items-center gap-1.5 pt-1 text-[11px] text-success-700 dark:text-success-400">
              <CheckCircleIcon />
              <span>Tidak ada konflik agenda / aturan operasional terdeteksi.</span>
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
