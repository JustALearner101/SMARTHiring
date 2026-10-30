"use client";

import React, { useState } from "react";
import { Link } from "@/i18n/navigation";
import Button from "@/components/ui/button/Button";
import { UserRole } from "@/types/auth";
import { AdvanceNextStage, HrDecision, HrDecisionType } from "@/types/interview";
import {
  AlertIcon,
  ArrowRightIcon,
  BoltIcon,
  CheckCircleIcon,
  CloseIcon,
  LockIcon,
} from "@/icons";

interface HrDecisionCardProps {
  initialDecision?: HrDecision;
  onSubmitDecision: (
    decision: HrDecisionType,
    notes: string,
    nextStage?: AdvanceNextStage | null
  ) => Promise<void> | void;
  candidateId: string;
  candidateName: string;
  roundName: string;
  currentUserId?: string | null;
  currentUserRole?: UserRole | null;
  interviewerId?: string | null;
  interviewerName?: string;
}

const STAGE_LABELS: Record<AdvanceNextStage, string> = {
  NEXT_INTERVIEW: "Next Interview Round (Next Round Ready)",
  TECHNICAL_TEST: "Technical Test Assessment",
  OFFERED: "Final Offering (OFFERED)",
};

export default function HrDecisionCard({
  initialDecision,
  onSubmitDecision,
  candidateId,
  candidateName,
  roundName,
  currentUserId,
  currentUserRole,
  interviewerId,
  interviewerName,
}: HrDecisionCardProps) {
  const isFinalized = Boolean(
    initialDecision &&
      (!initialDecision.workflow_status ||
        initialDecision.workflow_status === "FINALIZED")
  );
  const isPendingHrFollowup =
    initialDecision?.workflow_status === "PENDING_HR_FOLLOWUP";

  const isHrOrAdmin = currentUserRole === "HR" || currentUserRole === "ADMIN";
  const isAssignedToAnotherUser = Boolean(
    interviewerId && currentUserId && interviewerId !== currentUserId
  );

  const inferredDefaultStage: AdvanceNextStage =
    initialDecision?.next_stage ??
    (roundName.toLowerCase().includes("hr") ? "NEXT_INTERVIEW" : "OFFERED");

  const [selectedDecision, setSelectedDecision] = useState<HrDecisionType>(
    initialDecision?.decision || "ADVANCE"
  );
  const [nextStage, setNextStage] = useState<AdvanceNextStage>(inferredDefaultStage);
  const [notes, setNotes] = useState(() => {
    if (isPendingHrFollowup && isHrOrAdmin && initialDecision) {
      return `Following up on interviewer recommendation (${initialDecision.decided_by}): ${initialDecision.notes}`;
    }
    return (
      initialDecision?.notes ||
      "Candidate demonstrated strong competencies based on interview transcript evidence."
    );
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await onSubmitDecision(
        selectedDecision,
        notes,
        selectedDecision === "ADVANCE" ? nextStage : null
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderDecisionOutcomePill = (dec: HrDecision) => {
    if (dec.decision === "ADVANCE") {
      return (
        <span className="inline-flex items-center gap-1.5 rounded-lg bg-success-50 px-2.5 py-1 text-xs font-bold text-success-700 dark:bg-success-500/15 dark:text-success-300">
          <CheckCircleIcon />
          <span>
            ADVANCE
            {dec.next_stage ? ` → ${STAGE_LABELS[dec.next_stage] ?? dec.next_stage}` : ""}
          </span>
        </span>
      );
    }
    if (dec.decision === "HOLD") {
      return (
        <span className="inline-flex items-center gap-1.5 rounded-lg bg-warning-50 px-2.5 py-1 text-xs font-bold text-warning-700 dark:bg-warning-500/15 dark:text-warning-300">
          <AlertIcon />
          <span>HOLD (On Hold / Comparison)</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 rounded-lg bg-error-50 px-2.5 py-1 text-xs font-bold text-error-700 dark:bg-error-500/15 dark:text-error-300">
        <CloseIcon />
        <span>REJECTED</span>
      </span>
    );
  };

  // =========================================================================
  // STATE 1: FINALIZED DECISION (IMMUTABLE ONE-WAY LOCK FOR ALL ROLES)
  // =========================================================================
  if (isFinalized && initialDecision) {
    return (
      <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-100 pb-3 dark:border-gray-800">
          <div className="text-start">
            <h3 className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <span>Finalized Evaluation Decision</span>
              <span className="inline-flex items-center gap-1 rounded bg-gray-100 px-2 py-0.5 font-mono text-[10px] font-bold text-gray-700 dark:bg-gray-800 dark:text-gray-300">
                <LockIcon />
                IMMUTABLE RECORD
              </span>
            </h3>
            <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
              Final decision has been permanently finalized and locked in the audit trail.
            </p>
          </div>

          <span className="inline-flex items-center gap-1 rounded-full bg-success-50 px-2.5 py-1 text-xs font-semibold text-success-700 dark:bg-success-500/15 dark:text-success-400">
            <CheckCircleIcon />
            <span>FINALIZED</span>
          </span>
        </div>

        <div className="rounded-xl border border-gray-200 bg-gray-50/70 p-4 text-start space-y-3 dark:border-gray-800 dark:bg-gray-800/50">
          <div className="flex flex-wrap items-center justify-between gap-2">
            {renderDecisionOutcomePill(initialDecision)}
            <span className="text-[11px] text-gray-500 dark:text-gray-400">
              Decided by <strong>{initialDecision.decided_by}</strong> &bull;{" "}
              {initialDecision.decided_at}
            </span>
          </div>

          <div>
            <span className="block text-[11px] font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Final Rationale &amp; Audit Notes:
            </span>
            <p className="mt-1 text-xs text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-line">
              {initialDecision.notes}
            </p>
          </div>
        </div>

        {isHrOrAdmin && (
          <div className="flex flex-col gap-3 rounded-xl border border-gray-200 bg-gray-50 p-3.5 sm:flex-row sm:items-center sm:justify-between dark:border-gray-800 dark:bg-gray-800/50">
            <div className="text-start text-xs text-gray-700 dark:text-gray-300">
              {initialDecision.decision === "ADVANCE" &&
              initialDecision.next_stage === "NEXT_INTERVIEW" ? (
                <span>
                  Candidate status officially updated to{" "}
                  <strong>Next Round Ready (ESCALATED)</strong>.
                </span>
              ) : (
                <span>
                  Candidate status in Master Candidates has been synchronized permanently.
                </span>
              )}
            </div>

            <div className="flex shrink-0 items-center gap-2">
              {initialDecision.decision === "ADVANCE" &&
              initialDecision.next_stage === "NEXT_INTERVIEW" ? (
                <Link
                  href={`/orchestration/scheduling?candidateId=${candidateId}`}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-brand-500 px-3 py-2 text-xs font-semibold text-white shadow-theme-xs hover:bg-brand-600 transition-all"
                >
                  <BoltIcon className="text-white" />
                  <span>Schedule Next Interview</span>
                  <ArrowRightIcon className="rtl:rotate-180" />
                </Link>
              ) : (
                <Link
                  href="/master/candidates"
                  className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
                >
                  <span>View Candidates Directory</span>
                  <ArrowRightIcon className="rtl:rotate-180" />
                </Link>
              )}
            </div>
          </div>
        )}
      </div>
    );
  }

  // =========================================================================
  // STATE 2A: PENDING_HR_FOLLOWUP VIEWED BY INTERVIEWER (LOCKED HANDOFF)
  // =========================================================================
  if (isPendingHrFollowup && initialDecision && !isHrOrAdmin) {
    return (
      <div className="rounded-2xl border border-brand-200 bg-white p-5 shadow-theme-xs dark:border-brand-500/30 dark:bg-gray-900 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-100 pb-3 dark:border-gray-800">
          <div className="text-start">
            <h3 className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <span>Interviewer Recommendation Submitted</span>
              <span className="inline-flex items-center gap-1 rounded bg-brand-50 px-2 py-0.5 font-mono text-[10px] font-bold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
                <LockIcon />
                LOCKED FOR HR FOLLOW-UP
              </span>
            </h3>
            <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
              Your evaluation recommendation has been locked and forwarded to HR for final review.
            </p>
          </div>

          <span className="inline-flex items-center gap-1 rounded-full bg-warning-50 px-2.5 py-1 text-xs font-semibold text-warning-700 dark:bg-warning-500/15 dark:text-warning-300">
            <AlertIcon />
            <span>Pending HR Follow-Up</span>
          </span>
        </div>

        <div className="rounded-xl border border-brand-100 bg-brand-50/40 p-4 text-start space-y-3 dark:border-brand-500/20 dark:bg-brand-500/10">
          <div className="flex flex-wrap items-center justify-between gap-2">
            {renderDecisionOutcomePill(initialDecision)}
            <span className="text-[11px] text-gray-500 dark:text-gray-400">
              Submitted by <strong>{initialDecision.decided_by}</strong> &bull;{" "}
              {initialDecision.decided_at}
            </span>
          </div>
          <div>
            <span className="block text-[11px] font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Submitted Evaluation Notes:
            </span>
            <p className="mt-1 text-xs text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-line">
              {initialDecision.notes}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // =========================================================================
  // STATE 3: UNDECIDED SESSION ASSIGNED TO ANOTHER INTERVIEWER (READ-ONLY)
  // =========================================================================
  if (!initialDecision && isAssignedToAnotherUser) {
    return (
      <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-100 pb-3 dark:border-gray-800">
          <div className="text-start">
            <h3 className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <span>Awaiting Assigned Interviewer Evaluation</span>
              <span className="inline-flex items-center gap-1 rounded bg-warning-50 px-2 py-0.5 font-mono text-[10px] font-bold text-warning-700 dark:bg-warning-500/15 dark:text-warning-300">
                <LockIcon />
                READ-ONLY
              </span>
            </h3>
            <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
              Only the assigned interviewer is authorized to submit the initial evaluation for this session.
            </p>
          </div>
        </div>

        <div className="rounded-xl border border-warning-200 bg-warning-50/50 p-4 text-start text-xs text-warning-900 dark:border-warning-500/25 dark:bg-warning-500/10 dark:text-warning-200">
          This interview session is assigned to interviewer{" "}
          <strong>{interviewerName || "Assigned Interviewer"}</strong>. Awaiting evaluation recommendation from the assigned interviewer before HR can proceed with final action.
        </div>
      </div>
    );
  }

  // =========================================================================
  // STATE 4: ACTIVE FORM
  // - Interviewer submitting 1-time Recommendation to HR (locks to PENDING_HR_FOLLOWUP)
  // - HR/Admin finalizing Interviewer's Recommendation (locks to FINALIZED)
  // - HR/Admin deciding their own HR Screening session (locks to FINALIZED)
  // =========================================================================
  const isInterviewerSubmission = currentUserRole === "INTERVIEWER";
  const headerTitle = isPendingHrFollowup
    ? "HR Final Follow-Up Gate (Confirm Interviewer Recommendation)"
    : isInterviewerSubmission
    ? "Interviewer Evaluation & Recommendation Gate"
    : "HR Final Decision Gate";

  const headerSubtitle = isPendingHrFollowup
    ? "Review interviewer recommendations below, then finalize the HR decision to officially update candidate status."
    : isInterviewerSubmission
    ? "Your evaluation recommendation will be locked one-way and forwarded to HR for final review."
    : "Candidate application status in the Master Directory is updated automatically and locked once saved.";

  const submitButtonLabel = isPendingHrFollowup
    ? "Finalize HR Follow-Up Decision"
    : isInterviewerSubmission
    ? "Submit Recommendation to HR"
    : "Submit Final HR Decision";

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-100 pb-3 dark:border-gray-800">
        <div className="text-start">
          <h3 className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <span>{headerTitle}</span>
            <span className="rounded bg-brand-50 px-2 py-0.5 font-mono text-[10px] font-bold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
              {isInterviewerSubmission ? "HANDOFF TO HR" : "FINAL APPROVAL"}
            </span>
          </h3>
          <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
            {headerSubtitle}
          </p>
        </div>
      </div>

      {/* Interviewer Recommendation Banner shown to HR/Admin during Follow-Up */}
      {isPendingHrFollowup && initialDecision && (
        <div className="mt-4 rounded-xl border border-brand-200 bg-brand-50/50 p-4 text-start space-y-2.5 dark:border-brand-500/30 dark:bg-brand-500/10">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-xs font-bold text-brand-800 dark:text-brand-300">
              Interviewer Recommendation ({initialDecision.decided_by}):
            </span>
            {renderDecisionOutcomePill(initialDecision)}
          </div>
          <p className="text-xs text-gray-700 dark:text-gray-200 leading-relaxed whitespace-pre-line">
            &ldquo;{initialDecision.notes}&rdquo;
          </p>
          <span className="block text-[10px] text-gray-500 dark:text-gray-400">
            Submitted at {initialDecision.decided_at} &bull; Awaiting final HR confirmation
          </span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-4 space-y-4">
        {/* Decision Option Radio Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          <label
            className={`cursor-pointer flex flex-col justify-between rounded-xl border p-3 text-start transition-all ${
              selectedDecision === "ADVANCE"
                ? "border-success-500 bg-success-50/50 dark:bg-success-500/10 dark:border-success-500"
                : "border-gray-200 bg-white hover:border-gray-300 dark:border-gray-800 dark:bg-gray-800/40"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-success-800 dark:text-success-300 flex items-center gap-1.5">
                <CheckCircleIcon />
                ADVANCE
              </span>
              <input
                type="radio"
                name="hr-decision"
                value="ADVANCE"
                checked={selectedDecision === "ADVANCE"}
                onChange={() => setSelectedDecision("ADVANCE")}
                className="h-3.5 w-3.5 text-success-600 focus:ring-success-500"
              />
            </div>
            <span className="mt-1 text-[11px] text-gray-500 dark:text-gray-400">
              Advance to next interview round, technical test, or job offering.
            </span>
          </label>

          <label
            className={`cursor-pointer flex flex-col justify-between rounded-xl border p-3 text-start transition-all ${
              selectedDecision === "HOLD"
                ? "border-warning-500 bg-warning-50/50 dark:bg-warning-500/10 dark:border-warning-500"
                : "border-gray-200 bg-white hover:border-gray-300 dark:border-gray-800 dark:bg-gray-800/40"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-warning-800 dark:text-warning-300 flex items-center gap-1.5">
                <AlertIcon />
                HOLD
              </span>
              <input
                type="radio"
                name="hr-decision"
                value="HOLD"
                checked={selectedDecision === "HOLD"}
                onChange={() => setSelectedDecision("HOLD")}
                className="h-3.5 w-3.5 text-warning-600 focus:ring-warning-500"
              />
            </div>
            <span className="mt-1 text-[11px] text-gray-500 dark:text-gray-400">
              Put on hold for comparison against other candidates.
            </span>
          </label>

          <label
            className={`cursor-pointer flex flex-col justify-between rounded-xl border p-3 text-start transition-all ${
              selectedDecision === "REJECT"
                ? "border-error-500 bg-error-50/50 dark:bg-error-500/10 dark:border-error-500"
                : "border-gray-200 bg-white hover:border-gray-300 dark:border-gray-800 dark:bg-gray-800/40"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-error-800 dark:text-error-300 flex items-center gap-1.5">
                <CloseIcon />
                REJECT
              </span>
              <input
                type="radio"
                name="hr-decision"
                value="REJECT"
                checked={selectedDecision === "REJECT"}
                onChange={() => setSelectedDecision("REJECT")}
                className="h-3.5 w-3.5 text-error-600 focus:ring-error-500"
              />
            </div>
            <span className="mt-1 text-[11px] text-gray-500 dark:text-gray-400">
              Not recommended to advance to the next selection stage.
            </span>
          </label>
        </div>

        {/* Next Pipeline Stage Selector when ADVANCE is active */}
        {selectedDecision === "ADVANCE" && (
          <div className="rounded-xl border border-brand-200 bg-brand-50/40 p-3.5 text-start dark:border-brand-500/30 dark:bg-brand-500/10">
            <span className="block text-xs font-bold text-gray-900 dark:text-white">
              {isInterviewerSubmission
                ? "Recommended Next Stage for HR:"
                : "Select Next Stage (Automatically Updates Application Status):"}
            </span>
            <div className="mt-2.5 grid grid-cols-1 gap-2 sm:grid-cols-3">
              <button
                type="button"
                onClick={() => setNextStage("NEXT_INTERVIEW")}
                className={`rounded-lg border p-2.5 text-start text-xs transition-all ${
                  nextStage === "NEXT_INTERVIEW"
                    ? "border-brand-500 bg-white font-semibold text-brand-700 shadow-theme-xs dark:bg-gray-900 dark:text-brand-300"
                    : "border-gray-200 bg-white/70 text-gray-600 hover:border-gray-300 dark:border-gray-700 dark:bg-gray-800/60 dark:text-gray-300"
                }`}
              >
                <span className="block font-bold">1. Next Interview Round</span>
                <span className="mt-0.5 block text-[11px] font-normal text-gray-500 dark:text-gray-400">
                  User / Technical Interview &rarr; Status: <strong>Next Round Ready</strong>
                </span>
              </button>

              <button
                type="button"
                onClick={() => setNextStage("TECHNICAL_TEST")}
                className={`rounded-lg border p-2.5 text-start text-xs transition-all ${
                  nextStage === "TECHNICAL_TEST"
                    ? "border-brand-500 bg-white font-semibold text-brand-700 shadow-theme-xs dark:bg-gray-900 dark:text-brand-300"
                    : "border-gray-200 bg-white/70 text-gray-600 hover:border-gray-300 dark:border-gray-700 dark:bg-gray-800/60 dark:text-gray-300"
                }`}
              >
                <span className="block font-bold">2. Technical Test</span>
                <span className="mt-0.5 block text-[11px] font-normal text-gray-500 dark:text-gray-400">
                  Take-Home / Assessment &rarr; Status: <strong>Technical Test</strong>
                </span>
              </button>

              <button
                type="button"
                onClick={() => setNextStage("OFFERED")}
                className={`rounded-lg border p-2.5 text-start text-xs transition-all ${
                  nextStage === "OFFERED"
                    ? "border-brand-500 bg-white font-semibold text-brand-700 shadow-theme-xs dark:bg-gray-900 dark:text-brand-300"
                    : "border-gray-200 bg-white/70 text-gray-600 hover:border-gray-300 dark:border-gray-700 dark:bg-gray-800/60 dark:text-gray-300"
                }`}
              >
                <span className="block font-bold">3. Final Offering</span>
                <span className="mt-0.5 block text-[11px] font-normal text-gray-500 dark:text-gray-400">
                  Passed all selection stages &rarr; Status: <strong>Offering</strong>
                </span>
              </button>
            </div>
          </div>
        )}

        {/* Evaluation Notes */}
        <div className="text-start">
          <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
            {isInterviewerSubmission
              ? `Technical / User Evaluation Notes for ${candidateName}:`
              : `HR Final Decision Notes for ${candidateName}:`}
          </label>
          <textarea
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            required
            placeholder="Write evaluation reasoning based on transcript evidence..."
            className="w-full rounded-xl border border-gray-300 bg-gray-50 p-3 text-xs text-gray-800 placeholder-gray-400 focus:border-brand-500 focus:bg-white focus:outline-hidden dark:border-gray-700 dark:bg-gray-800 dark:text-white"
          />
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
          <span className="text-[11px] text-gray-500 dark:text-gray-400">
            Notice: Decision is one-way (immutable) and cannot be modified once submitted.
          </span>
          <Button
            variant="primary"
            size="sm"
            type="submit"
            disabled={isSubmitting}
            startIcon={<LockIcon />}
          >
            {submitButtonLabel}
          </Button>
        </div>
      </form>
    </div>
  );
}
