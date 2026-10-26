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

export default function CalendarMatrixPage() {
  const [selectedTimezone, setSelectedTimezone] = useState<"WIB" | "WITA" | "WIT">("WIB");
  const [events, setEvents] = useState<CalendarMatrixEvent[]>([]);
  const [policy, setPolicy] = useState<OperationalPolicy | null>(null);
  const [isTesterOpen, setIsTesterOpen] = useState(false);

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

  // When an available slot is clicked in the grid, open the tester.
  const handleSelectSlot = () => {
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
      <OperationalPolicyBanner onOpenTester={() => setIsTesterOpen(true)} policy={policy} />

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
