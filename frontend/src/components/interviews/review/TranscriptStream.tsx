"use client";

import React, { useState, useEffect, useRef } from "react";
import Button from "@/components/ui/button/Button";
import { TranscriptSegment } from "@/types/interview";
import { TimeIcon } from "@/icons";

interface TranscriptStreamProps {
  segments: TranscriptSegment[];
  activeSegmentId: string | null;
  onSelectSegment: (segment: TranscriptSegment) => void;
  onSwapSpeakers?: () => void;
  isSwapping?: boolean;
}

export default function TranscriptStream({
  segments,
  activeSegmentId,
  onSelectSegment,
  onSwapSpeakers,
  isSwapping = false,
}: TranscriptStreamProps) {
  const [search, setSearch] = useState("");
  const activeRef = useRef<HTMLDivElement>(null);

  const filteredSegments = segments.filter((seg) =>
    seg.text.toLowerCase().includes(search.toLowerCase()) ||
    seg.speaker_name.toLowerCase().includes(search.toLowerCase()) ||
    seg.timestamp_formatted.includes(search)
  );

  useEffect(() => {
    if (activeSegmentId && activeRef.current) {
      activeRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [activeSegmentId]);

  return (
    <div className="flex flex-col h-full rounded-2xl border border-gray-200 bg-white shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
      {/* Header and Search */}
      <div className="border-b border-gray-100 p-4 dark:border-gray-800">
        <div className="flex items-center justify-between gap-3 pb-3">
          <div className="flex items-baseline gap-2 min-w-0">
            <h3 className="text-sm font-bold text-gray-900 dark:text-white truncate">
              Transcript
            </h3>
            <span className="text-xs text-gray-500 dark:text-gray-400 font-mono">
              ({segments.length})
            </span>
          </div>

          {onSwapSpeakers && (
            <Button
              size="sm"
              variant="outline"
              onClick={onSwapSpeakers}
              isLoading={isSwapping}
              className="whitespace-nowrap"
              title="Tukar Peran Pembicara (Kandidat ↔ Pewawancara)"
            >
              Swap speakers
            </Button>
          )}
        </div>

        <div className="relative">
          <div className="pointer-events-none absolute inset-y-0 start-0 flex items-center ps-3 text-gray-400">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search transcript..."
            className="w-full rounded-xl border border-gray-300 bg-gray-50 py-2 ps-9 pe-3 text-xs text-gray-800 placeholder-gray-400 focus:border-brand-500 focus:bg-white focus:outline-hidden dark:border-gray-700 dark:bg-gray-800 dark:text-white"
          />
        </div>
      </div>

      {/* Scrolling Segment List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2.5 max-h-[460px]">
        {filteredSegments.length === 0 ? (
          <div className="py-12 text-center text-xs text-gray-400">
            No transcript segments match &quot;{search}&quot;
          </div>
        ) : (
          filteredSegments.map((seg) => {
            const isActive = seg.id === activeSegmentId;
            const isCandidate = seg.speaker_type === "CANDIDATE";

            return (
              <div
                key={seg.id}
                ref={isActive ? activeRef : undefined}
                onClick={() => onSelectSegment(seg)}
                className={`cursor-pointer rounded-xl p-3 transition-all border ${
                  isActive
                    ? "border-brand-500 bg-brand-50/20 ring-2 ring-brand-500/20 dark:bg-brand-500/10"
                    : isCandidate
                    ? "border-gray-200 bg-white hover:border-emerald-300 dark:border-gray-800 dark:bg-gray-800/40 border-s-3 border-s-emerald-500"
                    : "border-gray-200 bg-white hover:border-gray-300 dark:border-gray-800 dark:bg-gray-800/40 border-s-3 border-s-brand-500"
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span
                    className={`text-xs font-semibold ${
                      isCandidate
                        ? "text-emerald-700 dark:text-emerald-400"
                        : "text-brand-700 dark:text-brand-400"
                    }`}
                  >
                    {seg.speaker_name}
                  </span>

                  <span className="inline-flex items-center gap-1 font-mono text-[11px] text-gray-400 dark:text-gray-500">
                    <TimeIcon className="text-xs" />
                    <span>{seg.timestamp_formatted}</span>
                  </span>
                </div>

                <p className="text-xs leading-relaxed text-gray-800 dark:text-gray-200">
                  {seg.text}
                </p>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
