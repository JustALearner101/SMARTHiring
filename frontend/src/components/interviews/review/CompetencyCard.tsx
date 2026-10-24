"use client";

import React from "react";
import { CompetencySummaryPoint, SummaryEvidence } from "@/types/interview";
import EvidenceQuoteBox from "./EvidenceQuoteBox";
import { CheckCircleIcon } from "@/icons";

interface CompetencyCardProps {
  point: CompetencySummaryPoint;
  onJumpToEvidence: (evidence: SummaryEvidence) => void;
}

export default function CompetencyCard({
  point,
  onJumpToEvidence,
}: CompetencyCardProps) {
  const getCoverageBadge = (status: string) => {
    switch (status) {
      case "COVERED":
        return (
          <span className="rounded-md bg-success-50 px-2 py-0.5 text-[10px] font-bold text-success-700 dark:bg-success-500/15 dark:text-success-400">
            TOPIC COVERED
          </span>
        );
      case "PARTIAL":
        return (
          <span className="rounded-md bg-warning-50 px-2 py-0.5 text-[10px] font-bold text-warning-700 dark:bg-warning-500/15 dark:text-warning-400">
            PARTIAL
          </span>
        );
      default:
        return (
          <span className="rounded-md bg-gray-100 px-2 py-0.5 text-[10px] font-bold text-gray-500 dark:bg-gray-800 dark:text-gray-400">
            NOT DISCUSSED
          </span>
        );
    }
  };

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-4 md:p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900 transition-all hover:border-gray-300 dark:hover:border-gray-700">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-100 pb-3 dark:border-gray-800">
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-brand-500 font-mono text-xs font-bold text-white">
            {point.competency_code}
          </span>
          <h4 className="text-xs font-bold text-gray-900 dark:text-white">
            {point.competency_name}
          </h4>
        </div>

        <div className="flex items-center gap-2">
          {getCoverageBadge(point.coverage_status)}

          <span className="inline-flex items-center gap-1 rounded-md bg-brand-50 px-2 py-0.5 text-[10px] font-semibold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
            <CheckCircleIcon/>
            <span>Audited & Verified</span>
          </span>
        </div>
      </div>

      {/* Neutral Descriptive Summary (BR-01) */}
      <div className="mt-3">
        <p className="text-xs leading-relaxed text-gray-700 dark:text-gray-300">
          {point.content}
        </p>
      </div>

      {/* Citations and Verbatim Evidence Quotes */}
      {point.evidences.length > 0 && (
        <div className="mt-3 space-y-2">
          <span className="block text-[11px] font-semibold uppercase tracking-wider text-gray-400">
            Verbatim Evidence Citations ({point.evidences.length}):
          </span>
          {point.evidences.map((ev) => (
            <EvidenceQuoteBox
              key={ev.id}
              evidence={ev}
              onJumpToEvidence={onJumpToEvidence}
            />
          ))}
        </div>
      )}
    </div>
  );
}
