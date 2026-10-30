"use client";

import React from "react";
import { Link } from "@/i18n/navigation";
import { CalenderIcon, ArrowRightIcon } from "@/icons";
import Badge from "@/components/ui/badge/Badge";
import type { UpcomingInterview } from "@/services/dashboardService";

interface UpcomingInterviewsTableProps {
  interviews: UpcomingInterview[];
}

export function UpcomingInterviewsTable({ interviews }: UpcomingInterviewsTableProps) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-5 md:p-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
      <div className="flex items-center justify-between pb-4 border-b border-gray-100 dark:border-gray-800">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-400">
            <CalenderIcon/>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Upcoming Interviews (Next 7 Days)
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Confirmed interview schedule between candidates and interviewers
            </p>
          </div>
        </div>
        <Link
          href="/orchestration/calendar"
          className="inline-flex items-center gap-1 text-xs font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400"
        >
          View Calendar
          <ArrowRightIcon/>
        </Link>
      </div>

      {interviews.length === 0 ? (
        <div className="py-10 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            There are no scheduled interviews in the next 7 days.
          </p>
        </div>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-start">
            <thead>
              <tr className="border-b border-gray-100 dark:border-gray-800 text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                <th className="py-3 pe-4 text-start">Candidate</th>
                <th className="py-3 pe-4 text-start">Position</th>
                <th className="py-3 pe-4 text-start">Interviewer</th>
                <th className="py-3 pe-4 text-start">Time</th>
                <th className="py-3 text-start">Platform</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800 text-sm">
              {interviews.map((item) => (
                <tr
                  key={item.id}
                  className="hover:bg-gray-50/50 transition-colors dark:hover:bg-gray-800/50"
                >
                  <td className="py-3.5 pe-4">
                    <div className="font-semibold text-gray-900 dark:text-white">
                      {item.candidate_name}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 font-mono">
                      {item.candidate_code}
                    </div>
                  </td>
                  <td className="py-3.5 pe-4 text-gray-700 dark:text-gray-300 font-medium">
                    {item.position}
                  </td>
                  <td className="py-3.5 pe-4">
                    <div className="font-medium text-gray-900 dark:text-white">
                      {item.interviewer_name}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {item.interviewer_dept}
                    </div>
                  </td>
                  <td className="py-3.5 pe-4 text-gray-600 dark:text-gray-300">
                    {item.formatted_time}
                  </td>
                  <td className="py-3.5">
                    <Badge color="primary" size="sm">
                      {item.location_type}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

