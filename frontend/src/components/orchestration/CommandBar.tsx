"use client";

import Button from "@/components/ui/button/Button";
import { presetScenarios } from "@/data/mockOrchestrationData";
import { BoltIcon, ShootingStarIcon } from "@/icons";
import { PresetScenario } from "@/types/orchestration";
import React, { useState } from "react";

interface CommandBarProps {
  onExecuteCommand: (prompt: string, scenarioId?: string) => void;
  isProcessing: boolean;
  activeCandidateName?: string;
}

export default function CommandBar({
  onExecuteCommand,
  isProcessing,
  activeCandidateName,
}: CommandBarProps) {
  const [commandText, setCommandText] = useState(
    activeCandidateName
      ? `Schedule ${activeCandidateName}'s interview with Mr. Budi for next week`
      : "Schedule Rina Kusuma's interview with Mr. Budi for next week"
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
            <ShootingStarIcon/>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
              Autonomous Scheduling Command Bar
            </h3>
            <p className="text-[11px] text-gray-500 dark:text-gray-400">
              Type a natural language instruction or click the quick scenario button to test the AI's accountability.            </p>
          </div>
        </div>
        <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-50 px-2.5 py-0.5 text-[10px] font-mono font-semibold text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
          <span className="h-1.5 w-1.5 rounded-full bg-brand-500 animate-pulse"></span>
          LangGraph Ready
        </span>
      </div>

      {/* Main Input Form */}
      <form onSubmit={handleSubmit} className="mt-4">
        <div className="relative flex items-center">
          <div className="pointer-events-none absolute inset-y-0 start-0 flex items-center ps-4 text-brand-500">
            <BoltIcon/>
          </div>
          <input
            type="text"
            className="w-full rounded-xl border border-gray-200 bg-gray-50/60 ps-12 pe-32 py-3.5 text-xs text-gray-900 placeholder-gray-400 focus:border-brand-500 focus:bg-white focus:outline-hidden focus:ring-3 focus:ring-brand-500/15 dark:border-gray-800 dark:bg-gray-800/50 dark:text-white dark:placeholder-gray-500 transition-all font-medium"
            placeholder="Example: Schedule Rina Kusuma's interview with Mr. Budi for next week..."
            value={commandText}
            onChange={(e) => setCommandText(e.target.value)}
            disabled={isProcessing}
          />
          <div className="absolute inset-y-0 end-2 flex items-center">
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={isProcessing}
              startIcon={<ShootingStarIcon className="text-white" />}
            >
              AI Orchestration
            </Button>
          </div>
        </div>
      </form>

      {/* Preset Scenarios for Hackathon Judges */}
      <div className="mt-4 pt-3 border-t border-gray-100 dark:border-gray-800">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            Quick Test Scenarios (1-Click Demo)
          </span>
          <span className="text-[10px] text-gray-400">
            Click one of the scenarios for direct testing
          </span>
        </div>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {presetScenarios.map((sc) => (
            <button
              key={sc.id}
              type="button"
              disabled={isProcessing}
              onClick={() => handleSelectScenario(sc)}
              className="flex flex-col text-start rounded-xl border border-gray-200/90 bg-white p-2.5 hover:border-brand-400 hover:bg-brand-50/40 dark:border-gray-800 dark:bg-gray-800/40 dark:hover:border-brand-500/30 dark:hover:bg-brand-500/10 transition-all group"
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-xs text-gray-800 group-hover:text-brand-600 dark:text-gray-200 dark:group-hover:text-brand-400 line-clamp-1">
                  {sc.label}
                </span>
                <span className="rounded-md bg-gray-100 px-1.5 py-0.5 text-[9px] font-mono text-gray-600 dark:bg-gray-700 dark:text-gray-300">
                  {sc.tag}
                </span>
              </div>
              <p className="mt-1 text-[10px] text-gray-500 dark:text-gray-400 line-clamp-2 leading-relaxed">
                {sc.description}
              </p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
