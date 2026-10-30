"use client";

import React, { useState } from "react";
import { Link } from "@/i18n/navigation";
import {
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import Button from "@/components/ui/button/Button";
import { ConfirmationModal } from "@/components/ui/modal";
import ConsentBadge from "./ConsentBadge";
import AudioUploadModal from "./AudioUploadModal";
import { UserRole } from "@/types/auth";
import { InterviewSession } from "@/types/interview";
import { Candidate, InterviewerContact, RubricProfile } from "@/types/master";
import {
  AlertIcon,
  AudioIcon,
  BoltIcon,
  CheckCircleIcon,
  CloseLineIcon,
  DocsIcon,
  PlusIcon,
  TimeIcon,
  TrashBinIcon,
} from "@/icons";
import TablePagination from "@/components/common/TablePagination";

function formatSessionDate(isoStr?: string | null): string {
  if (!isoStr) return "-";
  try {
    let s = isoStr.trim();
    if (!s.endsWith("Z") && !/[+-]\d{2}:?\d{2}$/.test(s)) {
      s += "Z";
    }
    const d = new Date(s);
    if (isNaN(d.getTime())) return isoStr;
    const datePart = d.toLocaleDateString("id-ID", {
      day: "numeric",
      month: "short",
      year: "numeric",
      timeZone: "Asia/Jakarta",
    });
    const timePart = d.toLocaleTimeString("id-ID", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
      timeZone: "Asia/Jakarta",
    });
    return `${datePart} • ${timePart} WIB`;
  } catch {
    return isoStr;
  }
}

interface SessionTableProps {
  sessions: InterviewSession[];
  isLoading?: boolean;
  onUploadSession: (
    session: InterviewSession,
    file?: File | null
  ) => Promise<InterviewSession | null>;
  onDeleteSession?: (sessionId: string) => Promise<void>;
  candidates: Candidate[];
  rubrics: RubricProfile[];
  interviewers: InterviewerContact[];
  initialUploadCandidateId?: string | null;
  autoOpenUpload?: boolean;
  currentUserId?: string | null;
  currentUserName?: string | null;
  currentRole?: UserRole | null;
  currentPage?: number;
  pageSize?: number;
  totalItems?: number;
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
}

export default function SessionTable({
  sessions,
  isLoading = false,
  onUploadSession,
  onDeleteSession,
  candidates,
  rubrics,
  interviewers,
  initialUploadCandidateId,
  autoOpenUpload = false,
  currentUserId,
  currentUserName,
  currentRole,
  currentPage,
  pageSize,
  totalItems,
  onPageChange,
  onPageSizeChange,
}: SessionTableProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [consentFilter, setConsentFilter] = useState<string>("ALL");
  const [isModalOpen, setIsModalOpen] = useState<boolean>(autoOpenUpload);
  const [deleteTarget, setDeleteTarget] = useState<InterviewSession | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  const handleConfirmDelete = async () => {
    if (!deleteTarget || !onDeleteSession) return;
    setIsDeleting(true);
    try {
      await onDeleteSession(deleteTarget.id);
      setDeleteTarget(null);
    } catch {
      // Error toast is surfaced by parent handler
    } finally {
      setIsDeleting(false);
    }
  };

  const filteredSessions = sessions.filter((session) => {
    const matchesSearch =
      session.candidate_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      session.candidate_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      session.position.toLowerCase().includes(searchQuery.toLowerCase()) ||
      session.interviewer_name.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesConsent =
      consentFilter === "ALL" || session.consent_status === consentFilter;

    return matchesSearch && matchesConsent;
  });

  const renderJobStatus = (session: InterviewSession) => {
    if (
      session.consent_status !== "GRANTED" ||
      session.job_status === "REJECTED_NO_CONSENT"
    ) {
      return (
        <span className="inline-flex items-center gap-1 rounded-md bg-error-50 px-2 py-0.5 text-[11px] font-semibold text-error-700 dark:bg-error-500/15 dark:text-error-400">
          <CloseLineIcon />
          NO_CONSENT
        </span>
      );
    }

    if (session.job_status === "COMPLETED") {
      return (
        <div className="flex items-center gap-2 text-start">
          <span className="inline-flex items-center gap-1 rounded-md bg-success-50 px-2 py-0.5 text-[11px] font-semibold text-success-700 dark:bg-success-500/15 dark:text-success-400">
            <CheckCircleIcon />
            COMPLETED
          </span>
          {session.audio_duration && (
            <span className="inline-flex items-center gap-1 text-[11px] font-mono text-gray-600 dark:text-gray-400">
              <AudioIcon className="text-brand-500 text-xs shrink-0" />
              <span>{session.audio_duration}</span>
            </span>
          )}
        </div>
      );
    }

    const pct = session.progress_percentage ?? 25;
    return (
      <div className="space-y-1 min-w-[140px] max-w-[170px] text-start">
        <div className="flex items-center justify-between text-[10px] font-semibold">
          <span className="text-brand-600 dark:text-brand-400 flex items-center gap-1">
            <TimeIcon className="animate-spin text-xs shrink-0" />
            <span className="truncate">{session.job_status}</span>
          </span>
          <span className="text-gray-500 dark:text-gray-400 font-mono ms-1">{pct}%</span>
        </div>
        <div className="w-full h-1.5 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
          <div
            className="h-full bg-linear-to-r from-brand-500 to-theme-purple-500 rounded-full transition-all duration-500 ease-out animate-pulse"
            style={{ width: `${Math.max(10, pct)}%` }}
          />
        </div>
        <div className="flex items-center justify-between text-[9px] text-gray-400 dark:text-gray-500">
          <span
            className="truncate max-w-[95px]"
            title={session.current_step || "Processing..."}
          >
            {session.current_step || "Processing..."}
          </span>
          {session.audio_duration && (
            <span className="inline-flex items-center gap-1 font-mono shrink-0">
              <AudioIcon className="text-brand-500 text-[10px]" />
              {session.audio_duration}
            </span>
          )}
        </div>
      </div>
    );
  };

  const renderHrDecisionBadge = (session: InterviewSession) => {
    if (session.consent_status !== "GRANTED") {
      return <span className="text-[11px] text-gray-400">-</span>;
    }
    if (session.job_status !== "COMPLETED") {
      return <span className="text-[11px] text-gray-400">Awaiting AI...</span>;
    }
    const dec = session.hr_decision;
    if (!dec) {
      const isAssignedToOther =
        Boolean(session.interviewer_id) &&
        Boolean(currentUserId) &&
        session.interviewer_id !== currentUserId &&
        currentRole !== "INTERVIEWER";
      return (
        <span className="inline-flex items-center gap-1 rounded-md bg-warning-50 px-2 py-0.5 text-[11px] font-semibold text-warning-700 dark:bg-warning-500/15 dark:text-warning-300">
          <AlertIcon />
          {isAssignedToOther ? "Awaiting Interviewer" : "Pending Evaluation"}
        </span>
      );
    }

    const stageMap: Record<string, string> = {
      NEXT_INTERVIEW: "Next Round",
      TECHNICAL_TEST: "Tech Test",
      OFFERED: "Offering",
    };
    const stageText = dec.next_stage ? ` → ${stageMap[dec.next_stage] ?? dec.next_stage}` : "";

    if (dec.workflow_status === "PENDING_HR_FOLLOWUP") {
      return (
        <div className="space-y-0.5 text-start">
          <span className="inline-flex items-center gap-1 rounded-md bg-brand-50 px-2 py-0.5 text-[11px] font-semibold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
            <AlertIcon />
            Rec: {dec.decision}
            {stageText}
          </span>
          <span className="block text-[10px] font-semibold text-warning-600 dark:text-warning-400">
            Pending HR Follow-Up
          </span>
        </div>
      );
    }

    if (dec.decision === "ADVANCE") {
      return (
        <span className="inline-flex items-center gap-1 rounded-md bg-success-50 px-2 py-0.5 text-[11px] font-semibold text-success-700 dark:bg-success-500/15 dark:text-success-400">
          <CheckCircleIcon />
          FINAL: ADVANCE{stageText}
        </span>
      );
    }

    if (dec.decision === "HOLD") {
      return (
        <span className="inline-flex items-center gap-1 rounded-md bg-warning-50 px-2 py-0.5 text-[11px] font-semibold text-warning-700 dark:bg-warning-500/15 dark:text-warning-300">
          <AlertIcon />
          FINAL: HOLD
        </span>
      );
    }

    return (
      <span className="inline-flex items-center gap-1 rounded-md bg-error-50 px-2 py-0.5 text-[11px] font-semibold text-error-700 dark:bg-error-500/15 dark:text-error-400">
        <CloseLineIcon />
        FINAL: REJECTED
      </span>
    );
  };

  const getReviewActionConfig = (session: InterviewSession) => {
    const dec = session.hr_decision;
    const isOwnSession =
      Boolean(currentUserId) &&
      Boolean(session.interviewer_id) &&
      session.interviewer_id === currentUserId;

    if (!dec) {
      if (currentRole === "INTERVIEWER" || !session.interviewer_id || isOwnSession) {
        return {
          label: "Review & Decide",
          className:
            "bg-brand-500 text-white shadow-theme-xs hover:bg-brand-600",
        };
      }
      return {
        label: "View Progress",
        className:
          "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200",
      };
    }

    if (dec.workflow_status === "PENDING_HR_FOLLOWUP") {
      if (currentRole === "HR" || currentRole === "ADMIN") {
        return {
          label: "HR Follow-Up",
          className:
            "bg-warning-500 text-white shadow-theme-xs hover:bg-warning-600",
        };
      }
      return {
        label: "View Submitted",
        className:
          "border border-brand-200 bg-brand-50 text-brand-700 hover:bg-brand-100 dark:border-brand-500/30 dark:bg-brand-500/10 dark:text-brand-300",
      };
    }

    return {
      label: "View Evidence",
      className:
        "border border-brand-200 bg-brand-50 text-brand-700 hover:bg-brand-100 dark:border-brand-500/30 dark:bg-brand-500/10 dark:text-brand-300",
    };
  };

  return (
    <div className="space-y-4">
      {/* Search and Action Bar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-1 flex-wrap items-center gap-2.5">
          <div className="relative min-w-[240px] flex-1 sm:max-w-xs">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search candidate, code, or role..."
              className="w-full rounded-xl border border-gray-300 bg-white py-2 px-3.5 text-xs text-gray-800 placeholder-gray-400 focus:border-brand-500 focus:outline-hidden focus:ring-1 focus:ring-brand-500 dark:border-gray-700 dark:bg-gray-900 dark:text-white"
            />
          </div>

          <div className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400">
            <span>Consent:</span>
            <select
              value={consentFilter}
              onChange={(e) => setConsentFilter(e.target.value)}
              className="rounded-lg border border-gray-300 bg-white px-2.5 py-1.5 text-xs text-gray-800 focus:border-brand-500 focus:outline-hidden dark:border-gray-700 dark:bg-gray-900 dark:text-white"
            >
              <option value="ALL">All Status</option>
              <option value="GRANTED">Granted (Processing Allowed)</option>
              <option value="NOT_GRANTED">Not Granted (Blocked)</option>
            </select>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="primary"
            onClick={() => setIsModalOpen(true)}
            startIcon={<PlusIcon className="me-1" />}
          >
            Ingest Audio Recording
          </Button>
        </div>
      </div>

      {/* Sessions Table */}
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-2xs dark:border-gray-800 dark:bg-gray-900">
        <div className="max-w-full overflow-x-auto">
          <Table>
            <TableHeader className="border-b border-gray-100 bg-gray-50/50 dark:border-gray-800 dark:bg-gray-800/40">
              <TableRow>
                <TableCell isHeader className="py-3.5 ps-5 text-start text-[11px] font-semibold text-gray-500 dark:text-gray-400 min-w-[240px]">
                  CANDIDATE &amp; SCHEDULE
                </TableCell>
                <TableCell isHeader className="py-3.5 text-start text-[11px] font-semibold text-gray-500 dark:text-gray-400 min-w-[200px] max-w-[240px]">
                  TARGET POSITION &amp; ROUND
                </TableCell>
                <TableCell isHeader className="py-3.5 text-start text-[11px] font-semibold text-gray-500 dark:text-gray-400 min-w-[170px]">
                  INTERVIEWER
                </TableCell>
                <TableCell isHeader className="py-3.5 text-start text-[11px] font-semibold text-gray-500 dark:text-gray-400 min-w-[110px]">
                  CONSENT
                </TableCell>
                <TableCell isHeader className="py-3.5 text-start text-[11px] font-semibold text-gray-500 dark:text-gray-400 min-w-[170px]">
                  AI COPILOT &amp; AUDIO
                </TableCell>
                <TableCell isHeader className="py-3.5 text-start text-[11px] font-semibold text-gray-500 dark:text-gray-400 min-w-[160px]">
                  DECISION STATUS
                </TableCell>
                <TableCell isHeader className="py-3.5 pe-5 text-end text-[11px] font-semibold text-gray-500 dark:text-gray-400 min-w-[150px]">
                  ACTION
                </TableCell>
              </TableRow>
            </TableHeader>

            <TableBody className="divide-y divide-gray-100 dark:divide-gray-800">
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-12 text-center text-xs text-gray-400">
                    Loading interview sessions from database...
                  </TableCell>
                </TableRow>
              ) : filteredSessions.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-12 text-center text-xs text-gray-400">
                    No interview sessions found matching current filter
                  </TableCell>
                </TableRow>
              ) : (
                filteredSessions.map((session) => {
                  const actionCfg = getReviewActionConfig(session);
                  const canDeleteUndecided =
                    Boolean(onDeleteSession) &&
                    !session.hr_decision &&
                    (currentRole === "HR" ||
                      currentRole === "ADMIN" ||
                      (Boolean(currentUserId) && session.interviewer_id === currentUserId));

                  return (
                    <TableRow
                      key={session.id}
                      className="hover:bg-gray-50/60 dark:hover:bg-gray-800/40 transition-colors"
                    >
                      <TableCell className="py-4 ps-5">
                        <div className="flex items-center gap-3 min-w-[220px]">
                          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-50 font-bold text-xs text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
                            {session.candidate_name
                              .split(" ")
                              .map((n) => n[0])
                              .slice(0, 2)
                              .join("")}
                          </div>
                          <div className="text-start">
                            <div className="flex items-center gap-1.5 flex-wrap">
                              <span className="font-semibold text-xs text-gray-900 dark:text-white">
                                {session.candidate_name}
                              </span>
                            </div>
                            <span className="block text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">
                              {formatSessionDate(session.scheduled_at)}
                            </span>
                          </div>
                        </div>
                      </TableCell>

                      <TableCell className="py-4 text-start">
                        <div className="min-w-[190px] max-w-[240px]">
                          <span
                            className="font-medium text-xs text-gray-800 dark:text-gray-200 block truncate"
                            title={session.position}
                          >
                            {session.position}
                          </span>
                          <span
                            className="block text-[11px] text-gray-500 dark:text-gray-400 truncate mt-0.5"
                            title={session.round_name}
                          >
                            {session.round_name}
                          </span>
                        </div>
                      </TableCell>

                      <TableCell className="py-4 text-start">
                        <div className="min-w-[150px] max-w-[190px]">
                          <span
                            className="font-medium text-xs text-gray-800 dark:text-gray-200 block truncate"
                            title={session.interviewer_name}
                          >
                            {session.interviewer_name}
                          </span>
                          <span
                            className="block text-[11px] text-gray-500 dark:text-gray-400 truncate mt-0.5"
                            title={session.interviewer_role}
                          >
                            {session.interviewer_role || "-"}
                          </span>
                        </div>
                      </TableCell>

                      <TableCell className="py-4 min-w-[110px]">
                        <ConsentBadge status={session.consent_status} />
                      </TableCell>

                      <TableCell className="py-4 min-w-[170px]">
                        {renderJobStatus(session)}
                      </TableCell>

                      <TableCell className="py-4 min-w-[160px]">
                        {renderHrDecisionBadge(session)}
                      </TableCell>

                      <TableCell className="py-4 pe-5 text-end min-w-[150px]">
                        <div className="flex items-center justify-end gap-2">
                          {session.consent_status === "GRANTED" ? (
                            session.job_status === "COMPLETED" ? (
                              <Link
                                href={`/interviews/review?id=${session.id}`}
                                className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-semibold transition-all ${actionCfg.className}`}
                              >
                                <DocsIcon />
                                <span>{actionCfg.label}</span>
                              </Link>
                            ) : (
                              <span className="inline-flex items-center gap-1.5 rounded-lg border border-brand-200 bg-brand-50/50 px-2.5 py-1.5 text-xs font-semibold text-brand-600 dark:border-brand-500/20 dark:bg-brand-500/5 dark:text-brand-400">
                                <TimeIcon className="animate-spin text-xs" />
                                <span>Memproses...</span>
                              </span>
                            )
                          ) : (
                            <span className="text-[11px] text-gray-400 italic">
                              Blocked (No Consent)
                            </span>
                          )}

                          {(currentRole === "HR" || currentRole === "ADMIN") &&
                            session.hr_decision?.decision === "ADVANCE" &&
                            session.hr_decision?.next_stage === "NEXT_INTERVIEW" &&
                            session.hr_decision?.workflow_status !== "PENDING_HR_FOLLOWUP" && (
                              <Link
                                href={`/orchestration/scheduling?candidateId=${session.candidate_id}`}
                                className="inline-flex items-center gap-1 rounded-lg border border-warning-300 bg-warning-50 px-2.5 py-1.5 text-xs font-semibold text-warning-800 hover:bg-warning-100 dark:border-warning-500/30 dark:bg-warning-500/15 dark:text-warning-300"
                                title="Jadwalkan ronde interview berikutnya"
                              >
                                <BoltIcon />
                                <span>Next Round</span>
                              </Link>
                            )}

                          {canDeleteUndecided && (
                            <button
                              type="button"
                              onClick={() => setDeleteTarget(session)}
                              className="inline-flex items-center justify-center rounded-lg border border-error-200 bg-error-50/60 p-1.5 text-error-600 transition-colors hover:bg-error-100 dark:border-error-500/25 dark:bg-error-500/10 dark:text-error-400 dark:hover:bg-error-500/20"
                              title="Delete interview session (only permitted before evaluation decision)"
                            >
                              <TrashBinIcon/>
                            </button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>

        {/* Table Pagination */}
        {totalItems !== undefined && onPageChange && totalItems > 0 && (
          <TablePagination
            currentPage={currentPage ?? 1}
            totalPages={Math.ceil(totalItems / (pageSize ?? 10)) || 1}
            totalItems={totalItems}
            pageSize={pageSize ?? 10}
            onPageChange={onPageChange}
            onPageSizeChange={onPageSizeChange}
            pageSizeOptions={[10, 20, 50]}
            isLoading={isLoading}
          />
        )}
      </div>

      {/* Audio Upload Modal connected to Real Candidates & Rubrics */}
      <AudioUploadModal
        key={`${initialUploadCandidateId ?? "default"}-${currentUserId ?? "anon"}`}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={onUploadSession}
        candidates={candidates}
        rubrics={rubrics}
        interviewers={interviewers}
        preselectedCandidateId={initialUploadCandidateId}
        currentUserId={currentUserId}
        currentUserName={currentUserName}
        currentRole={currentRole}
      />

      {/* Guarded Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={Boolean(deleteTarget)}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleConfirmDelete}
        title="Delete Interview Session?"
        description={
          deleteTarget
            ? `The interview session for ${deleteTarget.candidate_name} (${deleteTarget.round_name}) does not have an evaluation decision and will be permanently deleted.`
            : undefined
        }
        confirmText="Yes, Delete Session"
        cancelText="Cancel"
        variant="danger"
        isLoading={isDeleting}
      />
    </div>
  );
}
