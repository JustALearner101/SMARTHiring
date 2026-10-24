"use client";

import React, { useState } from "react";
import { AudioIcon, TimeIcon } from "@/icons";

interface AudioWavePlayerProps {
  currentTimeMs: number;
  durationMs: number;
  isPlaying: boolean;
  onTogglePlay: () => void;
  onSeek: (ms: number) => void;
}

export default function AudioWavePlayer({
  currentTimeMs,
  durationMs,
  isPlaying,
  onTogglePlay,
  onSeek,
}: AudioWavePlayerProps) {
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1.0);

  const formatMs = (ms: number) => {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
  };

  const progressPercent = durationMs > 0 ? (currentTimeMs / durationMs) * 100 : 0;

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Play/Pause Button & Time */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onTogglePlay}
            className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-colors shadow-2xs ${
              isPlaying
                ? "bg-warning-500 text-white hover:bg-warning-600"
                : "bg-brand-500 text-white hover:bg-brand-600"
            }`}
            title={isPlaying ? "Pause audio" : "Play audio"}
          >
            {isPlaying ? (
              <svg className="h-4 w-4 fill-current" viewBox="0 0 24 24">
                <rect x="6" y="4" width="4" height="16" rx="1" />
                <rect x="14" y="4" width="4" height="16" rx="1" />
              </svg>
            ) : (
              <svg className="h-4 w-4 fill-current ml-0.5" viewBox="0 0 24 24">
                <polygon points="5,3 19,12 5,21" />
              </svg>
            )}
          </button>

          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm font-bold text-gray-900 dark:text-white">
                {formatMs(currentTimeMs)}
              </span>
              <span className="text-xs text-gray-400">/</span>
              <span className="font-mono text-xs text-gray-500 dark:text-gray-400">
                {formatMs(durationMs)}
              </span>
            </div>
            <span className="text-[11px] text-gray-400 flex items-center gap-1">
              <AudioIcon className="text-brand-500" />
              <span>Synced ASR Audio Channel</span>
            </span>
          </div>
        </div>

        {/* Speed Controls */}
        <div className="flex items-center gap-1.5">
          {[1.0, 1.25, 1.5].map((speed) => (
            <button
              key={speed}
              type="button"
              onClick={() => setPlaybackSpeed(speed)}
              className={`rounded-lg px-2 py-1 text-xs font-semibold transition-colors ${
                playbackSpeed === speed
                  ? "bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-300 border border-brand-200 dark:border-brand-500/30"
                  : "text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
              }`}
            >
              {speed}x
            </button>
          ))}
        </div>
      </div>

      {/* Progress Bar & Scrub Timeline */}
      <div className="mt-3">
        <input
          type="range"
          min={0}
          max={durationMs}
          value={currentTimeMs}
          onChange={(e) => onSeek(Number(e.target.value))}
          className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 accent-brand-500 dark:bg-gray-800"
        />
        <div className="mt-1 flex justify-between text-[10px] text-gray-400 font-mono">
          <span>00:00</span>
          <span>Timeline synchronized with verbatim quotes</span>
          <span>{formatMs(durationMs)}</span>
        </div>
      </div>
    </div>
  );
}
