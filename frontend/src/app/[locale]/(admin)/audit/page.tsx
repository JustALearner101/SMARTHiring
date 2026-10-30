"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import Badge from "@/components/ui/badge/Badge";
import { useAuth } from "@/context/AuthContext";
import { Link } from "@/i18n/navigation";
import {
  CheckCircleIcon,
  DocsIcon,
  LockIcon,
  ListIcon,
  ArrowRightIcon,
} from "@/icons";
import {
  getAuditStats,
  verifyHashChain,
  listAuditLogs,
  listSystemLogs,
  type AuditStats,
  type HashChainVerification,
  type SystemLog,
} from "@/services/auditService";
import type { AuditEvent } from "@/types/orchestration";
import TablePagination from "@/components/common/TablePagination";

type TabType = "ledger" | "systemLogs";

export default function AuditSecurityPage() {
  const { role, isLoading: isAuthLoading } = useAuth();
  const isAdmin = role === "ADMIN";

  const [activeTab, setActiveTab] = useState<TabType>("ledger");
  const [stats, setStats] = useState<AuditStats | null>(null);
  const [verification, setVerification] = useState<HashChainVerification | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);

  // Tab 1: Audit logs state
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [auditPage, setAuditPage] = useState(1);
  const [auditTotal, setAuditTotal] = useState(0);
  const [auditFilterBadge, setAuditFilterBadge] = useState<string>("ALL");
  const [auditSearch, setAuditSearch] = useState("");

  // Tab 2: System logs state
  const [systemLogs, setSystemLogs] = useState<SystemLog[]>([]);
  const [sysPage, setSysPage] = useState(1);
  const [sysTotal, setSysTotal] = useState(0);
  const [sysLogLevel, setSysLogLevel] = useState<string>("ALL");

  const [loading, setLoading] = useState(true);

  // Fetch initial summary & verifications
  const loadDashboardData = useCallback(async () => {
    try {
      const [statsRes, verifyRes, logsRes, sysRes] = await Promise.all([
        getAuditStats(),
        verifyHashChain(),
        listAuditLogs({ page: 1, page_size: 20 }),
        listSystemLogs({ page: 1, page_size: 20 }),
      ]);
      setStats(statsRes);
      setVerification(verifyRes);
      setAuditEvents(logsRes?.items ?? []);
      setAuditTotal(logsRes?.total ?? 0);
      setSystemLogs(sysRes?.items ?? []);
      setSysTotal(sysRes?.total ?? 0);
    } catch (err) {
      console.error("Failed to load Audit & Security data:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadDashboardData();
  }, [loadDashboardData]);

  // Handle manual trigger for hash chain verification
  const handleVerifyLedger = async () => {
    setIsVerifying(true);
    try {
      const res = await verifyHashChain();
      setVerification(res);
    } catch (err) {
      console.error("Failed to verify hash chain:", err);
    } finally {
      setIsVerifying(false);
    }
  };

  // Change page for Audit logs
  const handleAuditPageChange = async (newPage: number) => {
    setAuditPage(newPage);
    try {
      const res = await listAuditLogs({ page: newPage, page_size: 20 });
      setAuditEvents(res?.items ?? []);
      setAuditTotal(res?.total ?? 0);
    } catch (err) {
      console.error("Failed to load audit log page:", err);
    }
  };

  // Change page for System logs
  const handleSysPageChange = async (newPage: number) => {
    setSysPage(newPage);
    try {
      const res = await listSystemLogs({
        page: newPage,
        page_size: 20,
        level: sysLogLevel === "ALL" ? undefined : sysLogLevel,
      });
      setSystemLogs(res?.items ?? []);
      setSysTotal(res?.total ?? 0);
    } catch (err) {
      console.error("Failed to load system log page:", err);
    }
  };

  // Handle filter change for System logs
  const handleSysFilterChange = async (level: string) => {
    setSysLogLevel(level);
    setSysPage(1);
    try {
      const res = await listSystemLogs({
        page: 1,
        page_size: 20,
        level: level === "ALL" ? undefined : level,
      });
      setSystemLogs(res?.items ?? []);
      setSysTotal(res?.total ?? 0);
    } catch (err) {
      console.error("Failed to filter system log:", err);
    }
  };

  // Filtered audit events for Tab 1
  const filteredAuditEvents = useMemo(() => {
    return auditEvents.filter((ev) => {
      const matchBadge =
        auditFilterBadge === "ALL" ||
        ev.status_badge.toUpperCase() === auditFilterBadge;
      const matchSearch =
        auditSearch === "" ||
        ev.title.toLowerCase().includes(auditSearch.toLowerCase()) ||
        ev.description.toLowerCase().includes(auditSearch.toLowerCase()) ||
        ev.actor.toLowerCase().includes(auditSearch.toLowerCase()) ||
        ev.event_type.toLowerCase().includes(auditSearch.toLowerCase());
      return matchBadge && matchSearch;
    });
  }, [auditEvents, auditFilterBadge, auditSearch]);

  if (isAuthLoading || loading) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center gap-3">
        <div className="h-9 w-9 animate-spin rounded-full border-3 border-brand-500 border-t-transparent" />
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Loading Audit & Security command center...
        </p>
      </div>
    );
  }

  // Access check: Only ADMIN role is authorized
  if (!isAdmin) {
    return (
      <div className="space-y-6">
        <PageBreadcrumb pageTitle="Audit & Security" />
        <div className="rounded-2xl border border-warning-200 bg-warning-50/50 p-8 text-center shadow-theme-xs dark:border-warning-800 dark:bg-warning-950/20">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-warning-100 text-warning-600 dark:bg-warning-500/20 dark:text-warning-400">
            <LockIcon/>
          </div>
          <h2 className="mt-4 text-xl font-bold text-gray-900 dark:text-white">
            Restricted Access — Administrator Only
          </h2>
          <p className="mx-auto mt-2 max-w-lg text-sm text-gray-600 dark:text-gray-400">
            The Audit & Security module contains immutable audit trails (cryptographic hash chain) and system logs protected by RBAC policy (Pillar 5: RECORD).
          </p>
          <div className="mt-6">
            <Link
              href="/"
              className="inline-flex items-center gap-2 rounded-xl bg-brand-500 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-600 transition-colors"
            >
              Back to Main Dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <PageBreadcrumb pageTitle="Audit & Security Center" />
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
            Audit & Security Command Center
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400 sm:text-sm mt-0.5">
            Monitoring center for SHA-256 cryptographic audit trail integrity and system activity logs.
          </p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <Badge color="success" size="md" startIcon={<CheckCircleIcon/>}>
            RBAC: ADMIN ACCESS
          </Badge>
          <button
            onClick={loadDashboardData}
            className="rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-semibold text-gray-700 shadow-theme-xs hover:bg-gray-50 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-800 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* KPI Stats Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4 md:gap-6">
        {/* Card 1: Total Audit Events */}
        <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-400">
            <DocsIcon/>
          </div>
          <div className="mt-4">
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
              Total Audit Trail
            </span>
            <h3 className="mt-1 text-2xl font-bold text-gray-900 dark:text-white">
              {stats?.total_events.toLocaleString("id-ID") ?? 0}
            </h3>
          </div>
        </div>

        {/* Card 2: Hash Chain Integrity */}
        <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-success-50 text-success-600 dark:bg-success-500/10 dark:text-success-400">
            <CheckCircleIcon/>
          </div>
          <div className="mt-4">
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
              Hash-Chain Integrity
            </span>
            <div className="mt-1 flex items-center gap-2">
              <h3 className="text-xl font-bold text-success-600 dark:text-success-400">
                {verification?.is_valid ? "VALID & UNBROKEN" : "TAMPERED / ERROR"}
              </h3>
            </div>
          </div>
        </div>

        {/* Card 3: Total System Logs */}
        <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400">
            <ListIcon/>
          </div>
          <div className="mt-4">
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
              Total System Logs
            </span>
            <h3 className="mt-1 text-2xl font-bold text-gray-900 dark:text-white">
              {stats?.total_system_logs ?? 0}
            </h3>
          </div>
        </div>

        {/* Card 4: Technical System Errors */}
        <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-error-50 text-error-600 dark:bg-error-500/10 dark:text-error-400">
            <ListIcon/>
          </div>
          <div className="mt-4">
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
              System Error Logs
            </span>
            <h3 className="mt-1 text-2xl font-bold text-gray-900 dark:text-white">
              {stats?.total_system_errors ?? 0}
            </h3>
          </div>
        </div>
      </div>

      {/* Interactive Cryptographic Hash-Chain Verification Banner */}
      <div className="rounded-2xl border border-gray-200 bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 p-6 text-white shadow-theme-sm dark:border-gray-800">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="flex h-2.5 w-2.5 rounded-full bg-success-400 animate-pulse" />
              <h3 className="text-lg font-semibold tracking-wide">
                VCryptographic Chain Integrity Verification
              </h3>
            </div>
            <div className="mt-3 flex flex-wrap gap-4 pt-1 text-xs font-mono text-gray-300">
              <div>
                <span className="text-gray-400">Genesis Block:</span>{" "}
                <span className="text-brand-300">
                  {verification?.genesis_hash ? `${verification.genesis_hash.slice(0, 24)}...` : "—"}
                </span>
              </div>
              <div>
                <span className="text-gray-400">Latest Hash:</span>{" "}
                <span className="text-success-300">
                  {verification?.latest_hash ? `${verification.latest_hash.slice(0, 24)}...` : "—"}
                </span>
              </div>
              <div>
                <span className="text-gray-400">Verified Block:</span>{" "}
                <span className="text-white font-bold">{verification?.total_blocks ?? 0} Block</span>
              </div>
            </div>
          </div>

          <div className="shrink-0">
            <button
              onClick={handleVerifyLedger}
              disabled={isVerifying}
              className="inline-flex items-center gap-2 rounded-xl bg-brand-500 px-5 py-2.5 text-xs font-semibold text-white shadow-md hover:bg-brand-600 transition-all disabled:opacity-50"
            >
              {isVerifying ? (
                <>
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Memverifikasi...
                </>
              ) : (
                <>
                  <CheckCircleIcon/>
                  Run Chain Verification
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Tabs Header */}
      <div className="border-b border-gray-200 dark:border-gray-800">
        <nav className="flex space-x-6">
          <button
            onClick={() => setActiveTab("ledger")}
            className={`flex items-center gap-2 pb-3 text-sm font-semibold transition-colors border-b-2 ${
              activeTab === "ledger"
                ? "border-brand-500 text-brand-600 dark:text-brand-400"
                : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400"
            }`}
          >
            <DocsIcon/>
            Audit Ledger
            <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[11px] font-mono text-gray-700 dark:bg-gray-800 dark:text-gray-300">
              {auditTotal}
            </span>
          </button>

          <button
            onClick={() => setActiveTab("systemLogs")}
            className={`flex items-center gap-2 pb-3 text-sm font-semibold transition-colors border-b-2 ${
              activeTab === "systemLogs"
                ? "border-brand-500 text-brand-600 dark:text-brand-400"
                : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400"
            }`}
          >
            <ListIcon/>
            System Technical Logs
            <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[11px] font-mono text-gray-700 dark:bg-gray-800 dark:text-gray-300">
              {sysTotal}
            </span>
          </button>
        </nav>
      </div>

      {/* Tab 1: Immutable Ledger Stream */}
      {activeTab === "ledger" && (
        <div className="rounded-2xl border border-gray-200 bg-white p-5 md:p-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900 space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="text-base font-semibold text-gray-900 dark:text-white">
                List of Encrypted Audit Trails
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Append-only log recording all AI actions and HR decisions.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {/* Search */}
              <input
                type="text"
                placeholder="Cari aktor, event, atau detail..."
                value={auditSearch}
                onChange={(e) => setAuditSearch(e.target.value)}
                className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-1.5 text-xs text-gray-900 focus:border-brand-500 focus:outline-none dark:border-gray-800 dark:bg-gray-800 dark:text-white"
              />

              {/* Status Filter */}
              <select
                value={auditFilterBadge}
                onChange={(e) => setAuditFilterBadge(e.target.value)}
                className="rounded-lg border border-gray-200 bg-gray-50 px-2.5 py-1.5 text-xs text-gray-900 dark:border-gray-800 dark:bg-gray-800 dark:text-white"
              >
                <option value="ALL">All Status</option>
                <option value="SUCCESS">Success</option>
                <option value="WARNING">Warning</option>
                <option value="ERROR">Error</option>
                <option value="INFO">Info</option>
              </select>

              <Link
                href="/audit/logs"
                className="inline-flex items-center gap-1 text-xs font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400"
              >
                Full Page
                <ArrowRightIcon/>
              </Link>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-start">
              <thead>
                <tr className="border-b border-gray-100 text-xs font-semibold uppercase tracking-wider text-gray-500 dark:border-gray-800 dark:text-gray-400">
                  <th className="py-3 pe-4 text-start">Time</th>
                  <th className="py-3 pe-4 text-start">Event Type</th>
                  <th className="py-3 pe-4 text-start">Actor</th>
                  <th className="py-3 pe-4 text-start">Details of the Incident</th>
                  <th className="py-3 pe-4 text-start">Status</th>
                  <th className="py-3 text-start">Hash Code</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-sm dark:divide-gray-800">
                {filteredAuditEvents.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-xs text-gray-500">
                       No audit records match the filter.
                    </td>
                  </tr>
                ) : (
                  filteredAuditEvents.map((ev) => (
                    <tr
                      key={ev.id}
                      className="hover:bg-gray-50/50 transition-colors dark:hover:bg-gray-800/50"
                    >
                      <td className="py-3 pe-4 font-mono text-xs text-gray-500 dark:text-gray-400 shrink-0">
                        {new Date(ev.timestamp).toLocaleString("id-ID", {
                          day: "numeric",
                          month: "short",
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit",
                        })}
                      </td>
                      <td className="py-3 pe-4 font-mono text-xs font-semibold text-gray-900 dark:text-white">
                        {ev.event_type}
                      </td>
                      <td className="py-3 pe-4 text-xs font-medium text-gray-700 dark:text-gray-300">
                        {ev.actor}
                      </td>
                      <td className="py-3 pe-4 text-xs text-gray-600 dark:text-gray-300 max-w-xs truncate">
                        {ev.description}
                      </td>
                      <td className="py-3 pe-4">
                        <Badge color={ev.status_badge} size="sm">
                          {ev.status_badge.toUpperCase()}
                        </Badge>
                      </td>
                      <td className="py-3 font-mono text-[11px] text-gray-400 dark:text-gray-500">
                        {typeof ev.metadata?.hash === "string"
                          ? `${ev.metadata.hash.slice(0, 10)}...${ev.metadata.hash.slice(-6)}`
                          : "GENESIS"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <TablePagination
            currentPage={auditPage}
            totalPages={Math.ceil(auditTotal / 20) || 1}
            totalItems={auditTotal}
            pageSize={20}
            onPageChange={handleAuditPageChange}
          />
        </div>
      )}

      {/* Tab 2: System Access & Technical Logs */}
      {activeTab === "systemLogs" && (
        <div className="rounded-2xl border border-gray-200 bg-white p-5 md:p-6 shadow-theme-xs dark:border-gray-800 dark:bg-gray-900 space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="text-base font-semibold text-gray-900 dark:text-white">
                Technical System & Middleware Logs
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Logging of API access, HTTP methods, route status codes, and error stack traces.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Filter Level:</span>
              <select
                value={sysLogLevel}
                onChange={(e) => handleSysFilterChange(e.target.value)}
                className="rounded-lg border border-gray-200 bg-gray-50 px-2.5 py-1.5 text-xs text-gray-900 dark:border-gray-800 dark:bg-gray-800 dark:text-white"
              >
                <option value="ALL">All LEVEL</option>
                <option value="INFO">INFO</option>
                <option value="WARN">WARN</option>
                <option value="ERROR">ERROR</option>
              </select>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-start">
              <thead>
                <tr className="border-b border-gray-100 text-xs font-semibold uppercase tracking-wider text-gray-500 dark:border-gray-800 dark:text-gray-400">
                  <th className="py-3 pe-4 text-start">Time</th>
                  <th className="py-3 pe-4 text-start">Level</th>
                  <th className="py-3 pe-4 text-start">Methods & Paths</th>
                  <th className="py-3 pe-4 text-start">Status</th>
                  <th className="py-3 text-start">Error</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-sm dark:divide-gray-800">
                {systemLogs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-xs text-gray-500">
                      No system log entries were found.
                    </td>
                  </tr>
                ) : (
                  systemLogs.map((log) => (
                    <tr
                      key={log.nid}
                      className="hover:bg-gray-50/50 transition-colors dark:hover:bg-gray-800/50"
                    >
                      <td className="py-3 pe-4 font-mono text-xs text-gray-500 dark:text-gray-400 shrink-0">
                        {new Date(log.dcrea).toLocaleTimeString("id-ID")}
                      </td>
                      <td className="py-3 pe-4">
                        <Badge
                          color={
                            log.vlog_level === "ERROR"
                              ? "error"
                              : log.vlog_level === "WARN"
                              ? "warning"
                              : "info"
                          }
                          size="sm"
                        >
                          {log.vlog_level}
                        </Badge>
                      </td>
                      <td className="py-3 pe-4 font-mono text-xs text-gray-800 dark:text-gray-200">
                        <span className="font-bold text-brand-600 dark:text-brand-400 me-1.5">
                          {log.vlog_method ?? "REQ"}
                        </span>
                        {log.vlog_path ?? "—"}
                      </td>
                      <td className="py-3 pe-4 font-mono text-xs font-semibold">
                        <span
                          className={
                            log.vlog_status_code && Number(log.vlog_status_code) >= 400
                              ? "text-error-600 dark:text-error-400"
                              : "text-success-600 dark:text-success-400"
                          }
                        >
                          {log.vlog_status_code ?? "200"}
                        </span>
                      </td>
                      <td className="py-3 text-xs text-gray-600 dark:text-gray-300 max-w-md truncate">
                        {log.vlog_message}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <TablePagination
            currentPage={sysPage}
            totalPages={Math.ceil(sysTotal / 20) || 1}
            totalItems={sysTotal}
            pageSize={20}
            onPageChange={handleSysPageChange}
          />
        </div>
      )}
    </div>
  );
}
