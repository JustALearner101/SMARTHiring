"use client";

import React from "react";
import { SummaryEvidence } from "@/types/interview";
import { TimeIcon, ArrowRightIcon } from "@/icons";

interface EvidenceQuoteBoxProps {
  evidence: SummaryEvidence;
  onJumpToEvidence: (evidence: SummaryEvidence) => void;
}

export default function EvidenceQuoteBox({
  evidence,
  onJumpToEvidence,
}: EvidenceQuoteBoxProps) {
  return (
    <div className="mt-2 rounded-xl border border-amber-200 bg-amber-50/50 p-3 dark:border-amber-500/25 dark:bg-amber-500/10">
      <div className="flex items-center justify-between gap-2 mb-1.5">
        <span className="inline-flex items-center gap-1 font-mono text-xs font-semibold text-amber-800 dark:text-amber-300">
          <TimeIcon className="text-xs" />
          <span>{evidence.timestamp_formatted}</span>
        </span>

        <button
          type="button"
          onClick={() => onJumpToEvidence(evidence)}
          className="inline-flex items-center gap-1 rounded-md bg-white px-2 py-0.5 text-xs font-medium text-amber-800 shadow-2xs hover:bg-amber-100 dark:bg-gray-800 dark:text-amber-300 dark:hover:bg-gray-700 transition-colors"
          title="Play audio from this timestamp and highlight transcript"
        >
          <span>Play from {evidence.timestamp_formatted}</span>
          <ArrowRightIcon className="text-xs rtl:rotate-180" />
        </button>
      </div>

      <blockquote className="border-s-2 border-amber-400 ps-2.5 text-xs italic text-gray-800 dark:text-gray-200 leading-relaxed">
        &ldquo;{evidence.quote_text}&rdquo;
      </blockquote>
    </div>
  );
}
