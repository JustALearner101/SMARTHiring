"use client";

import React from "react";
import { QuickReplyPreset, QuickPresetType } from "@/types/simulator";
import { quickReplyPresets } from "@/data/mockSimulatorData";
import { BoltIcon, CheckLineIcon, TimeIcon, AlertIcon, LockIcon } from "@/icons";

interface WhatsAppQuickBarProps {
  onSelectPreset: (preset: QuickReplyPreset) => void;
  disabled?: boolean;
}

export default function WhatsAppQuickBar({
  onSelectPreset,
  disabled = false,
}: WhatsAppQuickBarProps) {
  const getIcon = (type: QuickPresetType) => {
    switch (type) {
      case "confirm":
        return <CheckLineIcon className="text-success-600 dark:text-success-400" />;
      case "reschedule":
        return <TimeIcon className="text-warning-600 dark:text-warning-400" />;
      case "friday_conflict":
        return <AlertIcon className="text-info-600 dark:text-info-400" />;
      case "prompt_injection":
        return <LockIcon className="text-error-600 dark:text-error-400" />;
    }
  };

  const getBadgeStyle = (variant: string) => {
    switch (variant) {
      case "success":
        return "bg-success-50 text-success-700 border-success-200 hover:bg-success-100 dark:bg-success-500/10 dark:text-success-300 dark:border-success-500/30";
      case "warning":
        return "bg-warning-50 text-warning-700 border-warning-200 hover:bg-warning-100 dark:bg-warning-500/10 dark:text-warning-300 dark:border-warning-500/30";
      case "danger":
        return "bg-error-50 text-error-700 border-error-200 hover:bg-error-100 dark:bg-error-500/10 dark:text-error-300 dark:border-error-500/30";
      case "info":
      default:
        return "bg-brand-50 text-brand-700 border-brand-200 hover:bg-brand-100 dark:bg-brand-500/10 dark:text-brand-300 dark:border-brand-500/30";
    }
  };

  return (
    <div className="border-t border-gray-200 bg-gray-50/90 px-4 py-2.5 dark:border-gray-800 dark:bg-gray-900/90">
      <div className="mb-1.5 flex items-center justify-between">
        <span className="flex items-center gap-1.5 text-xs font-semibold text-gray-700 dark:text-gray-300">
          <BoltIcon className="text-brand-500" />
          <span>Quick Demo Reply Chips (90s Judge Presets):</span>
        </span>
        <span className="text-[11px] text-gray-500 dark:text-gray-400">
          Click chip to auto-send reply
        </span>
      </div>

      <div className="flex flex-wrap gap-2">
        {quickReplyPresets.map((preset) => (
          <button
            key={preset.id}
            type="button"
            disabled={disabled}
            onClick={() => onSelectPreset(preset)}
            className={`group inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-all shadow-2xs ${getBadgeStyle(
              preset.badge_variant
            )} disabled:opacity-50 disabled:cursor-not-allowed`}
            title={preset.description}
          >
            {getIcon(preset.preset_type)}
            <span>{preset.label}</span>
            <span className="rounded bg-white/60 px-1 py-0.2 text-[10px] font-semibold uppercase opacity-80 group-hover:opacity-100 dark:bg-black/40">
              {preset.badge}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
