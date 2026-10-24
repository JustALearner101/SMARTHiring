"use client";

import React, { useState } from "react";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import { initialCalendarMatrixEvents } from "@/data/mockThreadAndCalendarData";
import { CalendarMatrixEvent } from "@/types/orchestration";
import TimezoneMatrixHeader from "@/components/orchestration/calendar/TimezoneMatrixHeader";
import OperationalPolicyBanner from "@/components/orchestration/calendar/OperationalPolicyBanner";
import CalendarMatrixView from "@/components/orchestration/calendar/CalendarMatrixView";
import SlotConflictCheckerModal from "@/components/orchestration/calendar/SlotConflictCheckerModal";

export default function CalendarMatrixPage() {
  const [selectedTimezone, setSelectedTimezone] = useState<"WIB" | "WITA" | "WIT">("WIB");
  const [events, setEvents] = useState<CalendarMatrixEvent[]>(initialCalendarMatrixEvents);
  const [isTesterOpen, setIsTesterOpen] = useState(false);

  const handleSelectSlot = (date: string, time: string) => {
    // When an available slot is clicked in the grid, open the tester pre-filled
    setIsTesterOpen(true);
  };

  return (
    <div className="space-y-6">
      <PageBreadcrumb pageTitle="Calendar Matrix" />

      {/* Tri-Zone Synchronizer Header */}
      <TimezoneMatrixHeader
        selectedTimezone={selectedTimezone}
        onSelectTimezone={setSelectedTimezone}
      />

      {/* Operational Policy Banner */}
      <OperationalPolicyBanner onOpenTester={() => setIsTesterOpen(true)} />

      {/* Weekly Matrix View */}
      <CalendarMatrixView
        events={events}
        selectedTimezone={selectedTimezone}
        onSelectSlot={handleSelectSlot}
      />

      {/* Quick Conflict Checker Modal */}
      <SlotConflictCheckerModal
        isOpen={isTesterOpen}
        onClose={() => setIsTesterOpen(false)}
        events={events}
      />
    </div>
  );
}
