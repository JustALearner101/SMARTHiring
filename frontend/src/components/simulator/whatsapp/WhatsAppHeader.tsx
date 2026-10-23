"use client";

import React from "react";
import { Link } from "@/i18n/navigation";
import { BoltIcon, TimeIcon, CheckCircleIcon } from "@/icons";

interface WhatsAppHeaderProps {
  candidateName: string;
  phoneNumber: string;
  position: string;
  isBotTyping: boolean;
  negotiationRound: number;
  onReset: () => void;
}

export default function WhatsAppHeader({
  candidateName,
  phoneNumber,
  position,
  isBotTyping,
  negotiationRound,
  onReset,
}: WhatsAppHeaderProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-200 bg-emerald-700 px-4 py-3 text-white dark:border-gray-800 dark:bg-emerald-800">
      <div className="flex items-center gap-3">
        <div className="relative flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-emerald-800 font-semibold text-white shadow-inner dark:bg-emerald-900 border border-emerald-500/30">
          RK
          <span className="absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-emerald-700 bg-success-400" />
        </div>

        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-medium text-white">{candidateName}</h3>
            <span className="rounded bg-emerald-900/60 px-2 py-0.5 text-[11px] font-medium text-emerald-100">
              {position}
            </span>
          </div>

          <p className="text-xs text-emerald-100/90 flex items-center gap-2">
            <span>{phoneNumber}</span>
            <span>&bull;</span>
            {isBotTyping ? (
              <span className="font-semibold text-warning-300 animate-pulse">
                SmartHiring Bot is typing...
              </span>
            ) : (
              <span className="flex items-center gap-1 text-emerald-200">
                <CheckCircleIcon/>
                Online &bull; WhatsApp Verified
              </span>
            )}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-900/70 px-3 py-1 text-xs font-semibold text-emerald-100 border border-emerald-500/40">
          Triage Round: {negotiationRound}/3
        </span>

        <button
          onClick={onReset}
          className="inline-flex items-center gap-1 rounded-lg bg-white/10 px-2.5 py-1.5 text-xs font-medium text-white transition-colors hover:bg-white/20"
          title="Reset conversation to initial state"
        >
          <TimeIcon/>
          <span>Reset</span>
        </button>

        <Link
          href="/orchestration/scheduling"
          className="inline-flex items-center gap-1 rounded-lg bg-white px-3 py-1.5 text-xs font-semibold text-emerald-800 shadow-sm transition-colors hover:bg-emerald-50"
        >
          <BoltIcon/>
          <span>AI Orchestrator</span>
        </Link>
      </div>
    </div>
  );
}
