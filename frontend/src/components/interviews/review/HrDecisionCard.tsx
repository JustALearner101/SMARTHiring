"use client";

import React, { useState } from "react";
import Button from "@/components/ui/button/Button";
import { HrDecision, HrDecisionType } from "@/types/interview";
import { CheckCircleIcon, AlertIcon, CloseIcon, LockIcon } from "@/icons";

interface HrDecisionCardProps {
  initialDecision?: HrDecision;
  onSubmitDecision: (decision: HrDecisionType, notes: string) => void;
  candidateName: string;
}

export default function HrDecisionCard({
  initialDecision,
  onSubmitDecision,
  candidateName,
}: HrDecisionCardProps) {
  const [selectedDecision, setSelectedDecision] = useState<HrDecisionType>(
    initialDecision?.decision || "ADVANCE"
  );
  const [notes, setNotes] = useState(
    initialDecision?.notes ||
      "Kandidat mendemonstrasikan keahlian teknis arsitektur frontend dan komunikasi kolaboratif yang sangat baik. Direkomendasikan lolos ke tahap offering."
  );
  const [isSubmitted, setIsSubmitted] = useState(!!initialDecision);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmitDecision(selectedDecision, notes);
    setIsSubmitted(true);
  };

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-100 pb-3 dark:border-gray-800">
        <div>
          <h3 className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <span>HR Final Decision Gate</span>
            <span className="rounded bg-brand-50 px-2 py-0.5 font-mono text-[10px] font-bold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
              APPROVAL
            </span>
          </h3>
          <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
            AI Copilot provides evidence-based analysis; the hiring decision remains 100% human-verified.
          </p>
        </div>

        {isSubmitted && (
          <span className="inline-flex items-center gap-1 rounded-full bg-success-50 px-2.5 py-1 text-xs font-semibold text-success-700 dark:bg-success-500/15 dark:text-success-400">
            <CheckCircleIcon/>
            <span>Decision Recorded</span>
          </span>
        )}
      </div>

      <form onSubmit={handleSubmit} className="mt-4 space-y-4">
        {/* Decision Option Radio Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          <label
            className={`cursor-pointer flex flex-col justify-between rounded-xl border p-3 transition-all ${
              selectedDecision === "ADVANCE"
                ? "border-success-500 bg-success-50/50 dark:bg-success-500/10 dark:border-success-500"
                : "border-gray-200 bg-white hover:border-gray-300 dark:border-gray-800 dark:bg-gray-800/40"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-success-800 dark:text-success-300 flex items-center gap-1.5">
                <CheckCircleIcon/>
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
              Advance to offering or next interview round.
            </span>
          </label>

          <label
            className={`cursor-pointer flex flex-col justify-between rounded-xl border p-3 transition-all ${
              selectedDecision === "HOLD"
                ? "border-warning-500 bg-warning-50/50 dark:bg-warning-500/10 dark:border-warning-500"
                : "border-gray-200 bg-white hover:border-gray-300 dark:border-gray-800 dark:bg-gray-800/40"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-warning-800 dark:text-warning-300 flex items-center gap-1.5">
                <AlertIcon/>
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
              Hold candidate to compare with incoming applicants.
            </span>
          </label>

          <label
            className={`cursor-pointer flex flex-col justify-between rounded-xl border p-3 transition-all ${
              selectedDecision === "REJECT"
                ? "border-error-500 bg-error-50/50 dark:bg-error-500/10 dark:border-error-500"
                : "border-gray-200 bg-white hover:border-gray-300 dark:border-gray-800 dark:bg-gray-800/40"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-error-800 dark:text-error-300 flex items-center gap-1.5">
                <CloseIcon/>
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
              Send polite rejection notification.
            </span>
          </label>
        </div>

        {/* Evaluation Notes */}
        <div>
          <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
            HR Evaluation & Notes for {candidateName}:
          </label>
          <textarea
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Enter rationale based on cited evidence..."
            className="w-full rounded-xl border border-gray-300 bg-gray-50 p-3 text-xs text-gray-800 placeholder-gray-400 focus:border-brand-500 focus:bg-white focus:outline-hidden dark:border-gray-700 dark:bg-gray-800 dark:text-white"
          />
        </div>

        <div className="flex justify-end pt-1">
          <Button variant="primary" size="sm" type="submit" startIcon={<LockIcon/>}>
            {isSubmitted ? "Update Decision" : "Submit Final Decision"}
          </Button>
        </div>
      </form>
    </div>
  );
}
