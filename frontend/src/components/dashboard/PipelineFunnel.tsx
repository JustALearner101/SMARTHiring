"use client";

import React from "react";
import type { PipelineStage } from "@/services/dashboardService";

interface PipelineFunnelProps {
  stages: PipelineStage[];
}

export function PipelineFunnel({ stages }: PipelineFunnelProps) {
  const total = stages.reduce((sum, s) => sum + s.count, 0);

  return (
    <div className="h-full rounded-2xl border border-gray-200 bg-white p-5 md:p-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
      <div className="flex items-center justify-between pb-4 border-b border-gray-100 dark:border-gray-800">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Hiring Pipeline
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            Distribution of candidates across all stages
          </p>
        </div>
        <span className="rounded-lg bg-gray-100 px-2.5 py-1 text-xs font-semibold text-gray-700 dark:bg-gray-800 dark:text-gray-300">
          Total: {total}
        </span>
      </div>

      <div className="mt-5 space-y-3.5">
        {stages.map((stage) => {
          const percentage = total > 0 ? Math.round((stage.count / total) * 100) : 0;
          return (
            <div key={stage.status} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-gray-700 dark:text-gray-300">
                  {stage.label}
                </span>
                <span className="text-gray-500 dark:text-gray-400">
                  {stage.count} ({percentage}%)
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-gray-100 dark:bg-gray-800">
                <div
                  className="h-full rounded-full transition-all duration-500 ease-out"
                  style={{
                    width: `${Math.max(percentage, stage.count > 0 ? 4 : 0)}%`,
                    backgroundColor: stage.color,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

