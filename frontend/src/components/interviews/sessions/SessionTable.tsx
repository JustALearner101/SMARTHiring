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
import TablePagination from "@/components/common/TablePagination";
import AudioUploadModal from "./AudioUploadModal";
import { UserRole } from "@/types/auth";
import { InterviewSession } from "@/types/interview";
import { Candidate, InterviewerContact, RubricProfile } from "@/types/master";
import { formatWibShort } from "@/utils/formatDateTime";
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

 const renderPipelineStatus = (session: InterviewSession) => {
 if (
 session.consent_status !== "GRANTED" ||
 session.job_status === "REJECTED_NO_CONSENT"
 ) {
 return (
 <span className="inline-flex items-center gap-1 rounded-md bg-error-50 px-2.5 py-1 text-[11px] font-semibold text-error-700 dark:bg-error-500/15 dark:text-error-400 whitespace-nowrap">
 <CloseLineIcon />
 No consent
 </span>
 );
 }

 if (session.job_status !== "COMPLETED") {
 const pct = session.progress_percentage ?? 25;
 return (
 <div className="space-y-1 max-w-[170px]">
 <div className="flex items-center justify-between text-[11px] font-semibold">
 <span className="text-brand-600 dark:text-brand-400 flex items-center gap-1 whitespace-nowrap">
 <TimeIcon className="animate-spin text-xs" />
 Processing
 </span>
 <span className="text-gray-500 dark:text-gray-400 font-mono text-[10px]">{pct}%</span>
 </div>
 <div className="w-full h-1.5 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
 <div
 className="h-full bg-gradient-to-r from-brand-500 to-theme-purple-500 rounded-full transition-all duration-500 ease-out"
 style={{ width: `${Math.max(10, pct)}%` }}
 />
 </div>
 </div>
 );
 }

 const dec = session.hr_decision;
 if (!dec) {
 const isAssignedToOther =
 Boolean(session.interviewer_id) &&
 Boolean(currentUserId) &&
 session.interviewer_id !== currentUserId &&
 currentRole !== "INTERVIEWER";
 return (
 <span className="inline-flex items-center gap-1 rounded-md bg-warning-50 px-2.5 py-1 text-[11px] font-semibold text-warning-700 dark:bg-warning-500/15 dark:text-warning-300 whitespace-nowrap">
 <AlertIcon />
 {isAssignedToOther ? "Awaiting interviewer" : "Pending evaluation"}
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
 <span className="inline-flex items-center gap-1 rounded-md bg-brand-50 px-2.5 py-1 text-[11px] font-semibold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300 whitespace-nowrap">
 <AlertIcon />
 Pending HR follow-up
 </span>
 );
 }

 if (dec.decision === "ADVANCE") {
 return (
 <span className="inline-flex items-center gap-1 rounded-md bg-success-50 px-2.5 py-1 text-[11px] font-semibold text-success-700 dark:bg-success-500/15 dark:text-success-400 whitespace-nowrap">
 <CheckCircleIcon />
 Advanced{stageText}
 </span>
 );
 }

 if (dec.decision === "HOLD") {
 return (
 <span className="inline-flex items-center gap-1 rounded-md bg-warning-50 px-2.5 py-1 text-[11px] font-semibold text-warning-700 dark:bg-warning-500/15 dark:text-warning-300 whitespace-nowrap">
 <AlertIcon />
 On hold
 </span>
 );
 }

 return (
 <span className="inline-flex items-center gap-1 rounded-md bg-error-50 px-2.5 py-1 text-[11px] font-semibold text-error-700 dark:bg-error-500/15 dark:text-error-400 whitespace-nowrap">
 <CloseLineIcon />
 Rejected
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
 label: "Review & decide",
 className:
 "bg-brand-500 text-white shadow-theme-xs hover:bg-brand-600",
 };
 }
 return {
 label: "View progress",
 className:
 "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200",
 };
 }

 if (dec.workflow_status === "PENDING_HR_FOLLOWUP") {
 if (currentRole === "HR" || currentRole === "ADMIN") {
 return {
 label: "HR follow-up",
 className:
 "bg-warning-500 text-white shadow-theme-xs hover:bg-warning-600",
 };
 }
 return {
 label: "View submitted",
 className:
 "border border-brand-200 bg-brand-50 text-brand-700 hover:bg-brand-100 dark:border-brand-500/30 dark:bg-brand-500/10 dark:text-brand-300",
 };
 }

 return {
 label: "View evidence",
 className:
 "border border-brand-200 bg-brand-50 text-brand-700 hover:bg-brand-100 dark:border-brand-500/30 dark:bg-brand-500/10 dark:text-brand-300",
 };
 };

 return (
 <div className="space-y-4">
 {/* Search and Action Bar */}
 <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
 <div className="flex flex-1 flex-wrap items-center gap-3">
 <div className="relative min-w-[240px] flex-1 sm:max-w-xs">
 <input
 type="text"
 value={searchQuery}
 onChange={(e) => setSearchQuery(e.target.value)}
 placeholder="Search candidate, code, or role..."
 className="w-full rounded-xl border border-gray-300 bg-white py-2 px-3.5 text-xs text-gray-800 placeholder-gray-400 focus:border-brand-500 focus:outline-hidden focus:ring-1 focus:ring-brand-500 dark:border-gray-700 dark:bg-gray-900 dark:text-white"
 />
 </div>

 <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
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

 {/* Sessions Table - 6 Streamlined Columns */}
 <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-2xs dark:border-gray-800 dark:bg-gray-900">
 {/* 1. Mobile Card List View (< md) */}
 <div className="block md:hidden divide-y divide-gray-100 dark:divide-gray-800">
 {isLoading ? (
 <div className="py-12 text-center text-xs text-gray-400">
 Loading interview sessions from database...
 </div>
 ) : filteredSessions.length === 0 ? (
 <div className="py-12 text-center text-xs text-gray-400">
 No interview sessions found matching current filter
 </div>
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
 <div key={session.id} className="p-4 space-y-3">
 {/* Header: Candidate Info & Status */}
 <div className="flex items-start justify-between gap-2.5">
 <div className="flex items-center gap-2.5 min-w-0">
 <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-50 font-bold text-xs text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
 {session.candidate_name
 .split(" ")
 .map((n) => n[0])
 .slice(0, 2)
 .join("")}
 </div>
 <div className="min-w-0">
 <span className="font-semibold text-xs text-gray-900 dark:text-white block truncate">
 {session.candidate_name}
 </span>
 <span className="font-mono text-[11px] text-gray-500 dark:text-gray-400 block">
 {session.candidate_code}
 </span>
 </div>
 </div>
 <div className="shrink-0">
 {renderPipelineStatus(session)}
 </div>
 </div>

 {/* Position & Round */}
 <div className="text-xs">
 <span className="font-medium text-gray-800 dark:text-gray-200 block truncate">
 {session.position}
 </span>
 <span className="text-[11px] text-gray-500 dark:text-gray-400 block truncate" title={session.round_name}>
 {session.round_name}
 </span>
 </div>

 {/* Info Grid: Interviewer & Recording */}
 <div className="grid grid-cols-2 gap-2.5 rounded-xl bg-gray-50/80 p-2.5 dark:bg-gray-800/40 border border-gray-100 dark:border-gray-800">
 <div className="min-w-0">
 <span className="text-[10px] font-semibold uppercase text-gray-400 block">
 Interviewer
 </span>
 <p className="text-xs font-medium text-gray-900 dark:text-white truncate">
 {session.interviewer_name}
 </p>
 <p className="text-[10px] text-gray-500 dark:text-gray-400 truncate">
 {session.interviewer_role}
 </p>
 </div>

 <div>
 <span className="text-[10px] font-semibold uppercase text-gray-400 block">
 Recorded
 </span>
 <div className="inline-flex items-center gap-1 font-mono text-xs text-gray-700 dark:text-gray-300">
 <AudioIcon className="text-brand-500 text-xs shrink-0" />
 <span>{session.audio_duration || "00:00"}</span>
 </div>
 <span className="block text-[10px] text-gray-500 dark:text-gray-400">
 {formatWibShort(session.scheduled_at)}
 </span>
 </div>
 </div>

 {/* Actions */}
 <div className="flex items-center justify-end gap-2 pt-1">
 {session.consent_status === "GRANTED" ? (
 session.job_status === "COMPLETED" ? (
 <Link
 href={`/interviews/review?id=${session.id}`}
 className={`flex-1 inline-flex items-center justify-center gap-1.5 rounded-xl px-3 py-2 text-xs font-semibold whitespace-nowrap transition-all shadow-theme-xs ${actionCfg.className}`}
 >
 <DocsIcon />
 <span>{actionCfg.label}</span>
 </Link>
 ) : (
 <span className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-xl border border-brand-200 bg-brand-50/50 px-3 py-2 text-xs font-semibold text-brand-600 dark:border-brand-500/20 dark:bg-brand-500/5 dark:text-brand-400">
 <TimeIcon className="animate-spin text-xs" />
 <span>Processing...</span>
 </span>
 )
 ) : (
 <span className="flex-1 text-center py-2 text-[11px] text-gray-400 italic">
 Consent Blocked
 </span>
 )}

 {(currentRole === "HR" || currentRole === "ADMIN") &&
 session.hr_decision?.decision === "ADVANCE" &&
 session.hr_decision?.next_stage === "NEXT_INTERVIEW" &&
 session.hr_decision?.workflow_status !== "PENDING_HR_FOLLOWUP" && (
 <Link
 href={`/orchestration/scheduling?candidateId=${session.candidate_id}`}
 className="inline-flex items-center justify-center gap-1 rounded-xl border border-warning-300 bg-warning-50 px-3 py-2 text-xs font-semibold text-warning-800 hover:bg-warning-100 dark:border-warning-500/30 dark:bg-warning-500/15 dark:text-warning-300 shadow-theme-xs"
 title="Jadwalkan ronde interview berikutnya"
 >
 <BoltIcon />
 <span>Next</span>
 </Link>
 )}

 {canDeleteUndecided && (
 <button
 type="button"
 onClick={() => setDeleteTarget(session)}
 className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-error-200 bg-error-50/60 text-error-600 transition-colors hover:bg-error-100 dark:border-error-500/25 dark:bg-error-500/10 dark:text-error-400 dark:hover:bg-error-500/20"
 title="Hapus sesi wawancara (hanya diizinkan sebelum ada keputusan)"
 >
 <TrashBinIcon />
 </button>
 )}
 </div>
 </div>
 );
 })
 )}
 </div>

 {/* 2. Desktop Table View (>= md) */}
 <div className="hidden md:block overflow-x-auto">
 <Table className="w-full min-w-[950px] table-fixed">
 <TableHeader className="border-b border-gray-100 bg-gray-50/50 dark:border-gray-800 dark:bg-gray-800/40">
 <TableRow>
 <TableCell isHeader className="w-[19%] py-3.5 ps-5 pe-4 text-start text-[11px] font-semibold text-gray-500 dark:text-gray-400 whitespace-nowrap">
 Candidate
 </TableCell>
 <TableCell isHeader className="w-[19%] py-3.5 px-4 text-start text-[11px] font-semibold text-gray-500 dark:text-gray-400 whitespace-nowrap">
 Position &amp; Round
 </TableCell>
 <TableCell isHeader className="w-[15%] py-3.5 px-4 text-start text-[11px] font-semibold text-gray-500 dark:text-gray-400 whitespace-nowrap">
 Interviewer
 </TableCell>
 <TableCell isHeader className="w-[11%] py-3.5 px-4 text-start text-[11px] font-semibold text-gray-500 dark:text-gray-400 whitespace-nowrap">
 Recorded
 </TableCell>
 <TableCell isHeader className="w-[18%] py-3.5 px-4 text-start text-[11px] font-semibold text-gray-500 dark:text-gray-400 whitespace-nowrap">
 Status
 </TableCell>
 <TableCell isHeader className="w-[18%] py-3.5 ps-4 pe-5 text-end text-[11px] font-semibold text-gray-500 dark:text-gray-400 whitespace-nowrap">
 Action
 </TableCell>
 </TableRow>
 </TableHeader>

 <TableBody className="divide-y divide-gray-100 dark:divide-gray-800">
 {isLoading ? (
 <TableRow>
 <TableCell colSpan={6} className="py-12 text-center text-xs text-gray-400">
 Loading interview sessions from database...
 </TableCell>
 </TableRow>
 ) : filteredSessions.length === 0 ? (
 <TableRow>
 <TableCell colSpan={6} className="py-12 text-center text-xs text-gray-400">
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
 {/* 1. Candidate Info */}
 <TableCell className="py-3.5 ps-5 pe-4">
 <div className="flex items-center gap-3">
 <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-50 font-bold text-xs text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
 {session.candidate_name
 .split(" ")
 .map((n) => n[0])
 .slice(0, 2)
 .join("")}
 </div>
 <div className="text-start min-w-0">
 <span className="font-semibold text-xs text-gray-900 dark:text-white block truncate">
 {session.candidate_name}
 </span>
 <span className="font-mono text-[11px] text-gray-500 dark:text-gray-400 block">
 {session.candidate_code}
 </span>
 </div>
 </div>
 </TableCell>

 {/* 2. Position & Round */}
 <TableCell className="py-3.5 px-4 text-start">
 <div className="min-w-0">
 <span className="font-medium text-xs text-gray-800 dark:text-gray-200 block truncate">
 {session.position}
 </span>
 <span
 className="text-[11px] text-gray-500 dark:text-gray-400 block truncate max-w-[210px]"
 title={session.round_name}
 >
 {session.round_name}
 </span>
 </div>
 </TableCell>

 {/* 3. Interviewer */}
 <TableCell className="py-3.5 px-4 text-start">
 <div className="min-w-0">
 <span className="font-medium text-xs text-gray-800 dark:text-gray-200 block truncate">
 {session.interviewer_name}
 </span>
 <span className="text-[11px] text-gray-500 dark:text-gray-400 block">
 {session.interviewer_role}
 </span>
 </div>
 </TableCell>

 {/* 4. Recorded (Duration & Date) */}
 <TableCell className="py-3.5 px-4 text-start">
 <div className="space-y-0.5">
 <div className="inline-flex items-center gap-1.5 font-mono text-xs text-gray-700 dark:text-gray-300">
 <AudioIcon className="text-brand-500 text-xs shrink-0" />
 <span>{session.audio_duration || "00:00"}</span>
 </div>
 <span className="block text-[11px] text-gray-500 dark:text-gray-400">
 {formatWibShort(session.scheduled_at)}
 </span>
 </div>
 </TableCell>

 {/* 5. Unified Status */}
 <TableCell className="py-3.5 px-4 text-start">
 {renderPipelineStatus(session)}
 </TableCell>

 {/* 6. Action */}
 <TableCell className="py-3.5 ps-4 pe-5 text-end">
 <div className="flex items-center justify-end gap-2">
 {session.consent_status === "GRANTED" ? (
 session.job_status === "COMPLETED" ? (
 <Link
 href={`/interviews/review?id=${session.id}`}
 className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold whitespace-nowrap transition-all ${actionCfg.className}`}
 >
 <DocsIcon />
 <span>{actionCfg.label}</span>
 </Link>
 ) : (
 <span className="inline-flex items-center gap-1.5 rounded-lg border border-brand-200 bg-brand-50/50 px-3 py-1.5 text-xs font-semibold text-brand-600 dark:border-brand-500/20 dark:bg-brand-500/5 dark:text-brand-400">
 <TimeIcon className="animate-spin text-xs" />
 <span>Processing...</span>
 </span>
 )
 ) : (
 <span className="text-[11px] text-gray-400 italic">
 Blocked
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
 <span>Next</span>
 </Link>
 )}

 {canDeleteUndecided && (
 <button
 type="button"
 onClick={() => setDeleteTarget(session)}
 className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-error-200 bg-error-50/60 text-error-600 transition-colors hover:bg-error-100 dark:border-error-500/25 dark:bg-error-500/10 dark:text-error-400 dark:hover:bg-error-500/20"
 title="Hapus sesi wawancara (hanya diizinkan sebelum ada keputusan)"
 >
 <TrashBinIcon />
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

 {totalItems !== undefined && onPageChange && (
 <TablePagination
 currentPage={currentPage ?? 1}
 totalPages={Math.max(1, Math.ceil((totalItems || 0) / (pageSize || 10)))}
 totalItems={totalItems}
 pageSize={pageSize || 10}
 onPageChange={onPageChange}
 onPageSizeChange={onPageSizeChange}
 pageSizeOptions={[10, 20, 50]}
 isLoading={isLoading}
 />
 )}
 </div>

 {/* Audio Upload Modal */}
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
 title="Hapus Sesi Wawancara?"
 description={
 deleteTarget
 ? `Sesi wawancara untuk ${deleteTarget.candidate_name} (${deleteTarget.round_name}) belum memiliki keputusan evaluasi dan akan dihapus secara permanen.`
 : undefined
 }
 confirmText="Ya, Hapus Sesi"
 cancelText="Batal"
 variant="danger"
 isLoading={isDeleting}
 />
 </div>
 );
}
