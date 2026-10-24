"use client";

import React, { useEffect, useState } from "react";

interface TimezoneMatrixHeaderProps {
  selectedTimezone: "WIB" | "WITA" | "WIT";
  onSelectTimezone: (tz: "WIB" | "WITA" | "WIT") => void;
}

export default function TimezoneMatrixHeader({
  selectedTimezone,
  onSelectTimezone,
}: TimezoneMatrixHeaderProps) {
  const [currentTime, setCurrentTime] = useState<Date>(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Compute local times
  const getTzTime = (offsetHours: number) => {
    const utc = currentTime.getTime() + currentTime.getTimezoneOffset() * 60000;
    const targetTime = new Date(utc + 3600000 * offsetHours);
    return targetTime.toLocaleTimeString("id-ID", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  const zones: {
    code: "WIB" | "WITA" | "WIT";
    label: string;
    sublabel: string;
    offset: number;
    utcStr: string;
  }[] = [
    {
      code: "WIB",
      label: "WIB (Western)",
      sublabel: "Jakarta, Surabaya, Medan",
      offset: 7,
      utcStr: "UTC+7",
    },
    {
      code: "WITA",
      label: "WITA (Central)",
      sublabel: "Denpasar, Makassar, Balikpapan",
      offset: 8,
      utcStr: "UTC+8",
    },
    {
      code: "WIT",
      label: "WIT (Eastern)",
      sublabel: "Jayapura, Ambon, Sorong",
      offset: 9,
      utcStr: "UTC+9",
    },
  ];

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-gray-900 dark:text-white">
              Tri-Zone Synchronizer (WIB / WITA / WIT)
            </h3>
            <span className="rounded bg-brand-50 px-2 py-0.5 font-mono text-[10px] font-bold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
              PERMISSIONS
            </span>
          </div>
          <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
            AI secara otomatis mengonversi jam kalender interviewer dan kandidat antar zona waktu Indonesia tanpa kebingungan.
          </p>
        </div>

        {/* 3 Zone Cards */}
        <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-3">
          {zones.map((z) => {
            const isSelected = selectedTimezone === z.code;
            return (
              <button
                key={z.code}
                onClick={() => onSelectTimezone(z.code)}
                className={`flex flex-col items-start rounded-xl border p-3 text-start transition-all ${
                  isSelected
                    ? "border-brand-500 bg-brand-50/50 dark:border-brand-500 dark:bg-brand-500/10 ring-2 ring-brand-500/20"
                    : "border-gray-200 bg-gray-50/50 hover:border-gray-300 dark:border-gray-800 dark:bg-gray-800/40"
                }`}
              >
                <div className="flex w-full items-center justify-between">
                  <span
                    className={`font-mono text-xs font-bold ${
                      isSelected
                        ? "text-brand-700 dark:text-brand-400"
                        : "text-gray-800 dark:text-gray-200"
                    }`}
                  >
                    {z.label}
                  </span>
                  <span className="rounded bg-white px-1.5 py-0.5 font-mono text-[10px] font-semibold text-gray-500 dark:bg-gray-800 dark:text-gray-400">
                    {z.utcStr}
                  </span>
                </div>
                <div className="mt-2 flex items-baseline gap-1.5">
                  <span className="font-mono text-lg font-bold text-gray-900 dark:text-white">
                    {getTzTime(z.offset)}
                  </span>
                </div>
                <span className="mt-1 text-[10px] text-gray-400 truncate max-w-full">
                  {z.sublabel}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
