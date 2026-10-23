"use client";

import Button from "@/components/ui/button/Button";
import { BoltIcon, CloseIcon, TimeIcon } from "@/icons";
import React, { useEffect, useState } from "react";

interface UndoBufferBannerProps {
  initialSeconds?: number;
  onUndo: () => void;
  onDispatchImmediately: () => void;
}

export default function UndoBufferBanner({
  initialSeconds = 60,
  onUndo,
  onDispatchImmediately,
}: UndoBufferBannerProps) {
  const [secondsLeft, setSecondsLeft] = useState(initialSeconds);

  useEffect(() => {
    if (secondsLeft <= 0) {
      onDispatchImmediately();
      return;
    }

    const timer = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          onDispatchImmediately();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [secondsLeft, onDispatchImmediately]);

  const progressPercent = (secondsLeft / initialSeconds) * 100;

  return (
    <div className="rounded-2xl border-2 border-warning-400 bg-gradient-to-r from-warning-500/10 via-brand-500/10 to-transparent p-5 xl:p-6 dark:border-warning-500/40 dark:bg-gray-900 shadow-theme-md transition-all animate-in fade-in slide-in-from-top-2">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3.5">
          <div className="relative flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-warning-500 text-white shadow-theme-xs">
            <TimeIcon className="animate-spin duration-3000" />
            <span className="absolute -bottom-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-brand-600 text-[10px] font-bold text-white font-mono">
              60s
            </span>
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-gray-900 dark:text-white">
                Grace Period: 60-Second Undo Buffer Active
              </h3>
              <span className="rounded-md bg-warning-500 px-2 py-0.5 text-[10px] font-mono font-bold text-white shadow-2xs">
                {String(Math.floor(secondsLeft / 60)).padStart(2, "0")}:
                {String(secondsLeft % 60).padStart(2, "0")} Tersisa
              </span>
            </div>
            <p className="mt-0.5 text-xs text-gray-600 dark:text-gray-300">
              The action plan has been approved. WhatsApp messages, emails, and calendar events are held for 60 seconds before being sent to an external server. You can cancel this now.
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5 shrink-0 justify-end">
          <Button
            variant="outline"
            size="md"
            onClick={onUndo}
            startIcon={<CloseIcon className="text-error-500" />}
            className="border-error-300 text-error-600 hover:bg-error-50 hover:border-error-400 dark:border-error-500/30 dark:hover:bg-error-500/15"
          >
            Undo Action Plan
          </Button>

          <Button
            variant="primary"
            size="md"
            onClick={onDispatchImmediately}
            startIcon={<BoltIcon className="text-white" />}
          >
            Send Now (Skip 60s)
          </Button>
        </div>
      </div>

      {/* Countdown Progress Bar */}
      <div className="mt-4">
        <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-800">
          <div
            className="h-full bg-gradient-to-r from-warning-500 to-brand-500 transition-all duration-1000 ease-linear rounded-full"
            style={{ width: `${progressPercent}%` }}
          ></div>
        </div>
        <div className="mt-1 flex justify-between text-[10px] font-mono text-gray-400">
          <span>60-Second Undo Buffer Active</span>
          <span>{secondsLeft}s remaining before execution</span>
        </div>
      </div>
    </div>
  );
}
