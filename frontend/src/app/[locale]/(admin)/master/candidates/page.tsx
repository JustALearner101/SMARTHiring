"use client";

import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import FormField from "@/components/form/FormField";
import InputField from "@/components/form/input/InputField";
import TextArea from "@/components/form/input/TextArea";
import Select from "@/components/form/Select";
import Badge from "@/components/ui/badge/Badge";
import Button from "@/components/ui/button/Button";
import { ConfirmationModal, Modal } from "@/components/ui/modal";
import {
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { Link } from "@/i18n/navigation";
import {
  AlertIcon,
  AudioIcon,
  BoltIcon,
  CheckCircleIcon,
  InfoIcon,
  LockIcon,
  PencilIcon,
  PlusIcon,
  TrashBinIcon,
} from "@/icons";
import { masterService } from "@/services";
import TablePagination from "@/components/common/TablePagination";
import {
  ApplicationStatus,
  Candidate,
  PaginatedResponse,
  PreferredChannel,
  Timezone,
} from "@/types/master";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

export default function CandidatesPage() {
  const { role } = useAuth();
  const canManageCandidates = role === "HR" || role === "ADMIN";
  const { showSuccess, showError } = useToast();
  const [isSaving, setIsSaving] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [timezoneFilter, setTimezoneFilter] = useState<string>("ALL");
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);

  // Modals
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [isSaveConfirmOpen, setIsSaveConfirmOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [activeCandidate, setActiveCandidate] = useState<Candidate | null>(null);

  // Re-application Modal State (Repeat Applicant Cycle)
  const [reapplyTarget, setReapplyTarget] = useState<Candidate | null>(null);
  const [reapplyPosition, setReapplyPosition] = useState("");
  const [reapplyNotes, setReapplyNotes] = useState("");
  const [isReapplyModalOpen, setIsReapplyModalOpen] = useState(false);

  // Offering Transition Confirmation Modal (from Technical Test / On Hold)
  const [offerTarget, setOfferTarget] = useState<Candidate | null>(null);

  // Form State (Status is system-managed automatically, never manually typed)
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    preferred_channel: "whatsapp" as PreferredChannel,
    applied_position: "",
    timezone: "WIB" as Timezone,
    resume_url: "",
    notes: "",
    current_salary: "" as string | number,
    expected_salary: "" as string | number,
  });

  // TanStack Query: Caches candidates in memory and syncs automatically on workflow invalidations
  const queryClient = useQueryClient();
  const { data: candidatesData, isLoading } = useQuery({
    queryKey: ["candidates"],
    queryFn: () => masterService.listCandidates({ page_size: 100 }),
  });

  const candidates = useMemo(() => candidatesData?.items || [], [candidatesData]);

  // Filtered List
  const filteredCandidates = useMemo(() => {
    return candidates.filter((cand) => {
      const q = searchQuery.toLowerCase();
      const matchesSearch =
        cand.name.toLowerCase().includes(q) ||
        cand.candidate_code.toLowerCase().includes(q) ||
        cand.applied_position.toLowerCase().includes(q) ||
        cand.email.toLowerCase().includes(q);

      const matchesStatus = statusFilter === "ALL" || cand.status === statusFilter;
      const matchesTimezone = timezoneFilter === "ALL" || cand.timezone === timezoneFilter;

      return matchesSearch && matchesStatus && matchesTimezone;
    });
  }, [candidates, searchQuery, statusFilter, timezoneFilter]);

  const totalPages = Math.ceil(filteredCandidates.length / pageSize) || 1;
  const paginatedCandidates = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredCandidates.slice(start, start + pageSize);
  }, [filteredCandidates, currentPage, pageSize]);

  // Detect prior application history by email while filling "Add New Candidate"
  const matchingPriorApplications = useMemo(() => {
    if (activeCandidate || !formData.email.trim()) return [];
    const targetEmail = formData.email.trim().toLowerCase();
    return candidates.filter((c) => c.email.trim().toLowerCase() === targetEmail);
  }, [activeCandidate, candidates, formData.email]);

  const hasActiveDuplicateInForm = useMemo(() => {
    if (!formData.applied_position.trim()) return false;
    const targetPos = formData.applied_position.trim().toLowerCase();
    return matchingPriorApplications.some(
      (c) =>
        c.applied_position.trim().toLowerCase() === targetPos &&
        c.status !== "REJECTED" &&
        c.status !== "OFFERED"
    );
  }, [formData.applied_position, matchingPriorApplications]);

  const hasNewerActiveCycleForRole = (cand: Candidate) =>
    candidates.some(
      (other) =>
        other.id !== cand.id &&
        other.email.trim().toLowerCase() === cand.email.trim().toLowerCase() &&
        other.applied_position.trim().toLowerCase() ===
          cand.applied_position.trim().toLowerCase() &&
        other.status !== "REJECTED" &&
        other.status !== "OFFERED"
    );

  // Open Add Modal
  const handleOpenAdd = () => {
    setActiveCandidate(null);
    setFormData({
      name: "",
      email: "",
      phone: "",
      preferred_channel: "whatsapp",
      applied_position: "",
      timezone: "WIB",
      resume_url: "",
      notes: "",
      current_salary: "",
      expected_salary: "",
    });
    setIsFormModalOpen(true);
  };

  // Open Edit Modal
  const handleOpenEdit = (cand: Candidate) => {
    setActiveCandidate(cand);
    setFormData({
      name: cand.name,
      email: cand.email,
      phone: cand.phone,
      preferred_channel: cand.preferred_channel,
      applied_position: cand.applied_position,
      timezone: cand.timezone,
      resume_url: cand.resume_url || "",
      notes: cand.notes || "",
      current_salary: cand.current_salary ?? "",
      expected_salary: cand.expected_salary ?? "",
    });
    setIsFormModalOpen(true);
  };

  // Step 1: Pre-save validation & trigger Confirmation Modal
  const handlePreSaveCandidate = () => {
    if (!formData.name.trim() || !formData.email.trim() || !formData.applied_position.trim()) {
      showError(
        "Form Validation Failed",
        "Please provide the candidate's name, email, and applied position before saving."
      );
      return;
    }
    if (!activeCandidate && hasActiveDuplicateInForm) {
      showError(
        "Active Application Already Exists",
        "A candidate with this email already has an active application for the same position."
      );
      return;
    }
    setIsSaveConfirmOpen(true);
  };

  // Step 2: Execute Save Candidate upon user confirmation
  const handleExecuteSaveCandidate = async () => {
    const editing = activeCandidate;
    const currentSalaryNum =
      formData.current_salary !== "" && !Number.isNaN(Number(formData.current_salary))
        ? Number(formData.current_salary)
        : undefined;
    const expectedSalaryNum =
      formData.expected_salary !== "" && !Number.isNaN(Number(formData.expected_salary))
        ? Number(formData.expected_salary)
        : undefined;

    setIsSaving(true);

    try {
      if (editing) {
        const updated = await masterService.updateCandidate(editing.id, {
          name: formData.name,
          email: formData.email,
          phone: formData.phone,
          preferred_channel: formData.preferred_channel,
          applied_position: formData.applied_position,
          timezone: formData.timezone,
          resume_url: formData.resume_url,
          notes: formData.notes,
          current_salary: currentSalaryNum,
          expected_salary: expectedSalaryNum,
        });
        queryClient.setQueryData(
          ["candidates"],
          (old: PaginatedResponse<Candidate> | undefined) => ({
            items: [
              updated,
              ...(old?.items || []).filter((c) => c.id !== editing.id),
            ],
            total: old?.total || 0,
            page: old?.page || 1,
            page_size: old?.page_size || 100,
            total_pages: old?.total_pages || 1,
          })
        );
        showSuccess(
          "Candidate Updated",
          `Candidate profile for ${formData.name} successfully saved to the database.`
        );
      } else {
        const created = await masterService.createCandidate({
          name: formData.name,
          email: formData.email,
          phone: formData.phone,
          preferred_channel: formData.preferred_channel,
          applied_position: formData.applied_position,
          status: "SCREENING",
          timezone: formData.timezone,
          resume_url: formData.resume_url,
          notes: formData.notes,
          current_salary: currentSalaryNum,
          expected_salary: expectedSalaryNum,
        });
        queryClient.setQueryData(
          ["candidates"],
          (old: PaginatedResponse<Candidate> | undefined) => ({
            items: [created, ...(old?.items || [])],
            total: (old?.total || 0) + 1,
            page: old?.page || 1,
            page_size: old?.page_size || 100,
            total_pages: old?.total_pages || 1,
          })
        );
        const cycleLabel =
          (created.application_cycle ?? 1) > 1
            ? ` (Cycle #${created.application_cycle})`
            : "";
        showSuccess(
          "Candidate Added",
          `Candidate ${formData.name} (${created.candidate_code})${cycleLabel} automatically entered the Screening stage.`
        );
      }
      void queryClient.invalidateQueries({ queryKey: ["candidates"] });
      setIsSaveConfirmOpen(false);
      setIsFormModalOpen(false);
    } catch (error) {
      console.error("Failed to save candidate:", error);
      const msg =
        error instanceof Error
          ? error.message
          : "An error occurred while saving candidate data to the server.";
      showError("Failed to Save Data", msg);
    } finally {
      setIsSaving(false);
    }
  };

  // Execute 1-Click Re-application (New Application Cycle for REJECTED Candidate)
  const handleExecuteReapply = async () => {
    if (!reapplyTarget) return;
    setIsSaving(true);
    try {
      const created = await masterService.reapplyCandidate(reapplyTarget.id, {
        applied_position: reapplyPosition.trim() || reapplyTarget.applied_position,
        notes: reapplyNotes.trim() || undefined,
      });
      queryClient.setQueryData(
        ["candidates"],
        (old: PaginatedResponse<Candidate> | undefined) => ({
          items: [created, ...(old?.items || [])],
          total: (old?.total || 0) + 1,
          page: old?.page || 1,
          page_size: old?.page_size || 100,
          total_pages: old?.total_pages || 1,
        })
      );
      void queryClient.invalidateQueries({ queryKey: ["candidates"] });
      setIsReapplyModalOpen(false);
      setReapplyTarget(null);
      showSuccess(
        `New Cycle Created (Cycle #${created.application_cycle ?? 2})`,
        `${created.name} re-registered as ${created.candidate_code} with initial status Screening. Prior history remains intact for audit.`
      );
    } catch (error) {
      console.error("Failed to reapply candidate:", error);
      const msg =
        error instanceof Error
          ? error.message
          : "Failed to create a new application cycle for this candidate.";
      showError("Re-application Failed", msg);
    } finally {
      setIsSaving(false);
    }
  };

  // Execute Move to Offering (for candidates passing Technical Test / On Hold)
  const handleConfirmMoveToOffering = async () => {
    if (!offerTarget) return;
    setIsSaving(true);
    try {
      const updated = await masterService.updateCandidate(offerTarget.id, {
        status: "OFFERED",
      });
      queryClient.setQueryData(
        ["candidates"],
        (old: PaginatedResponse<Candidate> | undefined) => ({
          items: [
            updated,
            ...(old?.items || []).filter((c) => c.id !== offerTarget.id),
          ],
          total: old?.total || 0,
          page: old?.page || 1,
          page_size: old?.page_size || 100,
          total_pages: old?.total_pages || 1,
        })
      );
      void queryClient.invalidateQueries({ queryKey: ["candidates"] });
      showSuccess(
        "Status Advanced to Offering",
        `${offerTarget.name} (${offerTarget.candidate_code}) has been advanced to the Offering stage.`
      );
      setOfferTarget(null);
    } catch (error) {
      console.error("Failed to advance candidate to offering:", error);
      const msg =
        error instanceof Error ? error.message : "Failed to update candidate status to Offering.";
      showError("Failed to Update Status", msg);
    } finally {
      setIsSaving(false);
    }
  };

  // Confirm Delete (Wired to guarded backend DELETE /api/v1/candidates/{id})
  const handleConfirmDelete = async () => {
    if (!activeCandidate) return;
    const targetId = activeCandidate.id;
    const targetName = activeCandidate.name;
    setIsSaving(true);
    try {
      await masterService.deleteCandidate(targetId);
      queryClient.setQueryData(
        ["candidates"],
        (old: PaginatedResponse<Candidate> | undefined) => ({
          items: (old?.items || []).filter((c) => c.id !== targetId),
          total: Math.max(0, (old?.total || 1) - 1),
          page: old?.page || 1,
          page_size: old?.page_size || 100,
          total_pages: old?.total_pages || 1,
        })
      );
      void queryClient.invalidateQueries({ queryKey: ["candidates"] });
      setIsDeleteModalOpen(false);
      setActiveCandidate(null);
      showSuccess("Candidate Deleted", `Candidate data for ${targetName} was successfully deleted from the database.`);
    } catch (error) {
      console.error("Failed to delete candidate:", error);
      const msg =
        error instanceof Error
          ? error.message
          : "Failed to delete candidate. Candidate may be linked to interview history records.";
      showError("Cannot Delete Candidate", msg);
    } finally {
      setIsSaving(false);
    }
  };

  // Render Status Badge
  const renderStatusBadge = (status: ApplicationStatus) => {
    switch (status) {
      case "ESCALATED":
        return (
          <Badge color="warning" size="sm">
            Next Round Ready
          </Badge>
        );
      case "INTERVIEW_SCHEDULED":
        return (
          <Badge color="primary" size="sm">
            Scheduled
          </Badge>
        );
      case "PENDING_HR_REVIEW":
        return (
          <Badge color="warning" size="sm">
            Pending HR Follow-Up
          </Badge>
        );
      case "TECHNICAL_TEST":
        return (
          <Badge color="info" size="sm">
            Technical Test
          </Badge>
        );
      case "COMPLETED":
        return (
          <Badge color="info" size="sm">
            On Hold (Reviewed)
          </Badge>
        );
      case "OFFERED":
        return (
          <Badge color="success" size="sm">
            Offering
          </Badge>
        );
      case "REJECTED":
        return (
          <Badge color="error" size="sm">
            Rejected
          </Badge>
        );
      default:
        return (
          <Badge color="light" size="sm">
            Screening
          </Badge>
        );
    }
  };

  // Context-Aware Workflow Action per Status
  const renderWorkflowAction = (cand: Candidate) => {
    if (cand.status === "SCREENING" || cand.status === "ESCALATED") {
      const isNextRound = cand.status === "ESCALATED";
      return (
        <Link
          href={`/orchestration/scheduling?candidateId=${cand.id}`}
          className="inline-flex items-center gap-1.5 rounded-lg bg-brand-500 px-3 py-1.5 text-xs font-semibold text-white shadow-theme-xs hover:bg-brand-600 active:bg-brand-700 transition-all duration-150"
          title={
            isNextRound
              ? "Jadwalkan interview tahap berikutnya (User / Technical)"
              : "Eskalasi & jadwalkan HR Interview via AI Orchestrator"
          }
        >
          <BoltIcon className="text-white" />
          <span>{isNextRound ? "Schedule Next" : "Schedule HR"}</span>
        </Link>
      );
    }

    if (cand.status === "INTERVIEW_SCHEDULED") {
      return (
        <Link
          href={`/interviews/sessions?candidateId=${cand.id}&action=upload`}
          className="inline-flex items-center gap-1.5 rounded-lg border border-brand-200 bg-brand-50 px-3 py-1.5 text-xs font-semibold text-brand-700 shadow-theme-xs hover:bg-brand-100 dark:border-brand-500/30 dark:bg-brand-500/15 dark:text-brand-300 transition-all duration-150"
          title="Upload interview recording to AI Copilot"
        >
          <AudioIcon />
          <span>Upload Audio</span>
        </Link>
      );
    }

    if (cand.status === "PENDING_HR_REVIEW") {
      return (
        <Link
          href={`/interviews/sessions?scope=awaiting_hr&candidateCode=${encodeURIComponent(cand.candidate_code)}`}
          className="inline-flex items-center gap-1.5 rounded-lg bg-warning-500 px-3 py-1.5 text-xs font-semibold text-white shadow-theme-xs hover:bg-warning-600 transition-all duration-150"
          title="Review the interviewer's evaluation results and provide final HR follow-up"
        >
          <CheckCircleIcon className="text-white" />
          <span>HR Follow-Up</span>
        </Link>
      );
    }

    if (cand.status === "TECHNICAL_TEST" || cand.status === "COMPLETED") {
      return (
        <div className="inline-flex items-center gap-1.5">
          <Link
            href={`/orchestration/scheduling?candidateId=${cand.id}`}
            className="inline-flex items-center gap-1 rounded-lg border border-gray-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-gray-700 shadow-theme-xs hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200"
            title="Schedule a follow-up interview"
          >
            <BoltIcon />
            <span>Schedule</span>
          </Link>
          {canManageCandidates && (
            <button
              type="button"
              onClick={() => setOfferTarget(cand)}
              className="inline-flex items-center gap-1 rounded-lg bg-success-600 px-2.5 py-1.5 text-xs font-semibold text-white shadow-theme-xs hover:bg-success-700 transition-all"
              title="Advance the candidate to the Offering stage"
            >
              <CheckCircleIcon />
              <span>Offer</span>
            </button>
          )}
        </div>
      );
    }

    if (cand.status === "REJECTED" && canManageCandidates) {
      const alreadyReapplied = hasNewerActiveCycleForRole(cand);
      return (
        <button
          type="button"
          disabled={alreadyReapplied}
          onClick={() => {
            setReapplyTarget(cand);
            setReapplyPosition(cand.applied_position);
            setReapplyNotes("");
            setIsReapplyModalOpen(true);
          }}
          className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-2.5 py-1.5 text-xs font-semibold text-gray-700 shadow-theme-xs hover:border-brand-400 hover:text-brand-600 disabled:cursor-not-allowed disabled:opacity-45 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:border-brand-500/40 dark:hover:text-brand-400 transition-all"
          title={
            alreadyReapplied
              ? "A new application cycle for this candidate is already active"
              : "Register a new application cycle (Re-apply) while preserving past history"
          }
        >
          <PlusIcon />
          <span>{alreadyReapplied ? "Cycle Active" : "Re-apply"}</span>
        </button>
      );
    }

    return null;
  };

  return (
    <div>
      <PageBreadcrumb pageTitle="Candidates Directory" />

      {/* Main Container */}
      <div className="rounded-2xl border border-gray-200 bg-white p-5 xl:p-6 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
        {/* Header Actions */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between pb-5 border-b border-gray-100 dark:border-gray-800">
          <div>
            <h3 className="text-theme-xl font-semibold text-gray-800 dark:text-white/90">
              Candidate List
            </h3>
            <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
              Application status advances automatically according to AI Scheduling, Interview Copilot, and HR decisions in Review &amp; Evidence.
            </p>
          </div>
          <Button
            variant="primary"
            size="sm"
            startIcon={<PlusIcon />}
            onClick={handleOpenAdd}
            disabled={!canManageCandidates}
            title={!canManageCandidates ? "Only HR or Admin can add candidates" : "Add new candidate"}
          >
            Add Candidate
          </Button>
        </div>

        {/* Filter Controls Bar */}
        <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-12">
          <div className="sm:col-span-6">
            <InputField
              placeholder="Search name, code, email, or position..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setCurrentPage(1);
              }}
            />
          </div>

          <div className="sm:col-span-3">
            <Select
              options={[
                { value: "ALL", label: "All Status" },
                { value: "SCREENING", label: "Screening" },
                { value: "INTERVIEW_SCHEDULED", label: "Scheduled" },
                { value: "PENDING_HR_REVIEW", label: "Pending HR Follow-Up" },
                { value: "ESCALATED", label: "Next Round Ready" },
                { value: "TECHNICAL_TEST", label: "Technical Test" },
                { value: "COMPLETED", label: "On Hold (Reviewed)" },
                { value: "OFFERED", label: "Offering" },
                { value: "REJECTED", label: "Rejected" },
              ]}
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setCurrentPage(1);
              }}
            />
          </div>

          <div className="sm:col-span-3">
            <Select
              options={[
                { value: "ALL", label: "All Timezone" },
                { value: "WIB", label: "WIB (UTC+7)" },
                { value: "WITA", label: "WITA (UTC+8)" },
                { value: "WIT", label: "WIT (UTC+9)" },
              ]}
              value={timezoneFilter}
              onChange={(e) => {
                setTimezoneFilter(e.target.value);
                setCurrentPage(1);
              }}
            />
          </div>
        </div>

        {/* Candidates Table */}
        <div className="mt-5 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-2xs dark:border-gray-800 dark:bg-gray-900">
          <div className="max-w-full overflow-x-auto">
            <Table>
            <TableHeader className="bg-gray-50 dark:bg-gray-800/60 border-b border-gray-200 dark:border-gray-800">
              <TableRow>
                <TableCell isHeader className="ps-4 pe-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300">
                  Candidate
                </TableCell>
                <TableCell isHeader className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300">
                  Applied Position
                </TableCell>
                <TableCell isHeader className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300">
                  Salary (Cur / Exp)
                </TableCell>
                <TableCell isHeader className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300">
                  Preferred Channel
                </TableCell>
                <TableCell isHeader className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300">
                  Timezone
                </TableCell>
                <TableCell isHeader className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300">
                  Application Status
                </TableCell>
                <TableCell isHeader className="pe-5 ps-3 py-3 text-end text-xs font-semibold text-gray-600 dark:text-gray-300">
                  Workflow Action
                </TableCell>
              </TableRow>
            </TableHeader>
            <TableBody className="divide-y divide-gray-100 dark:divide-gray-800">
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-8 text-center text-xs text-gray-400">
                    Loading candidates from database...
                  </TableCell>
                </TableRow>
              ) : filteredCandidates.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-8 text-center text-xs text-gray-400">
                    No candidate data matches the search criteria.
                  </TableCell>
                </TableRow>
              ) : (
                paginatedCandidates.map((cand) => (
                  <TableRow key={cand.id} className="hover:bg-gray-50/70 dark:hover:bg-white/[0.02] transition-colors">
                    {/* Candidate Info */}
                    <TableCell className="ps-4 pe-3 py-3.5">
                      <div className="flex flex-col">
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span className="font-semibold text-sm text-gray-900 dark:text-white/90">
                            {cand.name}
                          </span>
                          {(cand.application_cycle ?? 1) > 1 && (
                            <span className="inline-flex items-center rounded-md bg-warning-50 px-1.5 py-0.5 text-[10px] font-bold text-warning-700 dark:bg-warning-500/15 dark:text-warning-300">
                              Cycle #{cand.application_cycle}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-[11px] font-mono font-medium text-brand-600 dark:text-brand-400">
                            {cand.candidate_code}
                          </span>
                          <span className="text-gray-300 dark:text-gray-700">&bull;</span>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {cand.email}
                          </span>
                        </div>
                      </div>
                    </TableCell>

                    {/* Position */}
                    <TableCell className="px-3 py-3.5 text-xs text-gray-700 dark:text-gray-300 font-medium">
                      {cand.applied_position}
                    </TableCell>

                    {/* Salary (Role Guarded: Visible to HR & Admin) */}
                    <TableCell className="px-3 py-3.5">
                      {canManageCandidates ? (
                        cand.current_salary != null || cand.expected_salary != null ? (
                          <div className="flex flex-col text-xs font-mono">
                            <span className="font-semibold text-gray-800 dark:text-gray-200">
                              Exp:{" "}
                              {cand.expected_salary
                                ? `Rp ${(cand.expected_salary / 1000000).toLocaleString("id-ID")}M`
                                : "-"}
                            </span>
                            <span className="text-[11px] text-gray-500 dark:text-gray-400">
                              Cur:{" "}
                              {cand.current_salary
                                ? `Rp ${(cand.current_salary / 1000000).toLocaleString("id-ID")}M`
                                : "-"}
                            </span>
                          </div>
                        ) : (
                          <span className="text-xs text-gray-400">-</span>
                        )
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-500 dark:bg-gray-800 dark:text-gray-400">
                          <LockIcon />
                          <span>Confidential (HR)</span>
                        </span>
                      )}
                    </TableCell>

                    {/* Preferred Channel */}
                    <TableCell className="px-3 py-3.5">
                      <div className="flex flex-col gap-0.5">
                        <div className="flex items-center gap-1.5">
                          {cand.preferred_channel === "whatsapp" ? (
                            <span className="inline-flex items-center rounded-md bg-success-50 px-2 py-0.5 text-[10px] font-medium text-success-600 dark:bg-success-500/15 dark:text-success-400">
                              WhatsApp
                            </span>
                          ) : (
                            <span className="inline-flex items-center rounded-md bg-brand-50 px-2 py-0.5 text-[10px] font-medium text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
                              Email
                            </span>
                          )}
                        </div>
                        <span className="text-[11px] text-gray-500 dark:text-gray-400">
                          {cand.phone}
                        </span>
                      </div>
                    </TableCell>

                    {/* Timezone */}
                    <TableCell className="px-3 py-3.5">
                      <span className="inline-flex items-center rounded-md bg-gray-100 px-2 py-0.5 text-xs font-mono font-medium text-gray-700 dark:bg-gray-800 dark:text-gray-300">
                        {cand.timezone}
                      </span>
                    </TableCell>

                    {/* Status */}
                    <TableCell className="px-3 py-3.5">
                      {renderStatusBadge(cand.status)}
                    </TableCell>

                    {/* Actions */}
                    <TableCell className="pe-5 ps-3 py-3.5 text-end whitespace-nowrap">
                      <div className="flex items-center justify-end gap-1.5">
                        {renderWorkflowAction(cand)}

                        {/* Edit & Delete: HR & Admin */}
                        {canManageCandidates && (
                          <>
                            <button
                              type="button"
                              onClick={() => handleOpenEdit(cand)}
                              className="h-8 w-8 inline-flex items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-600 shadow-theme-xs hover:border-brand-300 hover:bg-gray-50 hover:text-brand-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:border-brand-500/30 dark:hover:bg-gray-700/60 dark:hover:text-brand-400 transition-all"
                              title="Edit Profil Kandidat"
                            >
                              <PencilIcon />
                            </button>

                            <button
                              type="button"
                              onClick={() => {
                                setActiveCandidate(cand);
                                setIsDeleteModalOpen(true);
                              }}
                              className="h-8 w-8 inline-flex items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-500 shadow-theme-xs hover:border-error-300 hover:bg-error-50 hover:text-error-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:hover:border-error-500/30 dark:hover:bg-error-500/15 dark:hover:text-error-400 transition-all"
                              title="Delete Candidate"
                            >
                              <TrashBinIcon />
                            </button>
                          </>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Table Pagination */}
        <TablePagination
          currentPage={currentPage}
          totalPages={totalPages}
          totalItems={filteredCandidates.length}
          pageSize={pageSize}
          onPageChange={setCurrentPage}
          onPageSizeChange={(newSize) => {
            setPageSize(newSize);
            setCurrentPage(1);
          }}
          pageSizeOptions={[10, 20, 50, 100]}
          isLoading={isLoading}
        />
        </div>
      </div>

      {/* Unified Candidate Form Modal (Add / Edit — No Manual Status Override) */}
      <Modal isOpen={isFormModalOpen} onClose={() => setIsFormModalOpen(false)} className="max-w-4xl m-4">
        <div className="p-8 sm:p-10">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {activeCandidate
              ? `Edit Candidate Profile`
              : "Add New Candidate"}
          </h3>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {activeCandidate
              ? "Update candidate profile and communication preferences. Application status is managed automatically by the system."
              : "New candidates automatically enter the Screening stage and are ready to be scheduled for an HR Interview."}
          </p>

          {/* Repeat Applicant / Duplicate Live Detection Banner */}
          {!activeCandidate && matchingPriorApplications.length > 0 && (
            <div
              className={`mt-4 flex items-start gap-2.5 rounded-xl border p-3.5 text-xs ${
                hasActiveDuplicateInForm
                  ? "border-error-200 bg-error-50 text-error-800 dark:border-error-500/30 dark:bg-error-500/10 dark:text-error-300"
                  : "border-warning-200 bg-warning-50 text-warning-800 dark:border-warning-500/30 dark:bg-warning-500/10 dark:text-warning-300"
              }`}
            >
              {hasActiveDuplicateInForm ? (
                <AlertIcon className="shrink-0 mt-0.5" />
              ) : (
                <InfoIcon className="shrink-0 mt-0.5" />
              )}
              <div className="text-start">
                {hasActiveDuplicateInForm ? (
                  <span>
                    <strong>Active Application Detected:</strong> This candidate already has an active application for position{" "}
                    <strong>{formData.applied_position}</strong>. Please use the ongoing application.
                  </span>
                ) : (
                  <span>
                    <strong>Prior Applicant History Detected ({matchingPriorApplications[0].candidate_code} &bull; {matchingPriorApplications[0].status}):</strong>{" "}
                    Saving this will automatically create a new <strong>Cycle #{(matchingPriorApplications[0].application_cycle ?? 1) + 1}</strong> with status{" "}
                    <strong>Screening</strong> while preserving prior evaluation history intact.
                  </span>
                )}
              </div>
            </div>
          )}

          <div className="mt-5 space-y-3.5">
            <FormField label="Full Name" required>
              <InputField
                placeholder="e.g., Rina Kusuma"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </FormField>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <FormField label="Email" required>
                <InputField
                  type="email"
                  placeholder="rina@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </FormField>

              <FormField label="Phone Number" required>
                <InputField
                  placeholder="+628123456789"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                />
              </FormField>
            </div>

            <FormField label="Position Applied" required>
              <InputField
                placeholder="e.g., Senior Frontend Engineer"
                value={formData.applied_position}
                onChange={(e) => setFormData({ ...formData, applied_position: e.target.value })}
              />
            </FormField>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <FormField label="Preferred Channel" required>
                <Select
                  options={[
                    { value: "whatsapp", label: "WhatsApp" },
                    { value: "email", label: "Email" },
                  ]}
                  value={formData.preferred_channel}
                  onChange={(e) =>
                    setFormData({ ...formData, preferred_channel: e.target.value as PreferredChannel })
                  }
                />
              </FormField>

              <FormField label="Timezone" required>
                <Select
                  options={[
                    { value: "WIB", label: "WIB (UTC+7)" },
                    { value: "WITA", label: "WITA (UTC+8)" },
                    { value: "WIT", label: "WIT (UTC+9)" },
                  ]}
                  value={formData.timezone}
                  onChange={(e) => setFormData({ ...formData, timezone: e.target.value as Timezone })}
                />
              </FormField>
            </div>

            {/* Salary Data (HR & Admin Only) */}
            {canManageCandidates && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-3 rounded-xl border border-brand-100 bg-brand-50/40 dark:border-brand-900/40 dark:bg-brand-950/20">
                <FormField label="Current Salary (IDR)" hint="Confidential - HR Only">
                  <InputField
                    type="number"
                    placeholder="e.g. 20000000"
                    value={formData.current_salary}
                    onChange={(e) => setFormData({ ...formData, current_salary: e.target.value })}
                  />
                </FormField>

                <FormField label="Expected Salary (IDR)" hint="Confidential - HR Only">
                  <InputField
                    type="number"
                    placeholder="e.g. 26000000"
                    value={formData.expected_salary}
                    onChange={(e) => setFormData({ ...formData, expected_salary: e.target.value })}
                  />
                </FormField>
              </div>
            )}

            <FormField label="Additional Notes" hint="Notes will be referenced by AI when composing the invitation draft.">
              <TextArea
                rows={2}
                placeholder="e.g. Passed initial CV screening. Prefers morning interview slots."
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              />
            </FormField>
          </div>

          <div className="mt-6 flex justify-end gap-2.5 pt-3 border-t border-gray-100 dark:border-gray-800">
            <Button variant="outline" disabled={isSaving} onClick={() => setIsFormModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" disabled={isSaving} onClick={handlePreSaveCandidate}>
              {activeCandidate ? "Update Profile" : "Save Candidate"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Re-application Cycle Modal for REJECTED Candidates */}
      <Modal
        isOpen={isReapplyModalOpen}
        onClose={() => setIsReapplyModalOpen(false)}
        className="max-w-lg m-4"
      >
        <div className="p-6 sm:p-8">
          <h3 className="text-base font-semibold text-gray-900 dark:text-white">
            Register New Application Cycle (Re-apply)
          </h3>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Creates a new application cycle with status <strong>Screening</strong> for{" "}
            <strong>{reapplyTarget?.name}</strong>. Interview recordings and the{" "}
            <code className="font-mono">REJECTED</code> decision for{" "}
            <code className="font-mono">{reapplyTarget?.candidate_code}</code> remain preserved for audit.
          </p>

          <div className="mt-4 space-y-3">
            <FormField label="Position Applied" required>
              <InputField
                value={reapplyPosition}
                onChange={(e) => setReapplyPosition(e.target.value)}
                placeholder="e.g., Senior Frontend Engineer"
              />
            </FormField>

            <FormField label="Re-application Context / Notes">
              <TextArea
                rows={2}
                value={reapplyNotes}
                onChange={(e) => setReapplyNotes(e.target.value)}
                placeholder="e.g. Re-applying after 6 months with updated portfolio."
              />
            </FormField>
          </div>

          <div className="mt-6 flex justify-end gap-2.5 pt-3 border-t border-gray-100 dark:border-gray-800">
            <Button
              variant="outline"
              size="sm"
              disabled={isSaving}
              onClick={() => setIsReapplyModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              disabled={isSaving}
              onClick={handleExecuteReapply}
              startIcon={<PlusIcon />}
            >
              Create Cycle #{(reapplyTarget?.application_cycle ?? 1) + 1}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Move to Offering Confirmation Modal */}
      <ConfirmationModal
        isOpen={Boolean(offerTarget)}
        onClose={() => setOfferTarget(null)}
        onConfirm={handleConfirmMoveToOffering}
        isLoading={isSaving}
        title="Advance Candidate to Offering"
        description={`Are you sure you want to advance "${offerTarget?.name}" (${offerTarget?.candidate_code}) to the Offering stage?`}
        confirmText="Yes, Move to Offering"
        cancelText="Cancel"
        variant="primary"
      />

      {/* Save Confirmation Modal (Add or Edit) */}
      <ConfirmationModal
        isOpen={isSaveConfirmOpen}
        onClose={() => setIsSaveConfirmOpen(false)}
        onConfirm={handleExecuteSaveCandidate}
        isLoading={isSaving}
        title={activeCandidate ? "Confirm Update Candidate" : "Confirm Add Candidate"}
        description={
          activeCandidate
            ? "Are you sure you want to update this candidate's profile information?"
            : "Are you sure you want to register this candidate into the Screening queue?"
        }
        confirmText={activeCandidate ? "Yes, Save Changes" : "Yes, Add Candidate"}
        cancelText="Cancel"
        variant="primary"
      />

      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        onConfirm={handleConfirmDelete}
        isLoading={isSaving}
        title="Confirm Delete Candidate"
        description={`Are you sure you want to delete candidate "${activeCandidate?.name}"? Candidates already linked to interview sessions or audit history will be protected against deletion.`}
        confirmText="Yes, Delete"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
}
