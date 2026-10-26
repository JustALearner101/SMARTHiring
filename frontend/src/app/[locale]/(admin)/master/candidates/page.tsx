"use client";

import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import FormField from "@/components/form/FormField";
import InputField from "@/components/form/input/InputField";
import TextArea from "@/components/form/input/TextArea";
import Select from "@/components/form/Select";
import Badge from "@/components/ui/badge/Badge";
import Button from "@/components/ui/button/Button";
import { Modal, ConfirmationModal } from "@/components/ui/modal";
import {
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Link } from "@/i18n/navigation";
import {
  BoltIcon,
  PencilIcon,
  PlusIcon,
  TrashBinIcon,
} from "@/icons";
import { masterService } from "@/services";
import { ApplicationStatus, Candidate, PreferredChannel, Timezone } from "@/types/master";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

export default function CandidatesPage() {
  const { role } = useAuth();
  const { showSuccess, showError } = useToast();
  const [isSaving, setIsSaving] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [timezoneFilter, setTimezoneFilter] = useState<string>("ALL");

  // Modals
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [isSaveConfirmOpen, setIsSaveConfirmOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [activeCandidate, setActiveCandidate] = useState<Candidate | null>(null);

  // Form State
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    preferred_channel: "whatsapp" as PreferredChannel,
    applied_position: "",
    status: "SCREENING" as ApplicationStatus,
    timezone: "WIB" as Timezone,
    resume_url: "",
    notes: "",
    current_salary: "" as string | number,
    expected_salary: "" as string | number,
  });

  // TanStack Query: Caches candidates in memory with 1-min freshness and 0ms navigation
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

  // Open Add Modal
  const handleOpenAdd = () => {
    setActiveCandidate(null);
    setFormData({
      name: "",
      email: "",
      phone: "+628",
      preferred_channel: "whatsapp",
      applied_position: "",
      status: "SCREENING",
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
      status: cand.status,
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
        "Validasi Form Gagal",
        "Harap lengkapi nama kandidat, email, dan posisi yang dilamar sebelum menyimpan."
      );
      return;
    }
    // Open confirmation dialog — form modal remains open in the background so user can go back if needed
    setIsSaveConfirmOpen(true);
  };

  // Step 2: Execute Save Candidate upon user confirmation in Modal
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
          status: formData.status,
          timezone: formData.timezone,
          resume_url: formData.resume_url,
          notes: formData.notes,
          current_salary: currentSalaryNum,
          expected_salary: expectedSalaryNum,
        });
        queryClient.setQueryData(
          ["candidates"],
          (old: { items: Candidate[]; total: number; page: number; page_size: number; total_pages: number } | undefined) => ({
            items: (old?.items || []).map((c) => (c.id === editing.id ? updated : c)),
            total: old?.total || 0,
            page: old?.page || 1,
            page_size: old?.page_size || 100,
            total_pages: old?.total_pages || 1,
          })
        );
        showSuccess(
          "Kandidat Diperbarui",
          `Data kandidat ${formData.name} berhasil disimpan ke database.`
        );
      } else {
        const created = await masterService.createCandidate({
          name: formData.name,
          email: formData.email,
          phone: formData.phone,
          preferred_channel: formData.preferred_channel,
          applied_position: formData.applied_position,
          status: formData.status,
          timezone: formData.timezone,
          resume_url: formData.resume_url,
          notes: formData.notes,
          current_salary: currentSalaryNum,
          expected_salary: expectedSalaryNum,
        });
        queryClient.setQueryData(
          ["candidates"],
          (old: { items: Candidate[]; total: number; page: number; page_size: number; total_pages: number } | undefined) => ({
            items: [created, ...(old?.items || [])],
            total: (old?.total || 0) + 1,
            page: old?.page || 1,
            page_size: old?.page_size || 100,
            total_pages: old?.total_pages || 1,
          })
        );
        showSuccess(
          "Kandidat Ditambahkan",
          `Kandidat ${formData.name} (${created.candidate_code}) berhasil ditambahkan ke antrean.`
        );
      }
      void queryClient.invalidateQueries({ queryKey: ["candidates"] });
      setIsSaveConfirmOpen(false);
      setIsFormModalOpen(false);
    } catch (error) {
      console.error("Failed to save candidate:", error);
      const msg =
        error instanceof Error ? error.message : "Terjadi kesalahan saat menyimpan data kandidat ke server.";
      showError("Gagal Menyimpan Data", msg);
    } finally {
      setIsSaving(false);
    }
  };

  // Confirm Delete
  const handleConfirmDelete = () => {
    if (!activeCandidate) return;
    const targetName = activeCandidate.name;
    queryClient.setQueryData(
      ["candidates"],
      (old: { items: Candidate[]; total: number; page: number; page_size: number; total_pages: number } | undefined) => ({
        items: (old?.items || []).filter((c) => c.id !== activeCandidate.id),
        total: Math.max(0, (old?.total || 1) - 1),
        page: old?.page || 1,
        page_size: old?.page_size || 100,
        total_pages: old?.total_pages || 1,
      })
    );
    void queryClient.invalidateQueries({ queryKey: ["candidates"] });
    setIsDeleteModalOpen(false);
    showSuccess("Kandidat Dihapus", `Data kandidat ${targetName} telah dihapus dari antrean.`);
  };

  // Render Status Badge
  const renderStatusBadge = (status: ApplicationStatus) => {
    switch (status) {
      case "ESCALATED":
        return <Badge color="warning" size="sm">Escalated</Badge>;
      case "INTERVIEW_SCHEDULED":
        return <Badge color="primary" size="sm">Scheduled</Badge>;
      case "COMPLETED":
        return <Badge color="info" size="sm">Completed</Badge>;
      case "OFFERED":
        return <Badge color="success" size="sm">Offered</Badge>;
      case "REJECTED":
        return <Badge color="error" size="sm">Rejected</Badge>;
      default:
        return <Badge color="light" size="sm">Screening</Badge>;
    }
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
              List of candidates who have been through ATS selection and are ready to be escalated to the interview stage by the AI Orchestrator.
            </p>
          </div>
          <Button
            variant="primary"
            size="sm"
            startIcon={<PlusIcon/>}
            onClick={handleOpenAdd}
            disabled={role !== "HR"}
            title={role !== "HR" ? "Hanya HR Admin yang berwenang menambah kandidat" : "Tambah kandidat baru"}
          >
            Add Candidate
          </Button>
        </div>

        {/* Filter Controls Bar */}
        <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-12">
          {/* Search Box */}
          <div className="sm:col-span-6">
            <InputField
              placeholder="Search name"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Status Filter */}
          <div className="sm:col-span-3">
            <Select
              options={[
                { value: "ALL", label: "All Status" },
                { value: "SCREENING", label: "Screening" },
                { value: "ESCALATED", label: "Escalated" },
                { value: "INTERVIEW_SCHEDULED", label: "Scheduled" },
                { value: "COMPLETED", label: "Completed" },
                { value: "OFFERED", label: "Offered" },
                { value: "REJECTED", label: "Rejected" },
              ]}
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            />
          </div>

          {/* Timezone Filter */}
          <div className="sm:col-span-3">
            <Select
              options={[
                { value: "ALL", label: "All Timezone" },
                { value: "WIB", label: "WIB (UTC+7)" },
                { value: "WITA", label: "WITA (UTC+8)" },
                { value: "WIT", label: "WIT (UTC+9)" },
              ]}
              value={timezoneFilter}
              onChange={(e) => setTimezoneFilter(e.target.value)}
            />
          </div>
        </div>

        {/* Candidates Table */}
        <div className="mt-5 overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-800">
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
                  Action
                </TableCell>
              </TableRow>
            </TableHeader>
            <TableBody className="divide-y divide-gray-100 dark:divide-gray-800">
              {isLoading ? (
                <TableRow>
                  <TableCell className="py-8 text-center text-xs text-gray-400">
                    Loading candidates from database...
                  </TableCell>
                </TableRow>
              ) : filteredCandidates.length === 0 ? (
                <TableRow>
                  <TableCell className="py-8 text-center text-xs text-gray-400">
                    No candidate data matches the search criteria.
                  </TableCell>
                </TableRow>
              ) : (
                filteredCandidates.map((cand) => (
                  <TableRow key={cand.id} className="hover:bg-gray-50/70 dark:hover:bg-white/[0.02] transition-colors">
                    {/* Candidate Info */}
                    <TableCell className="ps-4 pe-3 py-3.5">
                      <div className="flex flex-col">
                        <span className="font-semibold text-sm text-gray-900 dark:text-white/90">
                          {cand.name}
                        </span>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-[11px] font-mono font-medium text-brand-600 dark:text-brand-400">
                            {cand.candidate_code}
                          </span>
                          <span className="text-gray-300 dark:text-gray-700">•</span>
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

                    {/* Salary (Role Guarded: Visible only to HR) */}
                    <TableCell className="px-3 py-3.5">
                      {role === "HR" ? (
                        cand.current_salary != null || cand.expected_salary != null ? (
                          <div className="flex flex-col text-xs font-mono">
                            <span className="font-semibold text-gray-800 dark:text-gray-200">
                              Exp: {cand.expected_salary ? `Rp ${(cand.expected_salary / 1000000).toLocaleString("id-ID")}M` : "-"}
                            </span>
                            <span className="text-[11px] text-gray-500 dark:text-gray-400">
                              Cur: {cand.current_salary ? `Rp ${(cand.current_salary / 1000000).toLocaleString("id-ID")}M` : "-"}
                            </span>
                          </div>
                        ) : (
                          <span className="text-xs text-gray-400">-</span>
                        )
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-500 dark:bg-gray-800 dark:text-gray-400">
                          🔒 Confidential (HR)
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
                        {/* Escalate button */}
                        <Link
                          href={`/orchestration/scheduling?candidateId=${cand.id}`}
                          className="inline-flex items-center gap-1.5 rounded-lg bg-brand-500 px-3 py-0.5 text-xs font-semibold text-white shadow-theme-xs hover:bg-brand-600 active:bg-brand-700 transition-all duration-150"
                          title="Eskalasi ke User Interview"
                        >
                          <BoltIcon className="text-white" />
                          <span>Escalate</span>
                        </Link>

                        {/* Edit & Delete: HR only */}
                        {role === "HR" && (
                          <>
                            <button
                              type="button"
                              onClick={() => handleOpenEdit(cand)}
                              className="h-8 w-8 inline-flex items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-600 shadow-theme-xs hover:border-brand-300 hover:bg-gray-50 hover:text-brand-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:border-brand-500/30 dark:hover:bg-gray-700/60 dark:hover:text-brand-400 transition-all"
                              title="Edit Kandidat"
                            >
                              <PencilIcon/>
                            </button>

                            <button
                              type="button"
                              onClick={() => {
                                setActiveCandidate(cand);
                                setIsDeleteModalOpen(true);
                              }}
                              className="h-8 w-8 inline-flex items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-500 shadow-theme-xs hover:border-error-300 hover:bg-error-50 hover:text-error-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:hover:border-error-500/30 dark:hover:bg-error-500/15 dark:hover:text-error-400 transition-all"
                              title="Hapus Kandidat"
                            >
                              <TrashBinIcon/>
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

        {/* Footer Summary */}
        <div className="mt-4 flex items-center justify-between text-xs text-gray-400">
          <span>Menampilkan {filteredCandidates.length} dari {candidates.length} total kandidat</span>
          <span className="font-mono">API Contract: tblm_candidate</span>
        </div>
      </div>

      {/* Unified Candidate Form Modal (Add / Edit) */}
      <Modal isOpen={isFormModalOpen} onClose={() => setIsFormModalOpen(false)} className="max-w-4xl m-4">
        <div className="p-10">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {activeCandidate
              ? `Edit Candidate (${activeCandidate.candidate_code})`
              : "Add New Candidate"}
          </h3>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {activeCandidate
              ? "Update candidate profile and contact channel preferences."
              : "Register candidate data that has passed the initial ATS screening stage."}
          </p>

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

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <FormField label="Preferred Channel" required>
                <Select
                  options={[
                    { value: "whatsapp", label: "WhatsApp" },
                    { value: "email", label: "Email" },
                  ]}
                  value={formData.preferred_channel}
                  onChange={(e) => setFormData({ ...formData, preferred_channel: e.target.value as PreferredChannel })}
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

              <FormField label="Application Status" required>
                <Select
                  options={[
                    { value: "SCREENING", label: "Screening" },
                    { value: "ESCALATED", label: "Escalated" },
                    { value: "INTERVIEW_SCHEDULED", label: "Scheduled" },
                    { value: "COMPLETED", label: "Completed" },
                    { value: "OFFERED", label: "Offered" },
                    { value: "REJECTED", label: "Rejected" },
                  ]}
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value as ApplicationStatus })}
                />
              </FormField>
            </div>

            {/* Salary Data (HR Only) */}
            {role === "HR" && (
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
                placeholder="e.g. Passed initial technical tests. Has a preference for daytime interviews."
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
              {activeCandidate ? "Update" : "Save"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Save Confirmation Modal (Add or Edit) */}
      <ConfirmationModal
        isOpen={isSaveConfirmOpen}
        onClose={() => setIsSaveConfirmOpen(false)}
        onConfirm={handleExecuteSaveCandidate}
        isLoading={isSaving}
        title={activeCandidate ? "Confirm Update Candidate" : "Confirm Add Candidate"}
        description={
          activeCandidate
            ? "Are you sure you want to update this candidate's information? Please make sure the changes are correct."
            : "Are you sure you want to register this candidate? Please ensure the entered information is accurate."
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
        title="Confirm Delete Candidate"
        description={`Are you sure you want to delete candidate "${activeCandidate?.name}"? This action cannot be undone.`}
        confirmText="Yes, Delete"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
}
