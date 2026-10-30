"use client";

import React, { useEffect, useRef, useState } from "react";


interface AudioWavePlayerProps {
  currentTimeMs: number;
  durationMs: number;
  isPlaying: boolean;
  audioStreamUrl?: string | null;
  onTogglePlay: () => void;
  onSeek: (ms: number) => void;
  onDurationChange?: (durationMs: number) => void;
  onTimeUpdate?: (currentMs: number) => void;
  onEnded?: () => void;
}

export default function AudioWavePlayer({
  currentTimeMs,
  durationMs,
  isPlaying,
  audioStreamUrl,
  onTogglePlay,
  onSeek,
  onDurationChange,
  onTimeUpdate,
  onEnded,
}: AudioWavePlayerProps) {
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1.0);
  const [audioError, setAudioError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  // Compute resolved stream URL with token query param if needed
  const resolvedAudioSrc = React.useMemo(() => {
    if (!audioStreamUrl) return "";
    let src = audioStreamUrl;
    if (src.startsWith("/")) {
      const apiBase = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1").replace(/\/api\/v1\/?$/, "");
      src = `${apiBase}${src}`;
    }
    const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
    if (token && !src.includes("token=")) {
      const sep = src.includes("?") ? "&" : "?";
      src = `${src}${sep}token=${encodeURIComponent(token)}`;
    }
    return src;
  }, [audioStreamUrl]);

  // Sync play / pause state
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !resolvedAudioSrc) return;

    if (isPlaying) {
      audio.play().catch((err) => {
        console.warn("Audio autoplay / play interrupted:", err);
      });
    } else {
      audio.pause();
    }
  }, [isPlaying, resolvedAudioSrc]);

  // Sync playback speed
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = playbackSpeed;
    }
  }, [playbackSpeed]);

  // Sync seek if drifted more than 1.5 seconds
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    const audioMs = Math.floor(audio.currentTime * 1000);
    if (Math.abs(audioMs - currentTimeMs) > 1500) {
      audio.currentTime = currentTimeMs / 1000;
    }
  }, [currentTimeMs]);

  const formatMs = (ms: number) => {
    const totalSeconds = Math.max(0, Math.floor(ms / 1000));
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
  };

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
      {/* Hidden Native Audio Element */}
      {resolvedAudioSrc && (
        <audio
          ref={audioRef}
          src={resolvedAudioSrc}
          preload="metadata"
          onLoadedMetadata={(e) => {
            setAudioError(null);
            const dur = Math.floor(e.currentTarget.duration * 1000);
            if (dur && !isNaN(dur) && dur > 0 && onDurationChange) {
              onDurationChange(dur);
            }
          }}
          onTimeUpdate={(e) => {
            const currentMs = Math.floor(e.currentTarget.currentTime * 1000);
            if (onTimeUpdate) {
              onTimeUpdate(currentMs);
            }
          }}
          onEnded={() => {
            if (onEnded) onEnded();
            else onTogglePlay();
          }}
          onError={() => {
            setAudioError("Streaming audio dari server offline atau format tidak didukung.");
          }}
        />
      )}

      <div className="flex items-center justify-between gap-3">
        {/* Play/Pause Button & Time */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onTogglePlay}
            className={`flex h-9.5 w-9.5 shrink-0 items-center justify-center rounded-xl transition-colors shadow-2xs ${
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
              <svg className="h-4 w-4 fill-current ms-0.5" viewBox="0 0 24 24">
                <polygon points="5,3 19,12 5,21" />
              </svg>
            )}
          </button>

          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-mono text-sm font-bold text-gray-900 dark:text-white">
                {formatMs(currentTimeMs)}
              </span>
              <span className="text-xs text-gray-400">/</span>
              <span className="font-mono text-xs text-gray-500 dark:text-gray-400">
                {formatMs(durationMs)}
              </span>
            </div>
            {audioError && (
              <span className="text-[11px] text-warning-600 dark:text-warning-400 block">
                Audio playback unavailable
              </span>
            )}
          </div>
        </div>

        {/* Speed Controls - Segmented */}
        <div className="inline-flex rounded-lg border border-gray-200 bg-gray-50 p-0.5 dark:border-gray-700 dark:bg-gray-800">
          {[1.0, 1.25, 1.5].map((speed) => (
            <button
              key={speed}
              type="button"
              onClick={() => setPlaybackSpeed(speed)}
              className={`rounded-md px-2 py-1 text-[11px] font-semibold transition-colors ${
                playbackSpeed === speed
                  ? "bg-white text-brand-600 shadow-2xs dark:bg-gray-700 dark:text-white"
                  : "text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
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
          max={Math.max(durationMs, 1000)}
          value={currentTimeMs}
          onChange={(e) => {
            const targetMs = Number(e.target.value);
            onSeek(targetMs);
            if (audioRef.current) {
              audioRef.current.currentTime = targetMs / 1000;
            }
          }}
          className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 accent-brand-500 dark:bg-gray-800"
        />
        <div className="mt-1 flex justify-between text-[10px] text-gray-400 font-mono">
          <span>00:00</span>
          <span>{formatMs(durationMs)}</span>
        </div>
      </div>
    </div>
  );
}
