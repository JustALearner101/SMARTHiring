"use client";

import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import Badge from "@/components/ui/badge/Badge";
import { listAuditLogs } from "@/services/auditService";
import type { AuditEvent } from "@/types/orchestration";
import { useEffect, useState } from "react";

const badgeColor = (
  status: AuditEvent["status_badge"]
): "success" | "warning" | "error" | "info" => {
  switch (status) {
    case "success":
      return "success";
    case "warning":
      return "warning";
    case "error":
      return "error";
    default:
      return "info";
  }
};

/** Backend stores an ISO string; format as "HH:MM:SS". */
const formatTimestamp = (value: string): string => {
  if (!value) return "--:--:--";
  const isoTime = /T(\d{2}:\d{2}:\d{2})/.exec(value);
  if (isoTime) return isoTime[1];
  return value;
};

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isActive = true;

    const loadLogs = async () => {
      try {
        const page = await listAuditLogs({ page_size: 50 });
        if (isActive && Array.isArray(page?.items)) {
          setLogs(page.items);
        }
      } catch (error) {
        console.error("Failed to fetch audit logs:", error);
      } finally {
        if (isActive) setIsLoading(false);
      }
    };

    void loadLogs();

    return () => {
      isActive = false;
    };
  }, []);

  return (
    <div>
      <PageBreadcrumb pageTitle="Audit Logs (Hash Chain)" />
      <div className="rounded-2xl border border-gray-200 bg-white p-5 xl:p-7 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
        <div className="flex items-center justify-between border-b border-gray-100 pb-4 dark:border-gray-800">
          <div>
            <h3 className="text-theme-xl font-semibold text-gray-800 dark:text-white/90">
              Immutable Audit Logs & Hash Chain
            </h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Jejak audit kronologis tak-terubah (*append-only*): request masuk, deteksi guardrail, validasi sekunder, persetujuan HR, eksekusi, dan pembatalan (Undo).
            </p>
          </div>
          <span className="inline-flex items-center rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
            RECORD
          </span>
        </div>

        <div className="mt-6 flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 p-8 text-center dark:border-gray-800">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-brand-500 dark:bg-brand-500/10">
            🛡️
          </div>
          <h4 className="mt-3 text-base font-medium text-gray-800 dark:text-white/90">
            Cryptographic Hash-Chain Verification
          </h4>
          <p className="mt-1 max-w-md text-xs text-gray-500 dark:text-gray-400">
            Tabel jejak audit terenkripsi SHA-256 (`tblt_audit_log`) dengan verifikasi validitas rantai blok bukti integritas data akuntabilitas AI.
          </p>
        </div>

        <div className="mt-6">
          <div className="flex items-center justify-between border-b border-gray-100 pb-3 dark:border-gray-800">
            <div>
              <h4 className="text-sm font-semibold text-gray-800 dark:text-white/90">
                Audit Event Stream
              </h4>
              <p className="mt-0.5 text-[11px] text-gray-500 dark:text-gray-400">
                Setiap transisi node agen dicatat permanen pada ledger PostgreSQL.
              </p>
            </div>
            <span className="shrink-0 rounded-md bg-gray-100 px-2 py-0.5 font-mono text-[10px] text-gray-600 dark:bg-gray-800 dark:text-gray-300">
              {isLoading ? "Syncing..." : `${logs.length} Events`}
            </span>
          </div>

          {logs.length === 0 ? (
            <p className="mt-4 rounded-xl border border-dashed border-gray-200 p-6 text-center text-xs text-gray-500 dark:border-gray-800 dark:text-gray-400">
              {isLoading ? "Memuat jejak audit dari database..." : "Belum ada jejak audit yang tercatat."}
            </p>
          ) : (
            <ul className="mt-1 divide-y divide-gray-100 dark:divide-gray-800">
              {logs.map((event) => (
                <li
                  key={event.id}
                  className="flex flex-col gap-2 py-3 sm:flex-row sm:items-start sm:justify-between"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <time className="font-mono text-[10px] text-gray-400">
                        {formatTimestamp(event.timestamp)}
                      </time>
                      <span className="rounded border border-gray-200 px-1.5 py-0.5 font-mono text-[9px] font-semibold text-gray-600 dark:border-gray-700 dark:text-gray-300">
                        {event.event_type}
                      </span>
                      <span className="text-xs font-semibold text-gray-800 dark:text-white/90">
                        {event.title}
                      </span>
                    </div>
                    <p className="mt-1 text-[11px] leading-normal text-gray-500 dark:text-gray-400">
                      {event.description}
                    </p>
                    <p className="mt-1 text-[10px] text-gray-400">
                      Actor:{" "}
                      <strong className="font-medium text-gray-700 dark:text-gray-300">
                        {event.actor}
                      </strong>
                    </p>
                  </div>
                  <div className="shrink-0 sm:ps-4">
                    <Badge size="sm" color={badgeColor(event.status_badge)}>
                      {event.status_badge.toUpperCase()}
                    </Badge>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
