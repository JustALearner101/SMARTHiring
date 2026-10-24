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
import ConsentBadge from "./ConsentBadge";
import AudioUploadModal from "./AudioUploadModal";
import { InterviewSession } from "@/types/interview";
import {
  AudioIcon,
  DocsIcon,
  BoltIcon,
  PlusIcon,
  CheckCircleIcon,
  CloseLineIcon,
  TimeIcon,
} from "@/icons";

interface SessionTableProps {
  initialSessions: InterviewSession[];
}

export default function SessionTable({ initialSessions }: SessionTableProps) {
  const [sessions, setSessions] = useState<InterviewSession[]>(initialSessions);
  const [searchQuery, setSearchQuery] = useState("");
  const [consentFilter, setConsentFilter] = useState<string>("ALL");
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Filter sessions
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

  const handleAddSession = (newSession: InterviewSession) => {
    setSessions([newSession, ...sessions]);
  };

  const getJobStatusBadge = (status: string) => {
    switch (status) {
      case "COMPLETED":
        return (
          <span className="inline-flex items-center gap-1 rounded-md bg-success-50 px-2 py-0.5 text-[11px] font-semibold text-success-700 dark:bg-success-500/15 dark:text-success-400">
            <CheckCircleIcon/>
            COMPLETED
          </span>
        );
      case "IN_REVIEW":
        return (
          <span className="inline-flex items-center gap-1 rounded-md bg-brand-50 px-2 py-0.5 text-[11px] font-semibold text-brand-700 dark:bg-brand-500/15 dark:text-brand-400 animate-pulse">
            <TimeIcon/>
            IN_REVIEW
          </span>
        );
      case "REJECTED_NO_CONSENT":
        return (
          <span className="inline-flex items-center gap-1 rounded-md bg-error-50 px-2 py-0.5 text-[11px] font-semibold text-error-700 dark:bg-error-500/15 dark:text-error-400">
            <CloseLineIcon/>
            NO_CONSENT
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center rounded-md bg-gray-100 px-2 py-0.5 text-[11px] font-semibold text-gray-700 dark:bg-gray-800 dark:text-gray-300">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-4">
      {/* Search and Action Bar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-1 flex-wrap items-center gap-2.5">
          <div className="relative min-w-[240px] flex-1 sm:max-w-xs">
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search candidate, code, or role..."
              className="w-full rounded-xl border border-gray-300 bg-white py-2 pl-9 pr-3 text-xs text-gray-800 placeholder-gray-400 focus:border-brand-500 focus:outline-hidden focus:ring-1 focus:ring-brand-500 dark:border-gray-700 dark:bg-gray-900 dark:text-white"
            />
          </div>

          <select
            value={consentFilter}
            onChange={(e) => setConsentFilter(e.target.value)}
            className="rounded-xl border border-gray-300 bg-white px-3 py-2 text-xs font-medium text-gray-700 focus:border-brand-500 focus:outline-hidden dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300"
          >
            <option value="ALL">All Consent Statuses</option>
            <option value="GRANTED">Granted</option>
            <option value="NOT_GRANTED">Not Granted</option>
            <option value="WITHDRAWN">Withdrawn</option>
          </select>
        </div>

        <Button variant="primary" size="sm" onClick={() => setIsModalOpen(true)} startIcon={<PlusIcon/>}>
          Upload Audio Recording
        </Button>
      </div>

      {/* Table Card */}
      <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-theme-xs dark:border-gray-800 dark:bg-gray-900">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader className="border-b border-gray-100 bg-gray-50/50 dark:border-gray-800 dark:bg-gray-800/50">
              <TableRow>
                <TableCell isHeader className="py-3.5 pl-5 text-start text-xs font-semibold text-gray-600 dark:text-gray-400">
                  Candidate
                </TableCell>
                <TableCell isHeader className="py-3.5 text-start text-xs font-semibold text-gray-600 dark:text-gray-400">
                  Position & Round
                </TableCell>
                <TableCell isHeader className="py-3.5 text-start text-xs font-semibold text-gray-600 dark:text-gray-400">
                  Interviewer
                </TableCell>
                <TableCell isHeader className="py-3.5 text-start text-xs font-semibold text-gray-600 dark:text-gray-400">
                  Consent Status
                </TableCell>
                <TableCell isHeader className="py-3.5 text-start text-xs font-semibold text-gray-600 dark:text-gray-400">
                  Audio Duration
                </TableCell>
                <TableCell isHeader className="py-3.5 text-start text-xs font-semibold text-gray-600 dark:text-gray-400">
                  Job Pipeline
                </TableCell>
                <TableCell isHeader className="py-3.5 pr-5 text-end text-xs font-semibold text-gray-600 dark:text-gray-400">
                  Action
                </TableCell>
              </TableRow>
            </TableHeader>

            <TableBody className="divide-y divide-gray-100 dark:divide-gray-800">
              {filteredSessions.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-12 text-center text-xs text-gray-400">
                    No interview sessions found matching current filter
                  </TableCell>
                </TableRow>
              ) : (
                filteredSessions.map((session) => (
                  <TableRow key={session.id} className="hover:bg-gray-50/60 dark:hover:bg-gray-800/40 transition-colors">
                    <TableCell className="py-4 pl-5">
                      <div className="flex items-center gap-2.5">
                        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-50 font-bold text-xs text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
                          {session.candidate_name
                            .split(" ")
                            .map((n) => n[0])
                            .slice(0, 2)
                            .join("")}
                        </div>
                        <div>
                          <div className="flex items-center gap-1.5">
                            <span className="font-semibold text-xs text-gray-900 dark:text-white">
                              {session.candidate_name}
                            </span>
                            <span className="rounded bg-gray-100 px-1.5 py-0.2 font-mono text-[10px] text-gray-600 dark:bg-gray-800 dark:text-gray-300">
                              {session.candidate_code}
                            </span>
                          </div>
                          <span className="text-[11px] text-gray-500 dark:text-gray-400">
                            {session.scheduled_at}
                          </span>
                        </div>
                      </div>
                    </TableCell>

                    <TableCell className="py-4">
                      <div>
                        <span className="font-medium text-xs text-gray-800 dark:text-gray-200">
                          {session.position}
                        </span>
                        <span className="block text-[11px] text-gray-500 dark:text-gray-400">
                          {session.round_name}
                        </span>
                      </div>
                    </TableCell>

                    <TableCell className="py-4">
                      <div>
                        <span className="font-medium text-xs text-gray-800 dark:text-gray-200">
                          {session.interviewer_name}
                        </span>
                        <span className="block text-[11px] text-gray-500 dark:text-gray-400">
                          {session.interviewer_role}
                        </span>
                      </div>
                    </TableCell>

                    <TableCell className="py-4">
                      <ConsentBadge status={session.consent_status} />
                    </TableCell>

                    <TableCell className="py-4">
                      <div className="inline-flex items-center gap-1.5 text-xs font-mono text-gray-700 dark:text-gray-300">
                        <AudioIcon className="text-brand-500" />
                        <span>{session.audio_duration || "00:00"}</span>
                      </div>
                    </TableCell>

                    <TableCell className="py-4">
                      {getJobStatusBadge(session.job_status)}
                    </TableCell>

                    <TableCell className="py-4 pr-5 text-end">
                      <div className="flex items-center justify-end gap-2">
                        {session.consent_status === "GRANTED" ? (
                          <Link
                            href={`/interviews/review?id=${session.id}`}
                            className="inline-flex items-center gap-1.5 rounded-lg border border-brand-200 bg-brand-50 px-2.5 py-1.5 text-xs font-semibold text-brand-700 hover:bg-brand-100 dark:border-brand-500/30 dark:bg-brand-500/10 dark:text-brand-300"
                          >
                            <DocsIcon/>
                            <span>Review Evidence</span>
                          </Link>
                        ) : (
                          <span className="text-[11px] text-gray-400 italic">
                            Blocked (No Consent)
                          </span>
                        )}

                        <Link
                          href={`/orchestration/scheduling?candidateId=${session.candidate_id}`}
                          className="inline-flex items-center gap-1 rounded-lg border border-gray-200 bg-white px-2 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-800 dark:bg-gray-800 dark:text-gray-300"
                          title="Schedule follow-up round"
                        >
                          <BoltIcon/>
                        </Link>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      <AudioUploadModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleAddSession}
      />
    </div>
  );
}
