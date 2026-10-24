"use client";

import React from "react";
import { AlertIcon, CloseIcon, LockIcon } from "@/icons";
import { Link } from "@/i18n/navigation";

interface GuardrailAlertProps {
  payload: string;
  reason: string;
  timestamp: string;
  onDismiss: () => void;
}

export default function GuardrailAlert({
  payload,
  reason,
  timestamp,
  onDismiss,
}: GuardrailAlertProps) {
  return (
    <div className="relative mb-4 overflow-hidden rounded-xl border border-error-200 bg-error-50/90 p-4 shadow-sm dark:border-error-500/30 dark:bg-error-500/10">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-error-500 text-white shadow-sm">
          <AlertIcon/>
        </div>

        <div className="flex-1 pr-6">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 rounded bg-error-100 px-2 py-0.5 text-xs font-semibold uppercase tracking-wider text-error-700 dark:bg-error-500/20 dark:text-error-300">
              <LockIcon/>
              Guardrail Scanner Intercept
            </span>
            <span className="text-xs text-gray-500 dark:text-gray-400">{timestamp}</span>
          </div>

          <h4 className="mt-1 text-sm font-semibold text-error-800 dark:text-error-200">
            Adversarial Prompt Injection Blocked
          </h4>

          <p className="mt-1 text-xs text-error-700 dark:text-error-300">
            {reason}
          </p>

          <div className="mt-2 rounded-lg bg-white/80 p-2 font-mono text-xs text-gray-700 border border-error-200 dark:bg-gray-900/80 dark:border-error-500/30 dark:text-gray-300">
            <span className="text-error-600 font-semibold dark:text-error-400">Flagged Payload: </span>
            &quot;{payload}&quot;
          </div>

          <div className="mt-3 flex items-center gap-3">
            <Link
              href="/audit/guardrail"
              className="inline-flex items-center text-xs font-medium text-error-700 underline hover:text-error-800 dark:text-error-300"
            >
              View incident report in Security Guardrail &rarr;
            </Link>
            <button
              onClick={onDismiss}
              className="text-xs font-medium text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              Dismiss alert
            </button>
          </div>
        </div>

        <button
          onClick={onDismiss}
          className="absolute right-3 top-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          aria-label="Close alert"
        >
          <CloseIcon/>
        </button>
      </div>
    </div>
  );
}
