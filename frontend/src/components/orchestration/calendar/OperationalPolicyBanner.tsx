"use client";

import React from "react";
import { AlertIcon, LockIcon } from "@/icons";
import Button from "@/components/ui/button/Button";

interface OperationalPolicyBannerProps {
  onOpenTester: () => void;
}

export default function OperationalPolicyBanner({
  onOpenTester,
}: OperationalPolicyBannerProps) {
  return (
    <div className="rounded-2xl border border-warning-200 bg-warning-50/60 p-4 shadow-theme-xs dark:border-warning-900/40 dark:bg-warning-500/10">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 text-warning-600 dark:text-warning-400">
            <AlertIcon />
          </div>
          <div>
            <h4 className="text-xs font-bold text-warning-900 dark:text-warning-200 flex items-center gap-2">
              <span>Operational Rule Guardrails Active</span>
              <span className="rounded bg-warning-200/60 px-1.5 py-0.5 font-mono text-[10px] font-bold text-warning-800 dark:bg-warning-800/60 dark:text-warning-300">
                Pilar PERMISSIONS
              </span>
            </h4>
            <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-warning-800 dark:text-warning-300">
              <span className="flex items-center gap-1">
                <span className="font-semibold">• Jam Kerja:</span> 09:00 - 17:00
              </span>
              <span className="flex items-center gap-1 font-semibold text-error-700 dark:text-error-400">
                <span>• Sholat Jumat:</span> 11:30 - 13:00 (Blocked)
              </span>
              <span className="flex items-center gap-1">
                <span className="font-semibold">• Buffer Antar-Interview:</span> Min. 15 Menit
              </span>
            </div>
          </div>
        </div>

        <Button
          size="sm"
          variant="outline"
          onClick={onOpenTester}
          startIcon={<LockIcon />}
          className="shrink-0 border-warning-400 bg-white text-warning-900 hover:bg-warning-100 dark:border-warning-700 dark:bg-gray-800 dark:text-warning-200"
        >
          Test Slot Conflict Engine
        </Button>
      </div>
    </div>
  );
}
