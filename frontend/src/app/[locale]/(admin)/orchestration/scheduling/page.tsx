"use client";

import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import AuditTimeline from "@/components/orchestration/AuditTimeline";
import CommandBar from "@/components/orchestration/CommandBar";
import ConfirmationCard from "@/components/orchestration/ConfirmationCard";
import DisambiguationModal from "@/components/orchestration/DisambiguationModal";
import UndoBufferBanner from "@/components/orchestration/UndoBufferBanner";
import Button from "@/components/ui/button/Button";
import { initialCandidates } from "@/data/mockMasterData";
import {
  budiDisambiguationProfiles,
  generateSampleActionPlan,
  initialAuditLogs,
} from "@/data/mockOrchestrationData";
import {
  BoltIcon,
  CheckCircleIcon,
  CloseIcon,
  InfoIcon,
  ShootingStarIcon,
} from "@/icons";
import { ActionPlan, AuditEvent, DisambiguationProfile, PlanStatus } from "@/types/orchestration";
import { useSearchParams } from "next/navigation";
import React, { Suspense, useMemo, useState } from "react";

function SchedulingContent() {
  const searchParams = useSearchParams();
  const candidateId = searchParams.get("candidateId");

  // Matched Candidate from URL Query if navigated from /master/candidates
  const targetCandidate = useMemo(() => {
    if (!candidateId) return initialCandidates[0];
    return initialCandidates.find((c) => c.id === candidateId) || initialCandidates[0];
  }, [candidateId]);

  // Orchestrator State
  const [status, setStatus] = useState<PlanStatus>("IDLE");
  const [isProcessing, setIsProcessing] = useState(false);
  const [activePlan, setActivePlan] = useState<ActionPlan | null>(null);
  const [isDisambiguationOpen, setIsDisambiguationOpen] = useState(false);
  const [auditLogs, setAuditLogs] = useState<AuditEvent[]>(initialAuditLogs);

  // Helper to add timestamped audit event
  const pushAudit = (
    eventType: AuditEvent["event_type"],
    title: string,
    description: string,
    actor: string,
    badge: AuditEvent["status_badge"]
  ) => {
    const now = new Date();
    const timeStr = `${String(now.getHours()).padStart(2, "0")}:${String(
      now.getMinutes()
    ).padStart(2, "0")}:${String(now.getSeconds()).padStart(2, "0")}`;

    const newEvent: AuditEvent = {
      id: `aud-${Date.now().toString().slice(-5)}`,
      timestamp: timeStr,
      event_type: eventType,
      title,
      description,
      actor,
      status_badge: badge,
    };

    setAuditLogs((prev) => [newEvent, ...prev]);
  };

  // 1. Execute Command (Natural Language or Quick Presets)
  const handleExecuteCommand = (prompt: string, scenarioId?: string) => {
    setIsProcessing(true);
    setStatus("ANALYZING");

    pushAudit(
      "REQUEST_RECEIVED",
      "Perintah Scheduling Diterima",
      `Prompt: "${prompt}"`,
      "HR Admin (You)",
      "info"
    );

    setTimeout(() => {
      pushAudit(
        "GUARDRAIL_PASSED",
        "Prompt Injection Scanner: Lolos",
        "Instruksi dan lampiran bebas dari kode injeksi liar.",
        "Guardrail Scanner Node",
        "success"
      );

      // Check for Disambiguation ("Dua Pak Budi" scenario)
      const isDisambiguation =
        scenarioId === "scenario-disambiguation" ||
        prompt.toLowerCase().includes("pak budi") ||
        prompt.toLowerCase().includes("budi");

      if (isDisambiguation) {
        setIsProcessing(false);
        setStatus("CLARIFICATION_NEEDED");
        setIsDisambiguationOpen(true);

        pushAudit(
          "DISAMBIGUATION_TRIGGERED",
          "Detected Contact Ambiguity",
          "There are 2 contacts named Budi (Budi Santoso & Budi Raharjo). Requesting human clarification.",
          "Planner & Triage Agent",
          "warning"
        );
      } else if (scenarioId === "scenario-friday-prayer") {
        // Friday prayer auto-block scenario
        const prayerPlan = generateSampleActionPlan(
          targetCandidate.name,
          targetCandidate.applied_position,
          budiDisambiguationProfiles[0],
          prompt,
          1
        );
        // Change slot to 14:00 WIB
        prayerPlan.proposed_slot.formatted_wib = "Friday, 30 October 2026 — 14:00 - 15:00 WIB";
        prayerPlan.proposed_slot.formatted_wita = "Friday, 30 October 2026 — 15:00 - 16:00 WITA";
        prayerPlan.validator_notes =
          "The initial 12:00 PM WIB schedule was automatically blocked because it coincided with Friday Prayer time (11:30 AM–1:00 PM WIB). The slot was moved to 2:00 PM WIB.";

        setActivePlan(prayerPlan);
        setIsProcessing(false);
        setStatus("PENDING_APPROVAL");

        pushAudit(
          "SOURCES_RETRIEVED",
          "Friday Prayer Time Blocked",
          "12:00 PM WIB slot moved to 2:00 PM WIB.",
          "Secondary Validator Agent",
          "success"
        );
      } else if (scenarioId === "scenario-triage-round-3") {
        // Round 3 scenario
        const round3Plan = generateSampleActionPlan(
          "Fajar Nugroho",
          "Backend Engineer (Golang)",
          budiDisambiguationProfiles[0],
          prompt,
          3
        );
        setActivePlan(round3Plan);
        setIsProcessing(false);
        setStatus("PENDING_APPROVAL");

        pushAudit(
          "PLAN_VALIDATED",
          "LIMITS: Final Negotiation Round (3/3)",
          "If the candidate rejects this round, the AI will automatically escalate manually to HR.",
          "Planner Agent",
          "warning"
        );
      } else {
        // Normal straight plan
        const plan = generateSampleActionPlan(
          targetCandidate.name,
          targetCandidate.applied_position,
          budiDisambiguationProfiles[0],
          prompt,
          1
        );
        setActivePlan(plan);
        setIsProcessing(false);
        setStatus("PENDING_APPROVAL");

        pushAudit(
          "PLAN_VALIDATED",
          "Action Plan Ready for Review",
          "Draft WhatsApp to Candidate and Email to User are ready for Approval Gate.",
          "Secondary Validator Agent",
          "success"
        );
      }
    }, 800);
  };

  // 2. Resolve Disambiguation (Human picks one Budi)
  const handleResolveDisambiguation = (chosenBudi: DisambiguationProfile) => {
    setIsDisambiguationOpen(false);

    pushAudit(
      "DISAMBIGUATION_RESOLVED",
      `Contact Ambiguity Resolved: ${chosenBudi.name}`,
      `HR confirmed ${chosenBudi.name} (${chosenBudi.role}, ${chosenBudi.department}).`,
      "HR Admin (You)",
      "success"
    );

    const plan = generateSampleActionPlan(
      targetCandidate.name,
      targetCandidate.applied_position,
      chosenBudi,
      `Schedule an interview with ${chosenBudi.name}`,
      1
    );

    setActivePlan(plan);
    setStatus("PENDING_APPROVAL");

    pushAudit(
      "SOURCES_RETRIEVED",
      "Sources & Calendar Slots Verified",
      `Checking [cal-${chosenBudi.employee_id.toLowerCase()}] & [cand-ats-${targetCandidate.name.split(" ")[0].toLowerCase()}].`,
      "Context Retriever Node",
      "info"
    );
  };

  // 3. Human Approval (Enters 60s Undo Window)
  const handleApprove = () => {
    setStatus("UNDO_WINDOW");
    pushAudit(
      "HUMAN_APPROVED",
      "Human-in-the-Loop Approval Granted",
      "HR approved the Action Plan. The 60-second grace period begins before external dispatch.",
      "HR Admin (You)",
      "success"
    );
  };

  // 4. Human Undo (< 60s)
  const handleUndo = () => {
    setStatus("UNDONE");
    if (activePlan) {
      setActivePlan({ ...activePlan, status: "UNDONE" });
    }
    pushAudit(
      "ACTION_UNDONE",
      "Action Plan Canceled (Undo)",
      "Disptach canceled during grace period. No emails or WhatsApp messages sent.",
      "HR Admin (You)",
      "error"
    );
  };

  // 5. Final Dispatch (Timer Expired or Send Immediately)
  const handleDispatchImmediately = () => {
    setStatus("EXECUTED");
    if (activePlan) {
      setActivePlan({ ...activePlan, status: "EXECUTED" });
    }
    pushAudit(
      "ACTION_DISPATCHED",
      "Email & WhatsApp Sent",
      "Email sent to Hiring Manager, WhatsApp sent to Candidate, and calendar booked in PostgreSQL.",
      "Channel & Calendar Executor",
      "success"
    );
  };

  // 6. Reject Plan
  const handleReject = () => {
    setStatus("REJECTED");
    pushAudit(
      "ACTION_UNDONE",
      "Action Plan Rejected by HR",
      "The plan was canceled from the approval gate.",
      "HR Admin (You)",
      "warning"
    );
  };

  // 7. Reset to Idle
  const handleReset = () => {
    setStatus("IDLE");
    setActivePlan(null);
  };

  return (
    <div>
      <PageBreadcrumb pageTitle="Autonomous Scheduling" />

      {/* Pillars of Accountability Compliance Banner */}
      <div className="mb-5 rounded-2xl border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-500 text-white shadow-theme-xs">
              <BoltIcon className="text-white" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-gray-900 dark:text-white">
                AI Orchestrator
              </h2>
              <p className="text-[11px] text-gray-500 dark:text-gray-400">
                Automation of post-screening scheduling in ATS with full human oversight.
              </p>
            </div>
          </div>

          {/* 5 Pillars Badges */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="rounded-md bg-blue-50 px-2 py-1 text-[10px] font-bold text-blue-700 dark:bg-blue-500/15 dark:text-blue-300">
              1. SOURCES Cited
            </span>
            <span className="rounded-md bg-emerald-50 px-2 py-1 text-[10px] font-bold text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300">
              2. PERMISSIONS (WIB/WITA/WIT)
            </span>
            <span className="rounded-md bg-brand-50 px-2 py-1 text-[10px] font-bold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
              3. APPROVAL Gate
            </span>
            <span className="rounded-md bg-amber-50 px-2 py-1 text-[10px] font-bold text-amber-700 dark:bg-amber-500/15 dark:text-amber-300">
              4. LIMITS (Disambiguasi)
            </span>
            <span className="rounded-md bg-purple-50 px-2 py-1 text-[10px] font-bold text-purple-700 dark:bg-purple-500/15 dark:text-purple-300">
              5. RECORD Audit
            </span>
          </div>
        </div>
      </div>

      {/* Natural Language Command Bar */}
      <CommandBar
        onExecuteCommand={handleExecuteCommand}
        isProcessing={isProcessing}
        activeCandidateName={targetCandidate?.name}
      />

      {/* 60-Second Undo Window Banner (Rendered when in UNDO_WINDOW) */}
      {status === "UNDO_WINDOW" && (
        <div className="mt-5">
          <UndoBufferBanner
            initialSeconds={60}
            onUndo={handleUndo}
            onDispatchImmediately={handleDispatchImmediately}
          />
        </div>
      )}

      {/* Main Orchestration Workspace */}
      <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-12">
        {/* Left Column: Confirmation Card / Execution Results */}
        <div className="lg:col-span-8 space-y-5">
          {/* Status: EXECUTED */}
          {status === "EXECUTED" && (
            <div className="rounded-2xl border-2 border-success-400 bg-success-50/50 p-6 dark:border-success-500/40 dark:bg-success-500/10 shadow-theme-xs">
              <div className="flex items-start gap-3.5">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-success-500 text-white shadow-theme-xs">
                  <CheckCircleIcon/>
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h3 className="text-base font-bold text-success-900 dark:text-success-300">
                      Action Plan Successfully Executed & Sent!
                    </h3>
                    <span className="rounded-full bg-success-100 px-2.5 py-0.5 text-[10px] font-mono font-bold text-success-800 dark:bg-success-500/20 dark:text-success-300">
                      DISPATCH_COMPLETE
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-success-800 dark:text-success-400 leading-relaxed">
                    All actions have been distributed to external servers:
                    <br />
                    • <strong>Email</strong> sent to {activePlan?.interviewer_name} ({activePlan?.items[0]?.recipient_contact})
                    <br />
                    • <strong>WhatsApp</strong> sent to {activePlan?.candidate_name} ({activePlan?.items[1]?.recipient_contact})
                    <br />
                    • <strong>Calendar Slot</strong> locked at {activePlan?.proposed_slot?.formatted_wib}
                  </p>
                  <div className="mt-4 flex items-center gap-2.5">
                    <Button variant="primary" size="sm" onClick={handleReset}>
                      Start New Orchestration
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Status: UNDONE */}
          {status === "UNDONE" && (
            <div className="rounded-2xl border-2 border-error-300 bg-error-50/50 p-6 dark:border-error-500/40 dark:bg-error-500/10 shadow-theme-xs">
              <div className="flex items-start gap-3.5">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-error-500 text-white shadow-theme-xs">
                  <CloseIcon/>
                </div>
                <div className="flex-1">
                  <h3 className="text-base font-bold text-error-900 dark:text-error-300">
                    Action Plan Canceled
                  </h3>
                  <p className="mt-1 text-xs text-error-700 dark:text-error-400 leading-relaxed">
                    The submission request was withdrawn before the 60-second grace period expired. No emails or WhatsApp messages were sent to the candidate or interviewer. The cancellation note is stored in the audit log.
                  </p>
                  <div className="mt-4">
                    <Button variant="outline" size="sm" onClick={handleReset}>
                      Back to Command Bar
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Status: REJECTED */}
          {status === "REJECTED" && (
            <div className="rounded-2xl border border-gray-200 bg-gray-50 p-6 dark:border-gray-800 dark:bg-gray-800/40 text-center">
              <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-2xl bg-error-50 text-error-500 dark:bg-error-500/10 mb-2">
                <CloseIcon />
              </div>
              <h3 className="mt-2 text-sm font-semibold text-gray-800 dark:text-white">
                Action Plan Rejected by HR
              </h3>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                This action plan will not be processed further.
              </p>
              <div className="mt-3">
                <Button variant="primary" size="sm" onClick={handleReset}>
                  Create New Action Plan
                </Button>
              </div>
            </div>
          )}

          {/* Status: PENDING_APPROVAL or UNDO_WINDOW -> Confirmation Card */}
          {(status === "PENDING_APPROVAL" || status === "UNDO_WINDOW") && activePlan && (
            <ConfirmationCard
              plan={activePlan}
              onApprove={handleApprove}
              onReject={handleReject}
              isApproving={status === "UNDO_WINDOW"}
            />
          )}

          {/* Status: IDLE -> Welcome Dashboard & Architecture Overview */}
          {status === "IDLE" && (
            <div className="rounded-2xl border border-gray-200 bg-white p-6 xl:p-8 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
              <div className="flex items-center gap-3 pb-4 border-b border-gray-100 dark:border-gray-800">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
                  <ShootingStarIcon/>
                </div>
                <div>
                  <h3 className="text-base font-bold text-gray-900 dark:text-white">
                    Waiting for Orchestration Command
                  </h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Selected Candidate: <strong>{targetCandidate.name}</strong> ({targetCandidate.applied_position})
                  </p>
                </div>
              </div>

              {/* How it works 4-step cards */}
              <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div className="rounded-xl border border-gray-100 bg-gray-50/80 p-3.5 dark:border-gray-800 dark:bg-gray-800/40">
                  <div className="flex items-center gap-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-500 text-[11px] font-bold text-white">
                      1
                    </span>
                    <h4 className="text-xs font-bold text-gray-800 dark:text-white">
                      Scan Guardrail & Injection
                    </h4>
                  </div>
                  <p className="mt-1.5 text-[11px] text-gray-500 dark:text-gray-400 leading-relaxed">
                    Every instruction and CV document is scanned to detect malicious manipulation instructions (*prompt injection*).
                  </p>
                </div>

                <div className="rounded-xl border border-gray-100 bg-gray-50/80 p-3.5 dark:border-gray-800 dark:bg-gray-800/40">
                  <div className="flex items-center gap-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-500 text-[11px] font-bold text-white">
                      2
                    </span>
                    <h4 className="text-xs font-bold text-gray-800 dark:text-white">
                      Retrieve Slot & Rules
                    </h4>
                  </div>
                  <p className="mt-1.5 text-[11px] text-gray-500 dark:text-gray-400 leading-relaxed">
                    Matching empty calendar slots, WIB/WITA time zones, and blocking Friday prayer times.
                  </p>
                </div>

                <div className="rounded-xl border border-gray-100 bg-gray-50/80 p-3.5 dark:border-gray-800 dark:bg-gray-800/40">
                  <div className="flex items-center gap-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-500 text-[11px] font-bold text-white">
                      3
                    </span>
                    <h4 className="text-xs font-bold text-gray-800 dark:text-white">
                      Human Approval Gate
                    </h4>
                  </div>
                  <p className="mt-1.5 text-[11px] text-gray-500 dark:text-gray-400 leading-relaxed">
                    AI must stop displaying the complete draft message with source citations.
                  </p>
                </div>

                <div className="rounded-xl border border-gray-100 bg-gray-50/80 p-3.5 dark:border-gray-800 dark:bg-gray-800/40">
                  <div className="flex items-center gap-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-500 text-[11px] font-bold text-white">
                      4
                    </span>
                    <h4 className="text-xs font-bold text-gray-800 dark:text-white">
                      60-Second Undo Window
                    </h4>
                  </div>
                  <p className="mt-1.5 text-[11px] text-gray-500 dark:text-gray-400 leading-relaxed">
                    Providing a 60-second window for HR to cancel the shipment before the external gateway execution.
                  </p>
                </div>
              </div>

              {/* Fast Start Action Banner */}
              <div className="mt-6 flex flex-col sm:flex-row sm:items-center sm:justify-between rounded-xl bg-brand-500/10 p-4 border border-brand-500/20 text-xs text-brand-900 dark:text-brand-300">
                <div className="flex items-center gap-2">
                  <InfoIcon className="text-brand-600 shrink-0" />
                  <span>
                    Ready to try the scenario? Click the <strong>AI Orchestration</strong> button above or select one of the <strong>Quick Test Scenarios</strong>.
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Live Immutable Audit Trail */}
        <div className="lg:col-span-4">
          <div className="sticky top-20">
            <AuditTimeline logs={auditLogs} />
          </div>
        </div>
      </div>

      {/* Disambiguation Modal*/}
      <DisambiguationModal
        isOpen={isDisambiguationOpen}
        onClose={() => {
          setIsDisambiguationOpen(false);
          setStatus("IDLE");
        }}
        onSelectInterviewer={handleResolveDisambiguation}
        candidateName={targetCandidate.name}
        targetPosition={targetCandidate.applied_position}
      />
    </div>
  );
}

export default function AutonomousSchedulingPage() {
  return (
    <Suspense
      fallback={
        <div className="p-8 text-center text-xs text-gray-400">
          Loading AI Orchestrator...
        </div>
      }
    >
      <SchedulingContent />
    </Suspense>
  );
}
