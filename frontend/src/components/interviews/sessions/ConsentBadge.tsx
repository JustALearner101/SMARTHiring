"use client";

import React from "react";
import { ConsentStatus } from "@/types/interview";
import { CheckCircleIcon, AlertIcon, CloseIcon } from "@/icons";

interface ConsentBadgeProps {
  status: ConsentStatus;
}

export default function ConsentBadge({ status }: ConsentBadgeProps) {
  switch (status) {
    case "GRANTED":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-success-50 px-2.5 py-0.5 text-xs font-semibold text-success-700 dark:bg-success-500/15 dark:text-success-400 border border-success-200 dark:border-success-500/30">
          <CheckCircleIcon/>
          <span>GRANTED</span>
        </span>
      );
    case "NOT_GRANTED":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-warning-50 px-2.5 py-0.5 text-xs font-semibold text-warning-700 dark:bg-warning-500/15 dark:text-warning-400 border border-warning-200 dark:border-warning-500/30">
          <AlertIcon/>
          <span>NOT GRANTED</span>
        </span>
      );
    case "WITHDRAWN":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-error-50 px-2.5 py-0.5 text-xs font-semibold text-error-700 dark:bg-error-500/15 dark:text-error-400 border border-error-200 dark:border-error-500/30">
          <CloseIcon/>
          <span>WITHDRAWN</span>
        </span>
      );
  }
}
