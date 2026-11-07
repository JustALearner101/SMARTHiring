"use client";

import Button from "@/components/ui/button/Button";
import { BoltIcon, ShootingStarIcon } from "@/icons";
import { PresetScenario } from "@/types/orchestration";
import React, { useState } from "react";

interface CommandBarProps {
  onExecuteCommand: (prompt: string, scenarioId?: string) => void;
  isProcessing: boolean;
  activeCandidateName?: string;
  initialCommand?: string;
  scenarios: PresetScenario[];
}

export default function CommandBar({
  onExecuteCommand,
  isProcessing,
  activeCandidateName,
  initialCommand,
  scenarios,
}: CommandBarProps) {
  const [commandText, setCommandText] = useState(
    initialCommand ||
      (activeCandidateName
        ? `Schedule ${activeCandidateName}'s interview with Mr. Budi for next week`
        : "Schedule Rina Kusuma's interview with Mr. Budi for next week")
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!commandText.trim() || isProcessing) return;
    onExecuteCommand(commandText);
  };

  const handleSelectScenario = (scenario: PresetScenario) => {
    setCommandText(scenario.prompt);
    onExecuteCommand(scenario.prompt, scenario.id);
  };

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-5 xl:p-6 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between border-b border-gray-100 pb-3 dark:border-gray-800">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-500 text-white shadow-theme-xs">
            <ShootingStarIcon />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
              Autonomous Scheduling Command Bar
            </h3>
            <p className="text-[11px] text-gray-500 dark:text-gray-400">
              Type a natural language instruction or click the quick scenario button to test the AI&apos;s accountability.
            </p>
          </div>
        </div>
        <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-50 px-2.5 py-0.5 text-[10px] font-mono font-semibold text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
          <span className="h-1.5 w-1.5 rounded-full bg-brand-500 animate-pulse"></span>
          LangGraph Ready
        </span>
      </div>

      {/* Main Input Form */}
      <form onSubmit={handleSubmit} className="mt-4">
        <div className="flex flex-col gap-2.5 sm:block sm:relative">
          <div className="relative flex items-center">
            <div className="pointer-events-none absolute inset-y-0 start-0 flex items-center ps-4 text-brand-500">
              <BoltIcon />
            </div>
            <input
              type="text"
              className="w-full rounded-xl border border-gray-200 bg-gray-50/60 ps-12 pe-4 sm:pe-36 py-3.5 text-xs text-gray-900 placeholder-gray-400 focus:border-brand-500 focus:bg-white focus:outline-hidden focus:ring-3 focus:ring-brand-500/15 dark:border-gray-800 dark:bg-gray-800/50 dark:text-white dark:placeholder-gray-500 transition-all font-medium"
              placeholder="Example: Schedule Rina Kusuma's interview with Mr. Budi for next week..."
              value={commandText}
              onChange={(e) => setCommandText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
              disabled={isProcessing}
            />
          </div>
          <div className="w-full sm:absolute sm:inset-y-0 sm:end-2 sm:flex sm:w-auto sm:items-center">
            <Button
              type="button"
              onClick={(e) => {
                e.preventDefault();
                handleSubmit(e);
              }}
              variant="primary"
              size="sm"
              className="w-full justify-center sm:w-auto"
              isLoading={isProcessing}
              disabled={!commandText.trim() || isProcessing}
              startIcon={<ShootingStarIcon className="text-white" />}
            >
              AI Orchestration
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
