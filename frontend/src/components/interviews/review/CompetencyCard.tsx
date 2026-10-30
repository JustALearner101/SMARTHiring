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
  const isVerified =
    point.verification_status === "VERIFIED" &&
    point.coverage_status !== "NOT_DISCUSSED" &&
    point.evidences &&
    point.evidences.length > 0;

  const renderSingleStatusBadge = () => {
    if (isVerified) {
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-success-50 px-2.5 py-0.5 text-xs font-medium text-success-700 dark:bg-success-500/15 dark:text-success-400 border border-success-200 dark:border-success-500/30 whitespace-nowrap">
          <CheckCircleIcon className="text-xs" />
          <span>Verified</span>
        </span>
      );
    }

    if (point.coverage_status === "PARTIAL") {
      return (
        <span className="inline-flex items-center rounded-full bg-warning-50 px-2.5 py-0.5 text-xs font-medium text-warning-700 dark:bg-warning-500/15 dark:text-warning-400 border border-warning-200 dark:border-warning-500/30 whitespace-nowrap">
          Partial
        </span>
      );
    }

    return (
      <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-500 dark:bg-gray-800 dark:text-gray-400 whitespace-nowrap">
        Not discussed
      </span>
    );
  };

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-4 md:p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900 transition-all hover:border-gray-300 dark:hover:border-gray-700">
      <div className="flex items-center justify-between gap-3 border-b border-gray-100 pb-3 dark:border-gray-800">
        <div className="flex items-center gap-2.5 min-w-0">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-brand-500 font-mono text-xs font-bold text-white">
            {point.competency_code}
          </span>
          <h4 className="text-xs font-bold text-gray-900 dark:text-white truncate">
            {point.competency_name}
          </h4>
        </div>

        <div className="shrink-0">
          {renderSingleStatusBadge()}
        </div>
      </div>

      {/* Neutral Descriptive Summary */}
      <div className="mt-3">
        <p className="text-xs leading-relaxed text-gray-700 dark:text-gray-300">
          {point.content}
        </p>
      </div>

      {/* Evidence Citations */}
      {point.evidences && point.evidences.length > 0 && (
        <div className="mt-3 space-y-2">
          <span className="block text-[11px] font-semibold uppercase tracking-wider text-gray-400">
            Evidence ({point.evidences.length})
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
