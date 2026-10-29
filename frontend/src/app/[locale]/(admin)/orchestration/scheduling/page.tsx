"use client";

import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import AuditTimeline from "@/components/orchestration/AuditTimeline";
import CommandBar from "@/components/orchestration/CommandBar";
import ConfirmationCard from "@/components/orchestration/ConfirmationCard";
import DisambiguationModal from "@/components/orchestration/DisambiguationModal";
import UndoBufferBanner from "@/components/orchestration/UndoBufferBanner";
import Button from "@/components/ui/button/Button";
import {
  BoltIcon,
  ChatIcon,
  CheckCircleIcon,
  CloseIcon,
  EnvelopeIcon,
  InfoIcon,
  ShootingStarIcon,
  CalenderIcon,
} from "@/icons";
import { Link } from "@/i18n/navigation";
import { listAuditLogs } from "@/services/auditService";
import { getCandidate, listCandidates } from "@/services/masterService";
import {
  approveActionPlan,
  executeCommand,
  getCurrentActionPlan,
  isDisambiguationResult,
  listPresetScenarios,
  undoActionPlan,
} from "@/services/orchestrationService";
import { Candidate } from "@/types/master";
import {
  ActionPlan,
  AuditEvent,
  DisambiguationProfile,
  PlanStatus,
  PresetScenario,
} from "@/types/orchestration";
import { useSearchParams } from "next/navigation";
import React, { Suspense, useEffect, useMemo, useRef, useState } from "react";

function formatAuditTimestamp(raw: string): string {
  if (!raw.includes("T")) return raw;
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return raw;
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${pad(parsed.getHours())}:${pad(parsed.getMinutes())}:${pad(parsed.getSeconds())}`;
}

function toAuditEvent(event: AuditEvent): AuditEvent {
  return {
    id: event.id,
    timestamp: formatAuditTimestamp(event.timestamp),
    event_type: event.event_type,
    title: event.title,
    description: event.description,
    actor: event.actor,
    status_badge: event.status_badge,
    metadata: event.metadata,
  };
}

function mapPlanStatus(planStatus: PlanStatus): PlanStatus {
  switch (planStatus) {
    case "PENDING_APPROVAL":
    case "UNDO_WINDOW":
    case "EXECUTED":
    case "UNDONE":
      return planStatus;
    default:
      return "IDLE";
  }
}

function SchedulingContent() {
  const searchParams = useSearchParams();
  const candidateId = searchParams.get("candidateId") || searchParams.get("candidate_id");
  const slotStart = searchParams.get("slot_start");
  const interviewerName = searchParams.get("interviewer_name");
  const threadId = searchParams.get("thread_id");

  const [candidatesQueue, setCandidatesQueue] = useState<Candidate[]>([]);
  const [apiCandidate, setApiCandidate] = useState<Candidate | null>(null);
  const targetCandidate: Candidate | null =
    apiCandidate && candidateId && apiCandidate.id === candidateId
      ? apiCandidate
      : candidatesQueue.find((c) => c.id === candidateId) ?? candidatesQueue[0] ?? null;

  const initialCommandFromParams = useMemo(() => {
    const candName = targetCandidate?.name || "Rina Kusuma";
    const interName = interviewerName || "Budi Santoso";

    if (threadId) {
      return `Triage dan jadwalkan ulang technical interview untuk ${candName} bersama ${interName} (Thread #${threadId})`;
    }

    if (slotStart) {
      const dt = new Date(slotStart);
      if (!Number.isNaN(dt.getTime())) {
        const options: Intl.DateTimeFormatOptions = {
          weekday: "long",
          day: "numeric",
          month: "short",
          year: "numeric",
          hour: "2-digit",
          minute: "2-digit",
          timeZone: "Asia/Jakarta",
        };
        const formatted = new Intl.DateTimeFormat("id-ID", options).format(dt);
        return `Jadwalkan technical interview untuk ${candName} bersama ${interName} pada ${formatted} WIB`;
      }
      return `Jadwalkan technical interview untuk ${candName} bersama ${interName} pada ${slotStart}`;
    }

    return "";
  }, [slotStart, threadId, interviewerName, targetCandidate]);

  const [lastExecutedCommand, setLastExecutedCommand] = useState<string>("");

  const modalCandidate = useMemo(() => {
    const prompt = (lastExecutedCommand || "").toLowerCase();
    if (prompt && candidatesQueue.length > 0) {
      for (const cand of candidatesQueue) {
        if (prompt.includes(cand.name.toLowerCase())) {
          return cand;
        }
        const tokens = cand.name.toLowerCase().split(/\s+/).filter((t) => t.length >= 3);
        if (tokens.some((t) => prompt.includes(t))) {
          return cand;
        }
      }
    }
    return targetCandidate;
  }, [candidatesQueue, targetCandidate, lastExecutedCommand]);

  // Orchestrator State
  const [status, setStatus] = useState<PlanStatus>("IDLE");
  const [isProcessing, setIsProcessing] = useState(false);
  const [isApprovingPlan, setIsApprovingPlan] = useState(false);
  const [activePlan, setActivePlan] = useState<ActionPlan | null>(null);
  const [isDisambiguationOpen, setIsDisambiguationOpen] = useState(false);
  const [disambiguationProfiles, setDisambiguationProfiles] = useState<DisambiguationProfile[]>([]);
  const [undoSeconds, setUndoSeconds] = useState(60);
  const [scenarioList, setScenarioList] = useState<PresetScenario[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditEvent[]>([]);

  // Prevents the 60s countdown and the "Send Now" button from double-dispatching.
  const finalizedRef = useRef(false);

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
      id: `aud-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      timestamp: timeStr,
      event_type: eventType,
      title,
      description,
      actor,
      status_badge: badge,
    };

    setAuditLogs((prev) => [newEvent, ...prev]);
  };

  // Initial hydration strictly from Backend API
  useEffect(() => {
    let cancelled = false;

    const hydrate = async () => {
      try {
        const candidatesPage = await listCandidates({ page_size: 20 });
        if (!cancelled && Array.isArray(candidatesPage?.items)) {
          setCandidatesQueue(candidatesPage.items);
        }
      } catch (error) {
        console.error("Failed to fetch candidates queue:", error);
      }

      try {
        const scenarios = await listPresetScenarios();
        if (!cancelled && Array.isArray(scenarios)) setScenarioList(scenarios);
      } catch (error) {
        console.error("Failed to fetch preset scenarios:", error);
      }

      try {
        const page = await listAuditLogs({ page_size: 50 });
        if (!cancelled && Array.isArray(page?.items)) {
          setAuditLogs(page.items.map(toAuditEvent));
        }
      } catch (error) {
        console.error("Failed to fetch audit logs:", error);
      }

      try {
        const plan = await getCurrentActionPlan();
        if (!cancelled && plan) {
          setActivePlan(plan);
          const mappedStatus = mapPlanStatus(plan.status);
          if (mappedStatus === "UNDO_WINDOW") {
            const expiresAt = plan.undo_expires_at;
            if (typeof expiresAt === "number" && expiresAt > Date.now()) {
              setUndoSeconds(Math.max(1, Math.ceil((expiresAt - Date.now()) / 1000)));
              setStatus("UNDO_WINDOW");
            } else {
              setStatus("EXECUTED");
            }
          } else {
            setStatus(mappedStatus);
          }
        }
      } catch (error) {
        console.error("Failed to fetch current action plan:", error);
      }
    };

    void hydrate();

    return () => {
      cancelled = true;
    };
  }, []);

  // Candidate context from ?candidateId=...
  useEffect(() => {
    if (!candidateId) return;

    let cancelled = false;
    getCandidate(candidateId)
      .then((candidate) => {
        if (!cancelled) setApiCandidate(candidate);
      })
      .catch((error: unknown) => {
        console.error("Failed to fetch candidate by ID:", error);
      });

    return () => {
      cancelled = true;
    };
  }, [candidateId]);

  const applyPlan = (plan: ActionPlan) => {
    setActivePlan(plan);
    setStatus("PENDING_APPROVAL");
    setIsProcessing(false);
    setIsApprovingPlan(false);
    finalizedRef.current = false;

    const sourceRefs = plan.sources_cited.map((src) => src.ref_code).join(" · ");
    pushAudit(
      "SOURCES_RETRIEVED",
      "Sources & Calendar Slots Verified",
      sourceRefs || `Calendar slots and candidate records verified for ${plan.candidate_name}.`,
      "Context Retriever Node",
      "info"
    );

    pushAudit(
      "PLAN_VALIDATED",
      "Action Plan Ready for Review",
      plan.validator_notes ||
        "Draft WhatsApp to Candidate and Email to User are ready for Approval Gate.",
      "Secondary Validator Agent",
      "success"
    );
  };

  // 1. Execute Command (Natural Language or Quick Presets) strictly via Backend API
  const handleExecuteCommand = async (prompt: string, scenarioId?: string) => {
    if (isProcessing) return;

    setLastExecutedCommand(prompt);
    setIsProcessing(true);
    setStatus("ANALYZING");
    finalizedRef.current = false;

    pushAudit(
      "REQUEST_RECEIVED",
      "Perintah Scheduling Diterima",
      `Prompt: "${prompt}"`,
      "HR Admin (You)",
      "info"
    );

    try {
      const result = await executeCommand({
        command: prompt,
        scenario_id: scenarioId ?? null,
      });

      if (isDisambiguationResult(result)) {
        setDisambiguationProfiles(result.profiles);
        setIsProcessing(false);
        setStatus("CLARIFICATION_NEEDED");
        setIsDisambiguationOpen(true);

        pushAudit(
          "DISAMBIGUATION_TRIGGERED",
          "Detected Contact Ambiguity",
          result.message ||
            "Multiple contacts matched the query. Requesting human clarification.",
          "Planner & Triage Agent",
          "warning"
        );
        return;
      }

      applyPlan(result);
    } catch (error) {
      console.error("Failed to execute scheduling command:", error);
      setIsProcessing(false);
      setStatus("IDLE");
    }
  };

  // 2. Resolve Disambiguation (Human picks one Budi) strictly via Backend API
  const handleResolveDisambiguation = async (chosenBudi: DisambiguationProfile) => {
    setIsDisambiguationOpen(false);

    pushAudit(
      "DISAMBIGUATION_RESOLVED",
      `Contact Ambiguity Resolved: ${chosenBudi.name}`,
      `HR confirmed ${chosenBudi.name} (${chosenBudi.role}, ${chosenBudi.department}).`,
      "HR Admin (You)",
      "success"
    );

    setIsProcessing(true);
    setStatus("ANALYZING");
    finalizedRef.current = false;

    const originalPrompt = lastExecutedCommand || "";
    let followUpCommand = "";

    if (originalPrompt && /budi/i.test(originalPrompt)) {
      followUpCommand = originalPrompt.replace(
        /(?:mr\.?\s+|pak\s+)?budi(?:\s+santoso|\s+hartono)?/gi,
        `${chosenBudi.name} (${chosenBudi.department}, ${chosenBudi.timezone})`
      );
    } else {
      const candidateName = modalCandidate?.name ?? "Rina Kusuma";
      followUpCommand = `Schedule an interview for ${candidateName} with ${chosenBudi.name} (${chosenBudi.department}, ${chosenBudi.timezone})`;
    }

    try {
      const result = await executeCommand({ command: followUpCommand, scenario_id: null });

      if (isDisambiguationResult(result)) {
        setDisambiguationProfiles(result.profiles);
        setIsProcessing(false);
        setStatus("CLARIFICATION_NEEDED");
        setIsDisambiguationOpen(true);
        return;
      }

      applyPlan(result);
    } catch (error) {
      console.error("Failed to resolve disambiguation command:", error);
      setIsProcessing(false);
      setStatus("IDLE");
    }
  };

  // 3. Human Approval (Enters 60s Undo Window)
  const handleApprove = async (customizedPlan?: ActionPlan) => {
    const planToApprove = customizedPlan || activePlan;
    if (!planToApprove || isApprovingPlan) return;

    setIsApprovingPlan(true);

    const candRoleItem = planToApprove.items?.find((i) => i.recipient_role.toLowerCase().includes("candidate"));
    const interRoleItem = planToApprove.items?.find(
      (i) => !i.recipient_role.toLowerCase().includes("candidate") && i.channel !== "calendar"
    );
    const candCh = candRoleItem?.channel?.toUpperCase() || "EMAIL";
    const interCh = interRoleItem?.channel?.toUpperCase() || "EMAIL";

    pushAudit(
      "HUMAN_APPROVED",
      "Human-in-the-Loop Approval Granted",
      `HR approved the Action Plan (Candidate: ${candCh}, Interviewer: ${interCh}). The 60-second grace period begins before external dispatch.`,
      "HR Admin (You)",
      "success"
    );

    try {
      const approvedPlan = await approveActionPlan(planToApprove.id, {
        approved_by: "HR Admin (You)",
        send_immediately: false,
        customized_items: planToApprove.items,
      });

      finalizedRef.current = false;
      setActivePlan(approvedPlan);
      const expiresAt =
        typeof approvedPlan.undo_expires_at === "number"
          ? approvedPlan.undo_expires_at
          : Date.now() + 60000;
      setUndoSeconds(Math.max(1, Math.ceil((expiresAt - Date.now()) / 1000)));
      setIsApprovingPlan(false);
      setStatus("UNDO_WINDOW");

      pushAudit(
        "UNDO_BUFFER_STARTED",
        "60-Second Undo Buffer Started",
        "Dispatch is held for 60 seconds. HR can still cancel before the external gateway executes.",
        "Approval Gate Node",
        "warning"
      );
    } catch (error) {
      console.error("Failed to approve action plan:", error);
      setIsApprovingPlan(false);
    }
  };

  // 4. Human Undo (< 60s)
  const handleUndo = async () => {
    finalizedRef.current = true;
    const plan = activePlan;
    if (!plan) return;

    try {
      const undonePlan = await undoActionPlan(
        plan.id,
        "Manual cancellation by HR within 60s window"
      );
      setActivePlan(undonePlan);
      setStatus("UNDONE");

      pushAudit(
        "ACTION_UNDONE",
        "Action Plan Canceled (Undo)",
        "Dispatch canceled during grace period. No emails or WhatsApp messages sent.",
        "HR Admin (You)",
        "error"
      );
    } catch (error) {
      console.error("Failed to undo action plan:", error);
    }
  };

  // 5. Final Dispatch (Timer Expired or Send Immediately)
  const handleDispatchImmediately = async () => {
    if (finalizedRef.current) return;
    finalizedRef.current = true;

    const plan = activePlan;
    if (!plan) return;

    try {
      const executedPlan = await approveActionPlan(plan.id, {
        approved_by: "HR Admin (You)",
        send_immediately: true,
        customized_items: plan.items,
      });
      setActivePlan(executedPlan);
      setStatus("EXECUTED");

      const candItem = plan.items?.find((i) => i.recipient_role.toLowerCase().includes("candidate"));
      const interItem = plan.items?.find(
        (i) => !i.recipient_role.toLowerCase().includes("candidate") && i.channel !== "calendar"
      );
      const candCh = candItem?.channel?.toLowerCase() === "whatsapp" ? "WhatsApp" : "Email";
      const interCh = interItem?.channel?.toLowerCase() === "whatsapp" ? "WhatsApp" : "Email";

      pushAudit(
        "ACTION_DISPATCHED",
        `${interCh} & ${candCh} Sent`,
        `${interCh} sent to Hiring Manager, ${candCh} sent to Candidate, and calendar booked in PostgreSQL.`,
        "Channel & Calendar Executor",
        "success"
      );
    } catch (error) {
      console.error("Failed to dispatch action plan:", error);
    }
  };

  // 6. Reject Plan (Client-side state — no /reject endpoint on backend, Ledger U-08)
  const handleReject = () => {
    finalizedRef.current = true;
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
    finalizedRef.current = false;
    setStatus("IDLE");
    setActivePlan(null);
    setIsApprovingPlan(false);
  };

  return (
    <div>
      <PageBreadcrumb pageTitle="Autonomous Scheduling" />

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

      {/* Cross-Page Context Banner (Milestone 3 Integration) */}
      {threadId && (
        <div className="mb-4 rounded-xl border border-warning-200 bg-warning-50 p-3.5 dark:border-warning-800/60 dark:bg-warning-500/10">
          <div className="flex items-center gap-2.5">
            <div className="text-warning-600 dark:text-warning-400">
              <BoltIcon className="h-4 w-4" />
            </div>
            <div className="text-xs">
              <span className="font-bold text-warning-900 dark:text-warning-200">
                Konteks Triage Thread #{threadId} Aktif:
              </span>{" "}
              <span className="text-warning-800 dark:text-warning-300">
                Menangani eskalasi negosiasi untuk {targetCandidate?.name || "kandidat"}. Command telah disiapkan di bawah untuk menjadwalkan ulang.
              </span>
            </div>
          </div>
        </div>
      )}

      {slotStart && !threadId && (
        <div className="mb-4 rounded-xl border border-brand-200 bg-brand-50 p-3.5 dark:border-brand-800/60 dark:bg-brand-500/10">
          <div className="flex items-center gap-2.5">
            <div className="text-brand-600 dark:text-brand-400">
              <BoltIcon className="h-4 w-4" />
            </div>
            <div className="text-xs">
              <span className="font-bold text-brand-900 dark:text-brand-200">
                Konteks Slot Calendar Matrix Aktif:
              </span>{" "}
              <span className="text-brand-800 dark:text-brand-300">
                Slot waktu telah dipilih dari Calendar Matrix. Klik &quot;AI Orchestration&quot; untuk memvalidasi dan memproses proposal jadwal.
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Natural Language Command Bar */}
      <CommandBar
        key={`${targetCandidate?.id ?? "default"}-${initialCommandFromParams}`}
        onExecuteCommand={handleExecuteCommand}
        isProcessing={isProcessing}
        activeCandidateName={targetCandidate?.name}
        initialCommand={initialCommandFromParams || undefined}
        scenarios={scenarioList}
      />

      {/* 60-Second Undo Window Banner (Rendered when in UNDO_WINDOW) */}
      {status === "UNDO_WINDOW" && (
        <div className="mt-5">
          <UndoBufferBanner
            initialSeconds={undoSeconds}
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
                  <div className="mt-2 space-y-2">
                    <p className="text-xs font-medium text-success-800 dark:text-success-400">
                      All actions have been distributed to external servers:
                    </p>
                    <div className="space-y-1.5">
                      {activePlan?.items
                        ?.filter((i) => i.channel !== "calendar")
                        .map((item) => {
                          const isEmail = item.channel === "email";
                          return (
                            <div
                              key={item.id}
                              className="flex items-center gap-2 rounded-xl bg-white/70 p-2.5 dark:bg-gray-900/70 border border-success-200/80 dark:border-success-900/40 shadow-2xs"
                            >
                              <span
                                className={`inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-[11px] font-bold ${
                                  isEmail
                                    ? "bg-brand-50 text-brand-700 border border-brand-200 dark:bg-brand-500/15 dark:text-brand-300 dark:border-brand-500/30"
                                    : "bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-500/15 dark:text-emerald-300 dark:border-emerald-500/30"
                                }`}
                              >
                                {isEmail ? (
                                  <>
                                    <EnvelopeIcon/>
                                    <span>Email</span>
                                  </>
                                ) : (
                                  <>
                                    <ChatIcon/>
                                    <span>WhatsApp</span>
                                  </>
                                )}
                              </span>
                              <span className="text-xs text-gray-800 dark:text-gray-200">
                                sent to <strong>{item.recipient_name}</strong> ({item.recipient_contact}) via{" "}
                                <span className="font-mono text-[11px] text-gray-600 dark:text-gray-400">
                                  {isEmail ? "Sumopod SMTP (SSL 465)" : "WhatsApp Gateway"}
                                </span>
                              </span>
                            </div>
                          );
                        })}
                      {activePlan?.proposed_slot?.formatted_wib && (
                        <div className="flex items-center gap-2 rounded-xl bg-white/70 p-2.5 dark:bg-gray-900/70 border border-success-200/80 dark:border-success-900/40 shadow-2xs">
                          <span className="inline-flex items-center gap-1.5 rounded-lg border border-purple-200 bg-purple-50 px-2 py-1 text-[11px] font-bold text-purple-700 dark:border-purple-500/30 dark:bg-purple-500/15 dark:text-purple-300">
                            <CalenderIcon/>
                            Calendar
                          </span>
                          <span className="text-xs text-gray-800 dark:text-gray-200">
                            Slot locked at <strong>{activePlan.proposed_slot.formatted_wib}</strong> (PostgreSQL Checked)
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="mt-4 flex flex-wrap items-center gap-2.5">
                    <Button variant="primary" size="sm" onClick={handleReset}>
                      Start New Orchestration
                    </Button>
                    <Link
                      href="/orchestration/calendar"
                      className="inline-flex items-center gap-1.5 rounded-lg border border-purple-300 bg-purple-50 px-3 py-2 text-xs font-semibold text-purple-800 transition-colors hover:bg-purple-100 dark:border-purple-500/30 dark:bg-purple-500/10 dark:text-purple-300 shadow-2xs"
                    >
                      <span>📅 Calendar Matrix</span>
                    </Link>
                    <Link
                      href="/orchestration/threads"
                      className="inline-flex items-center gap-1.5 rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-800 transition-colors hover:bg-amber-100 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-300 shadow-2xs"
                    >
                      <span>📋 Triage Threads</span>
                    </Link>
                    <Link
                      href="/simulator/email"
                      className="inline-flex items-center gap-1.5 rounded-lg border border-brand-300 bg-brand-50 px-3 py-2 text-xs font-semibold text-brand-800 transition-colors hover:bg-brand-100 dark:border-brand-500/30 dark:bg-brand-500/10 dark:text-brand-300 shadow-2xs"
                    >
                      <EnvelopeIcon className="text-brand-600" />
                      <span>Email Simulator</span>
                    </Link>
                    <Link
                      href="/simulator/whatsapp"
                      className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-300 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-800 transition-colors hover:bg-emerald-100 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-300 shadow-2xs"
                    >
                      <ChatIcon className="text-emerald-600" />
                      <span>WhatsApp Simulator</span>
                    </Link>
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
              isApproving={status === "UNDO_WINDOW" || isApprovingPlan}
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
                    {targetCandidate ? (
                      <>
                        Selected Candidate: <strong>{targetCandidate.name}</strong> ({targetCandidate.applied_position})
                      </>
                    ) : (
                      "Loading candidate directory from database..."
                    )}
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

              {/* Candidates Awaiting Interview Escalation */}
              <div className="mt-5 rounded-xl border border-gray-100 bg-gray-50/60 p-4 dark:border-gray-800 dark:bg-gray-800/30">
                <div className="flex items-center justify-between border-b border-gray-200/60 pb-3 dark:border-gray-800">
                  <div className="flex items-center gap-2">
                    <h4 className="text-xs font-bold text-gray-900 dark:text-white">
                      Candidates Awaiting Interview Escalation
                    </h4>
                    <span className="rounded-full bg-brand-50 px-2 py-0.5 text-[10px] font-mono font-semibold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
                      {candidatesQueue.slice(0, 3).length} in Queue
                    </span>
                  </div>
                </div>

                <div className="mt-3 divide-y divide-gray-200/50 dark:divide-gray-800">
                  {candidatesQueue.slice(0, 3).map((cand) => (
                    <div
                      key={cand.id}
                      className="flex flex-wrap items-center justify-between gap-3 py-2.5 first:pt-1 last:pb-1"
                    >
                      <div className="flex items-center gap-3">
                        <div>
                          <div className="flex items-center gap-1.5">
                            <span className="font-semibold text-xs text-gray-900 dark:text-white">
                              {cand.name}
                            </span>
                            <span className="rounded bg-gray-200/70 px-1.5 py-0.2 text-[10px] font-medium text-gray-700 dark:bg-gray-700 dark:text-gray-300">
                              {cand.timezone}
                            </span>
                          </div>
                          <span className="text-[11px] text-gray-500 dark:text-gray-400">
                            {cand.applied_position} &bull; Channel: {cand.preferred_channel.toUpperCase()}
                          </span>
                        </div>
                      </div>

                      <button
                        type="button"
                        onClick={() => handleExecuteCommand(`Schedule an interview for ${cand.name} with Mr. Budi next week`)}
                        className="inline-flex items-center gap-1 rounded-lg border border-brand-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-brand-700 hover:bg-brand-50 dark:border-brand-500/30 dark:bg-gray-800 dark:text-brand-300 shadow-2xs transition-colors"
                      >
                        <BoltIcon/>
                        <span>Escalate Now</span>
                      </button>
                    </div>
                  ))}
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

      {/* Disambiguation Modal */}
      <DisambiguationModal
        isOpen={isDisambiguationOpen}
        onClose={() => {
          setIsDisambiguationOpen(false);
          setStatus("IDLE");
        }}
        onSelectInterviewer={handleResolveDisambiguation}
        candidateName={modalCandidate?.name ?? "Candidate"}
        targetPosition={modalCandidate?.applied_position ?? "Applied Position"}
        profiles={disambiguationProfiles}
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
