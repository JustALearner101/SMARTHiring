"use client";

import Button from "@/components/ui/button/Button";
import { AlertIcon, ShootingStarIcon } from "@/icons";
import { PlanStatus } from "@/types/orchestration";
import React from "react";

interface OrchestrationPipelineLoaderProps {
  status: Extract<PlanStatus, "ANALYZING" | "CLARIFICATION_NEEDED">;
  commandPrompt: string;
  onReopenDisambiguation?: () => void;
  onCancel?: () => void;
}

const PIPELINE_STEPS = [
  {
    step: "1",
    title: "Guardrail & Prompt Injection Scan",
    desc: "Scan instructions for adversarial manipulation patterns & permission boundaries.",
  },
  {
    step: "2",
    title: "Context, Contact & Calendar Retriever",
    desc: "Retrieve candidate profiles, contact directories, calendar schedules, & WIB/WITA/WIT time zones.",
  },
  {
    step: "3",
    title: "Planner & Triage Agent",
    desc: "Compose optimal slots, provide source citations [SOURCES], and draft Email/WhatsApp messages.",
  },
  {
    step: "4",
    title: "Secondary Validator Agent",
    desc: "Verify compliance with working hours (09:00–17:00), block time for Friday prayers, and allow a 15-minute buffer.",
  },
] as const;

export default function OrchestrationPipelineLoader({
  status,
  commandPrompt,
  onReopenDisambiguation,
  onCancel,
}: OrchestrationPipelineLoaderProps) {
  if (status === "CLARIFICATION_NEEDED") {
    return (
      <div className="rounded-2xl border-2 border-warning-300 bg-warning-50/50 p-6 dark:border-warning-500/40 dark:bg-warning-500/10 shadow-theme-xs">
        <div className="flex items-start gap-3.5">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-warning-500 text-white shadow-theme-xs">
            <AlertIcon />
          </div>
          <div className="flex-1 text-start">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-base font-bold text-gray-900 dark:text-white">
                Human Clarification Required (Contact Ambiguity)
              </h3>
              <span className="rounded-full bg-warning-100 px-2.5 py-0.5 font-mono text-[10px] font-bold text-warning-800 dark:bg-warning-500/20 dark:text-warning-300">
                LIMITS
              </span>
            </div>
            <p className="mt-1.5 text-xs leading-relaxed text-gray-600 dark:text-gray-300">
              AI detected more than one internal contact matching your command and stopped according to the <strong>LIMITS</strong> accountability rule. Please select the intended interviewer profile to continue composing the action plan.
            </p>
            <div className="mt-4 flex flex-wrap items-center gap-2.5">
              {onReopenDisambiguation && (
                <Button variant="primary" size="sm" onClick={onReopenDisambiguation}>
                  Choose Contact Profile
                </Button>
              )}
              {onCancel && (
                <Button variant="outline" size="sm" onClick={onCancel}>
                  Cancel Orchestration
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-brand-200 bg-white p-6 xl:p-7 dark:border-brand-500/30 dark:bg-gray-900 shadow-theme-xs">
      <div className="flex items-center justify-between border-b border-gray-100 pb-4 dark:border-gray-800">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-500 text-white shadow-theme-xs animate-pulse">
            <ShootingStarIcon />
          </div>
          <div className="text-start">
            <h3 className="text-base font-bold text-gray-900 dark:text-white">
              Executing LangGraph Orchestration Pipeline...
            </h3>
            <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400 line-clamp-1">
              Prompt:{" "}
              <span className="font-medium text-gray-700 dark:text-gray-300">
                &ldquo;{commandPrompt}&rdquo;
              </span>
            </p>
          </div>
        </div>
        <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-50 px-2.5 py-1 font-mono text-[10px] font-semibold text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
          <span className="h-2 w-2 rounded-full bg-brand-500 animate-ping" />
          RUNNING
        </span>
      </div>

      <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2">
        {PIPELINE_STEPS.map((item) => (
          <div
            key={item.step}
            className="rounded-xl border border-gray-100 bg-gray-50/80 p-3.5 text-start dark:border-gray-800 dark:bg-gray-800/40 animate-pulse"
          >
            <div className="flex items-center gap-2">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-500 text-[11px] font-bold text-white">
                {item.step}
              </span>
              <h4 className="text-xs font-bold text-gray-800 dark:text-white">
                {item.title}
              </h4>
            </div>
            <p className="mt-1.5 text-[11px] leading-relaxed text-gray-500 dark:text-gray-400">
              {item.desc}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

