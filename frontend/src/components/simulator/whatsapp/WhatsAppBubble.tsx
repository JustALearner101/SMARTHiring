"use client";

import React from "react";
import { SimulatedWhatsAppMessage } from "@/types/simulator";
import { CheckLineIcon, AlertIcon, LockIcon } from "@/icons";

interface WhatsAppBubbleProps {
  message: SimulatedWhatsAppMessage;
}

export default function WhatsAppBubble({ message }: WhatsAppBubbleProps) {
  const isCandidate = message.sender === "candidate";

  return (
    <div
      className={`flex flex-col mb-3 max-w-[85%] md:max-w-[70%] ${
        isCandidate ? "ml-auto items-end" : "mr-auto items-start"
      }`}
    >
      <div
        className={`relative rounded-2xl px-4 py-2.5 text-sm shadow-xs ${
          isCandidate
            ? message.is_guardrail_flagged
              ? "rounded-tr-none bg-error-50 text-error-900 border-2 border-error-500 dark:bg-error-950/40 dark:text-error-100 dark:border-error-500"
              : "rounded-tr-none bg-emerald-100 text-gray-900 border border-emerald-200 dark:bg-emerald-900/50 dark:text-emerald-50 dark:border-emerald-700/50"
            : "rounded-tl-none bg-white text-gray-800 border border-gray-200 dark:bg-gray-800 dark:text-gray-100 dark:border-gray-700"
        }`}
      >
        {/* Sender Name for bot */}
        {!isCandidate && (
          <div className="mb-1 flex items-center gap-1.5 text-xs font-semibold text-emerald-700 dark:text-emerald-400">
            <span>{message.sender_name}</span>
            <span className="rounded bg-emerald-100 px-1.5 py-0.2 text-[10px] text-emerald-800 dark:bg-emerald-800/50 dark:text-emerald-200">
              Verified Bot
            </span>
          </div>
        )}

        {/* Flagged warning badge */}
        {message.is_guardrail_flagged && (
          <div className="mb-1.5 flex items-center gap-1 rounded bg-error-100 px-2 py-0.5 text-xs font-semibold text-error-800 dark:bg-error-900 dark:text-error-200">
            <LockIcon className="shrink-0 text-error-600 dark:text-error-300" />
            <span>Intercepted by Guardrail Scanner</span>
          </div>
        )}

        {/* Message Content with line breaks */}
        <div className="whitespace-pre-wrap leading-relaxed text-xs md:text-sm">
          {message.text}
        </div>

        {/* Timestamp and Delivery checkmarks */}
        <div className="mt-1 flex items-center justify-end gap-1 text-[10px] text-gray-400 dark:text-gray-400">
          <span>{message.timestamp}</span>
          {isCandidate && (
            <span
              className={`flex items-center ${
                message.is_guardrail_flagged
                  ? "text-error-500"
                  : "text-brand-500 dark:text-brand-400"
              }`}
              title={message.status}
            >
              <CheckLineIcon className="inline -mr-1" />
              <CheckLineIcon className="inline" />
            </span>
          )}
        </div>
      </div>

      {/* Sub-label explanation if flagged */}
      {message.is_guardrail_flagged && message.guardrail_reason && (
        <span className="mt-1 flex items-center gap-1 text-[11px] font-medium text-error-600 dark:text-error-400">
          <AlertIcon/>
          {message.guardrail_reason}
        </span>
      )}
    </div>
  );
}
