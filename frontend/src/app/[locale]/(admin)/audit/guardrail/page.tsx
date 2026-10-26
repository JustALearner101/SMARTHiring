"use client";

import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import Badge from "@/components/ui/badge/Badge";
import { listAuditLogs } from "@/services/auditService";
import { listSimulatorNotifications } from "@/services/simulatorService";
import type { AuditEvent } from "@/types/orchestration";
import type { SimulatorNotification } from "@/types/simulator";
import { useEffect, useMemo, useState } from "react";

const GUARDRAIL_PATTERN = /GUARDRAIL|INJECTION|SECURITY|BLOCKED/i;

interface GuardrailAlert {
  id: string;
  timestamp: string;
  title: string;
  detail: string;
  source: string;
  isBlocked: boolean;
}

/** Backend stores an ISO string; format as "HH:MM:SS". */
const formatTimestamp = (value: string): string => {
  if (!value) return "--:--:--";
  const isoTime = /T(\d{2}:\d{2}:\d{2})/.exec(value);
  if (isoTime) return isoTime[1];
  return value;
};

const deriveAlerts = (
  events: AuditEvent[],
  notifications: SimulatorNotification[]
): GuardrailAlert[] => {
  const fromNotifications: GuardrailAlert[] = notifications
    .filter((notification) => notification.type === "guardrail_blocked")
    .map((notification) => ({
      id: `notif-${notification.id}`,
      timestamp: notification.timestamp,
      title: notification.title,
      detail: notification.message,
      source: "WhatsApp Simulator",
      isBlocked: true,
    }));

  const fromAudit: GuardrailAlert[] = events
    .filter((event) =>
      GUARDRAIL_PATTERN.test(
        `${event.event_type} ${event.title} ${event.description}`
      )
    )
    .map((event) => ({
      id: `audit-${event.id}`,
      timestamp: event.timestamp,
      title: event.title,
      detail: event.description,
      source: event.actor,
      isBlocked: event.status_badge === "error" || event.status_badge === "warning",
    }));

  return [...fromNotifications, ...fromAudit];
};

export default function GuardrailAlertsPage() {
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [notifications, setNotifications] = useState<SimulatorNotification[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isActive = true;

    const loadGuardrails = async () => {
      try {
        const [logs, notifs] = await Promise.all([
          listAuditLogs({ page_size: 50 }),
          listSimulatorNotifications(),
        ]);

        if (!isActive) return;

        if (logs && Array.isArray(logs.items)) setAuditEvents(logs.items);
        if (Array.isArray(notifs)) setNotifications(notifs);
      } catch (error) {
        console.error("Failed to fetch guardrail alerts:", error);
      } finally {
        if (isActive) setIsLoading(false);
      }
    };

    void loadGuardrails();

    return () => {
      isActive = false;
    };
  }, []);

  const alerts = useMemo(
    () => deriveAlerts(auditEvents, notifications),
    [auditEvents, notifications]
  );

  const blockedCount = alerts.filter((alert) => alert.isBlocked).length;

  return (
    <div>
      <PageBreadcrumb pageTitle="Guardrail & Injection Alerts" />
      <div className="rounded-2xl border border-gray-200 bg-white p-5 xl:p-7 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
        <div className="flex items-center justify-between border-b border-gray-100 pb-4 dark:border-gray-800">
          <div>
            <h3 className="text-theme-xl font-semibold text-gray-800 dark:text-white/90">
              Prompt Injection & Security Guardrails
            </h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Monitoring pertahanan keamanan AI terhadap serangan *prompt injection* pada CV pelamar, dokumen meeting, dan balasan chat.
            </p>
          </div>
          <span className="inline-flex items-center rounded-full bg-error-50 px-3 py-1 text-xs font-medium text-error-600 dark:bg-error-500/15 dark:text-error-400">
            Security Scanner
          </span>
        </div>

        <div className="mt-6 flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 p-8 text-center dark:border-gray-800">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-error-50 text-error-500 dark:bg-error-500/10">
            🚨
          </div>
          <h4 className="mt-3 text-base font-medium text-gray-800 dark:text-white/90">
            Quarantined Instructions & Security Flags
          </h4>
          <p className="mt-1 max-w-md text-xs text-gray-500 dark:text-gray-400">
            Daftar flag instruksi tertanam (`tblt_flag.vflag_type = EMBEDDED_INSTRUCTION`) yang berhasil diblokir sebelum masuk ke model perencana (Planner).
          </p>
        </div>

        <div className="mt-6">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-100 pb-3 dark:border-gray-800">
            <div>
              <h4 className="text-sm font-semibold text-gray-800 dark:text-white/90">
                Guardrail Alert Stream
              </h4>
              <p className="mt-0.5 text-[11px] text-gray-500 dark:text-gray-400">
                Turunan dari event audit guardrail dan notifikasi simulator WhatsApp.
              </p>
            </div>
            <div className="flex items-center gap-2 font-mono text-[10px]">
              <span className="rounded-md bg-gray-100 px-2 py-0.5 text-gray-600 dark:bg-gray-800 dark:text-gray-300">
                {isLoading ? "Syncing..." : `${alerts.length} Alerts`}
              </span>
              <span className="rounded-md bg-error-50 px-2 py-0.5 font-semibold text-error-600 dark:bg-error-500/15 dark:text-error-400">
                {blockedCount} Blocked
              </span>
            </div>
          </div>

          {alerts.length === 0 ? (
            <div className="mt-4 rounded-xl border border-dashed border-gray-200 p-6 text-center dark:border-gray-800">
              <p className="text-xs font-medium text-gray-700 dark:text-gray-300">
                {isLoading ? "Memuat alert guardrail dari database..." : "Tidak ada alert guardrail"}
              </p>
              <p className="mt-1 text-[11px] text-gray-500 dark:text-gray-400">
                Scanner belum mencatat instruksi tertanam maupun upaya *prompt injection*.
              </p>
            </div>
          ) : (
            <ul className="mt-1 divide-y divide-gray-100 dark:divide-gray-800">
              {alerts.map((alert) => (
                <li
                  key={alert.id}
                  className="flex flex-col gap-2 py-3 sm:flex-row sm:items-start sm:justify-between"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <time className="font-mono text-[10px] text-gray-400">
                        {formatTimestamp(alert.timestamp)}
                      </time>
                      <span className="text-xs font-semibold text-gray-800 dark:text-white/90">
                        {alert.title}
                      </span>
                    </div>
                    <p className="mt-1 text-[11px] leading-normal text-gray-500 dark:text-gray-400">
                      {alert.detail}
                    </p>
                    <p className="mt-1 text-[10px] text-gray-400">
                      Source:{" "}
                      <strong className="font-medium text-gray-700 dark:text-gray-300">
                        {alert.source}
                      </strong>
                    </p>
                  </div>
                  <div className="shrink-0 sm:ps-4">
                    <Badge size="sm" color={alert.isBlocked ? "error" : "success"}>
                      {alert.isBlocked ? "BLOCKED" : "PASSED"}
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
