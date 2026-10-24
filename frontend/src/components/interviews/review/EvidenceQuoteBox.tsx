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
    <div className="mt-2.5 rounded-xl border border-amber-200 bg-amber-50/60 p-3 dark:border-amber-500/30 dark:bg-amber-500/10">
      <div className="flex items-center justify-between gap-2 mb-1.5">
        <span className="inline-flex items-center gap-1 font-mono text-[11px] font-bold text-amber-800 dark:text-amber-300">
          <TimeIcon/>
          <span>Timestamp: {evidence.timestamp_formatted}</span>
        </span>

        <button
          type="button"
          onClick={() => onJumpToEvidence(evidence)}
          className="inline-flex items-center gap-1 rounded-md bg-white px-2 py-0.5 text-[11px] font-semibold text-amber-800 shadow-2xs hover:bg-amber-100 dark:bg-gray-800 dark:text-amber-300 dark:hover:bg-gray-700 transition-colors"
          title="Jump to audio position and highlight transcript segment"
        >
          <span>Jump to Audio</span>
          <ArrowRightIcon/>
        </button>
      </div>

      <blockquote className="border-l-2 border-amber-400 pl-2.5 text-xs italic text-gray-800 dark:text-gray-200">
        &ldquo;{evidence.quote_text}&rdquo;
      </blockquote>
    </div>
  );
}
