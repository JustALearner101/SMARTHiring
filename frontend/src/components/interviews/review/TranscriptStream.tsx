"use client";

import React, { useState, useEffect, useRef } from "react";
import { TranscriptSegment } from "@/types/interview";
import { TimeIcon, CheckCircleIcon, UserIcon } from "@/icons";

interface TranscriptStreamProps {
  segments: TranscriptSegment[];
  activeSegmentId: string | null;
  onSelectSegment: (segment: TranscriptSegment) => void;
}

export default function TranscriptStream({
  segments,
  activeSegmentId,
  onSelectSegment,
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
        <div className="flex items-center justify-between pb-3">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-gray-900 dark:text-white">
              Verbatim Dialogue Transcript
            </h3>
            <span className="rounded-full bg-gray-100 px-2 py-0.5 font-mono text-[11px] text-gray-600 dark:bg-gray-800 dark:text-gray-300">
              {segments.length} segments
            </span>
          </div>

          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-success-600 dark:text-success-400">
            <CheckCircleIcon/>
            ASR Sync Active
          </span>
        </div>

        <div className="relative">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search dialogue keywords (e.g. 'Turbopack', 'WebSocket')..."
            className="w-full rounded-xl border border-gray-300 bg-gray-50 py-2 pl-9 pr-3 text-xs text-gray-800 placeholder-gray-400 focus:border-brand-500 focus:bg-white focus:outline-hidden dark:border-gray-700 dark:bg-gray-800 dark:text-white"
          />
        </div>
      </div>

      {/* Scrolling Segment List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 max-h-[460px]">
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
                className={`cursor-pointer rounded-xl p-3.5 transition-all border ${
                  isActive
                    ? "border-brand-500 bg-brand-50/30 ring-2 ring-brand-500/20 shadow-xs dark:bg-brand-500/10"
                    : isCandidate
                    ? "border-emerald-200 bg-emerald-50/20 hover:border-emerald-300 dark:border-emerald-800/40 dark:bg-emerald-950/10"
                    : "border-gray-200 bg-white hover:border-gray-300 dark:border-gray-800 dark:bg-gray-800/40"
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-2">
                    <span
                      className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-semibold ${
                        isCandidate
                          ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-200"
                          : "bg-brand-50 text-brand-800 dark:bg-brand-900/60 dark:text-brand-200"
                      }`}
                    >
                      <UserIcon/>
                      <span>{seg.speaker_name}</span>
                    </span>

                    <span className="rounded bg-gray-100 px-1.5 py-0.2 font-mono text-[10px] text-gray-500 dark:bg-gray-800 dark:text-gray-400">
                      {seg.id}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center gap-1 font-mono text-[11px] text-gray-500 dark:text-gray-400">
                      <TimeIcon className="text-brand-500" />
                      <span>{seg.timestamp_formatted}</span>
                    </span>

                    <span className="text-[10px] text-gray-400">
                      {Math.round(seg.confidence * 100)}% conf
                    </span>
                  </div>
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
