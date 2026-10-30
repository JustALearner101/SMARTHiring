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
import { PencilIcon, PlusIcon, TrashBinIcon } from "@/icons";
import { masterService } from "@/services";
import {
  CompetencyItem,
  RubricProfile,
  RubricTargetRole,
} from "@/types/master";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

export default function RubricsPage() {
  const { user, role } = useAuth();
  const { showSuccess, showError } = useToast();
  const [activeProfileId, setActiveProfileId] = useState<string>("");
  const [isMutating, setIsMutating] = useState(false);

  // Add Rubric Profile Modal
  const [isAddProfileOpen, setIsAddProfileOpen] = useState(false);
  const [newProfileCode, setNewProfileCode] = useState("");
  const [newProfileName, setNewProfileName] = useState("");
  const [newProfileDesc, setNewProfileDesc] = useState("");
  const [newProfileDept, setNewProfileDept] = useState("");
  const [newProfileTargetRole, setNewProfileTargetRole] =
    useState<RubricTargetRole>("HR");

  // Delete Rubric Profile Confirmation
  const [deleteTargetProfile, setDeleteTargetProfile] =
    useState<RubricProfile | null>(null);

  // Add / Edit Competency Modal
  const [isCompModalOpen, setIsCompModalOpen] = useState(false);
  const [editingComp, setEditingComp] = useState<CompetencyItem | null>(null);
  const [compCode, setCompCode] = useState("");
  const [compName, setCompName] = useState("");
  const [compDesc, setCompDesc] = useState("");
  const [compWeight, setCompWeight] = useState(25);
  const [compTarget, setCompTarget] = useState(4);

  // Delete Competency Confirmation
  const [deleteTargetComp, setDeleteTargetComp] =
    useState<CompetencyItem | null>(null);

  const queryClient = useQueryClient();
  const queryKey = useMemo(
    () => ["rubrics", user?.id || "anon", role || "anon"],
    [user?.id, role]
  );

  const { data: rubricsData, isLoading } = useQuery({
    queryKey,
    queryFn: async () => {
      const apiProfiles = await masterService.listRubrics();
      return (Array.isArray(apiProfiles) ? apiProfiles : []).map((profile) => ({
        ...profile,
        competencies: Array.isArray(profile.competencies)
          ? profile.competencies
          : [],
      }));
    },
  });

  const profiles = useMemo(() => rubricsData || [], [rubricsData]);
  const activeProfile =
    profiles.find((p) => p.id === activeProfileId) || profiles[0];

  const canMutateActiveProfile = useMemo(() => {
    if (!activeProfile || !role) return false;
    if (role === "ADMIN") return true;
    if (role === "INTERVIEWER") {
      return activeProfile.owner_user_id === user?.id;
    }
    if (role === "HR") {
      return (
        activeProfile.owner_user_id === user?.id ||
        activeProfile.target_role === "HR"
      );
    }
    return false;
  }, [activeProfile, role, user?.id]);

  // Open Add Profile Modal
  const handleOpenAddProfile = () => {
    setNewProfileCode(
      role === "INTERVIEWER" ? "PROFILE-DIV-R1" : "PROFILE-HR-R1"
    );
    setNewProfileName("");
    setNewProfileDesc("");
    setNewProfileDept(user?.department || "");
    setNewProfileTargetRole(role === "INTERVIEWER" ? "INTERVIEWER" : "HR");
    setIsAddProfileOpen(true);
  };

  // Execute Create Rubric Profile
  const handleCreateProfile = async () => {
    if (!newProfileCode.trim() || !newProfileName.trim()) {
      showError(
        "Validasi Gagal",
        "Harap lengkapi kode profil rubrik dan nama tahap wawancara."
      );
      return;
    }
    setIsMutating(true);
    try {
      const created = await masterService.createRubricProfile({
        code: newProfileCode.trim().toUpperCase(),
        round_name: newProfileName.trim(),
        description: newProfileDesc.trim() || undefined,
        department: newProfileDept.trim() || undefined,
        target_role:
          role === "ADMIN"
            ? newProfileTargetRole
            : role === "INTERVIEWER"
            ? "INTERVIEWER"
            : "HR",
      });
      queryClient.setQueryData(
        queryKey,
        (old: RubricProfile[] | undefined) => [created, ...(old || [])]
      );
      setActiveProfileId(created.id);
      void queryClient.invalidateQueries({ queryKey: ["rubrics"] });
      setIsAddProfileOpen(false);
      showSuccess(
        "Profil Rubrik Dibuat",
        `Profil rubrik "${created.round_name}" (${created.code}) berhasil disimpan ke database.`
      );
    } catch (error) {
      console.error("Failed to create rubric profile:", error);
      showError(
        "Gagal Membuat Profil Rubrik",
        error instanceof Error
          ? error.message
          : "Terjadi kesalahan saat menyimpan profil rubrik."
      );
    } finally {
      setIsMutating(false);
    }
  };

  // Execute Delete Rubric Profile
  const handleConfirmDeleteProfile = async () => {
    if (!deleteTargetProfile) return;
    const targetId = deleteTargetProfile.id;
    const targetName = deleteTargetProfile.round_name;
    setIsMutating(true);
    try {
      await masterService.deleteRubricProfile(targetId);
      queryClient.setQueryData(queryKey, (old: RubricProfile[] | undefined) =>
        (old || []).filter((p) => p.id !== targetId)
      );
      if (activeProfileId === targetId) {
        setActiveProfileId("");
      }
      void queryClient.invalidateQueries({ queryKey: ["rubrics"] });
      setDeleteTargetProfile(null);
      showSuccess(
        "Profil Rubrik Dihapus",
        `Profil rubrik "${targetName}" berhasil dihapus.`
      );
    } catch (error) {
      console.error("Failed to delete rubric profile:", error);
      showError(
        "Tidak Dapat Menghapus Profil",
        error instanceof Error
          ? error.message
          : "Profil rubrik sudah digunakan pada riwayat sesi wawancara."
      );
    } finally {
      setIsMutating(false);
    }
  };

  // Open Add Competency Modal
  const handleOpenAddCompetency = () => {
    setEditingComp(null);
    setCompCode("");
    setCompName("");
    setCompDesc("");
    setCompWeight(25);
    setCompTarget(4);
    setIsCompModalOpen(true);
  };

  // Open Edit Competency Modal
  const handleOpenEditCompetency = (comp: CompetencyItem) => {
    setEditingComp(comp);
    setCompCode(comp.code);
    setCompName(comp.name);
    setCompDesc(comp.description);
    setCompWeight(comp.weight);
    setCompTarget(comp.target_score);
    setIsCompModalOpen(true);
  };

  // Save Competency (Create or Update via Backend API)
  const handleSaveCompetency = async () => {
    if (!activeProfile) return;
    if (!compCode.trim() || !compName.trim() || !compDesc.trim()) {
      showError(
        "Validasi Gagal",
        "Harap lengkapi kode, nama kompetensi, dan pertanyaan/panduan penilaian."
      );
      return;
    }

    setIsMutating(true);
    try {
      if (editingComp) {
        const updated = await masterService.updateCompetency(
          activeProfile.id,
          editingComp.id,
          {
            code: compCode.trim().toUpperCase(),
            name: compName.trim(),
            description: compDesc.trim(),
            weight: compWeight,
            target_score: compTarget,
          }
        );
        queryClient.setQueryData(queryKey, (old: RubricProfile[] | undefined) =>
          (old || []).map((p) =>
            p.id === activeProfile.id
              ? {
                  ...p,
                  competencies: p.competencies.map((c) =>
                    c.id === editingComp.id
                      ? { ...updated, weight: compWeight, target_score: compTarget }
                      : c
                  ),
                }
              : p
          )
        );
        showSuccess(
          "Kompetensi Diperbarui",
          `Indikator kompetensi "${updated.name}" berhasil diperbarui.`
        );
      } else {
        const created = await masterService.createCompetency(activeProfile.id, {
          code: compCode.trim().toUpperCase(),
          name: compName.trim(),
          description: compDesc.trim(),
          weight: compWeight,
          target_score: compTarget,
        });
        queryClient.setQueryData(queryKey, (old: RubricProfile[] | undefined) =>
          (old || []).map((p) =>
            p.id === activeProfile.id
              ? {
                  ...p,
                  competencies: [
                    ...p.competencies,
                    { ...created, weight: compWeight, target_score: compTarget },
                  ],
                }
              : p
          )
        );
        showSuccess(
          "Kompetensi Ditambahkan",
          `Indikator kompetensi "${created.name}" berhasil disimpan ke database.`
        );
      }
      void queryClient.invalidateQueries({ queryKey: ["rubrics"] });
      setIsCompModalOpen(false);
      setEditingComp(null);
    } catch (error) {
      console.error("Failed to save competency:", error);
      showError(
        "Gagal Menyimpan Kompetensi",
        error instanceof Error
          ? error.message
          : "Terjadi kesalahan saat menyimpan indikator kompetensi."
      );
    } finally {
      setIsMutating(false);
    }
  };

  // Delete Competency upon confirmation
  const handleConfirmDeleteCompetency = async () => {
    if (!activeProfile || !deleteTargetComp) return;
    const compName = deleteTargetComp.name;
    const targetCompId = deleteTargetComp.id;
    setIsMutating(true);
    try {
      await masterService.deleteCompetency(activeProfile.id, targetCompId);
      queryClient.setQueryData(queryKey, (old: RubricProfile[] | undefined) =>
        (old || []).map((p) =>
          p.id === activeProfile.id
            ? {
                ...p,
                competencies: p.competencies.filter(
                  (c) => c.id !== targetCompId
                ),
              }
            : p
        )
      );
      void queryClient.invalidateQueries({ queryKey: ["rubrics"] });
      setDeleteTargetComp(null);
      showSuccess(
        "Kompetensi Dihapus",
        `Indikator kompetensi "${compName}" berhasil dihapus dari profil rubrik.`
      );
    } catch (error) {
      console.error("Failed to delete competency:", error);
      showError(
        "Tidak Dapat Menghapus Kompetensi",
        error instanceof Error
          ? error.message
          : "Indikator kompetensi sudah tertaut pada sesi wawancara historis."
      );
    } finally {
      setIsMutating(false);
    }
  };

  const totalWeight =
    activeProfile?.competencies.reduce((sum, c) => sum + c.weight, 0) || 0;

  return (
    <div>
      <PageBreadcrumb pageTitle="Rubrics & Competencies" />

      {/* Main Container */}
      <div className="rounded-2xl border border-gray-200 bg-white p-5 xl:p-6 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-gray-100 pb-5 dark:border-gray-800">
          <div>
            <h3 className="text-theme-xl font-semibold text-gray-800 dark:text-white/90">
              Evaluation Rubrics &amp; Competencies
            </h3>
            <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
              {role === "INTERVIEWER"
                ? `Daftar profil rubrik dan pertanyaan penilaian khusus bidang Anda (${user?.department || "Technical / Division"}).`
                : role === "HR"
                ? "Kelola rubrik pertanyaan wawancara HR yang digunakan AI Copilot untuk mengekstrak bukti kutipan."
                : "Tampilan penuh Administrator atas seluruh profil rubrik penilaian HR maupun setiap divisi Pewawancara."}
            </p>
          </div>
          <Button
            variant="primary"
            size="sm"
            startIcon={<PlusIcon />}
            onClick={handleOpenAddProfile}
          >
            New Rubric Profile
          </Button>
        </div>

        {/* Profile Tabs */}
        {profiles.length > 0 && (
          <div className="mt-5 flex flex-wrap gap-2 border-b border-gray-100 pb-3 dark:border-gray-800">
            {profiles.map((prof) => {
              const isActive = prof.id === activeProfile?.id;
              return (
                <button
                  key={prof.id}
                  type="button"
                  onClick={() => setActiveProfileId(prof.id)}
                  className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-semibold transition-all ${
                    isActive
                      ? "bg-brand-500 text-white shadow-theme-xs"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
                  }`}
                >
                  <span>{prof.round_name}</span>
                  <span
                    className={`rounded-md px-1.5 py-0.5 text-[10px] font-mono ${
                      isActive
                        ? "bg-white/20 text-white"
                        : "bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300"
                    }`}
                  >
                    {prof.code}
                  </span>
                </button>
              );
            })}
          </div>
        )}

        {/* Empty State if Interviewer has not created a rubric yet */}
        {!isLoading && profiles.length === 0 && (
          <div className="mt-6 rounded-xl border border-dashed border-gray-300 bg-gray-50/60 p-8 text-center dark:border-gray-700 dark:bg-gray-800/30">
            <h4 className="text-sm font-semibold text-gray-800 dark:text-white">
              Belum Ada Profil Rubrik Penilaian
            </h4>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Buat profil rubrik pertanyaan sesuai posisi/divisi Anda agar AI Interview Copilot mengevaluasi kandidat menggunakan indikator Anda sendiri.
            </p>
            <div className="mt-4">
              <Button
                variant="primary"
                size="sm"
                startIcon={<PlusIcon />}
                onClick={handleOpenAddProfile}
              >
                Buat Profil Rubrik Pertama Anda
              </Button>
            </div>
          </div>
        )}

        {/* Profile Info Banner */}
        {activeProfile && (
          <div className="mt-4 rounded-xl border border-gray-100 bg-gray-50/70 p-4 dark:border-gray-800 dark:bg-gray-800/40">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-mono font-medium text-brand-600 dark:text-brand-400">
                    {activeProfile.code}
                  </span>
                  <Badge
                    color={
                      activeProfile.target_role === "INTERVIEWER"
                        ? "info"
                        : "success"
                    }
                    size="sm"
                  >
                    {activeProfile.target_role === "INTERVIEWER"
                      ? "Interviewer Rubric"
                      : "HR Rubric"}
                  </Badge>
                  {activeProfile.department && (
                    <Badge color="light" size="sm">
                      {activeProfile.department}
                    </Badge>
                  )}
                  {activeProfile.owner_name && (
                    <span className="text-[11px] text-gray-500 dark:text-gray-400">
                      Owner: <strong>{activeProfile.owner_name}</strong>
                    </span>
                  )}
                </div>
                <h4 className="text-sm font-semibold text-gray-900 dark:text-white mt-1">
                  {activeProfile.round_name}
                </h4>
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  {activeProfile.description}
                </p>
              </div>
              <div className="flex items-center gap-4 self-end sm:self-center">
                <div className="text-end">
                  <span className="text-[11px] text-gray-400">Total Weight</span>
                  <div
                    className={`text-base font-bold ${
                      totalWeight === 100
                        ? "text-success-600 dark:text-success-400"
                        : "text-warning-500"
                    }`}
                  >
                    {totalWeight}%
                  </div>
                </div>
                {canMutateActiveProfile && (
                  <button
                    type="button"
                    onClick={() => setDeleteTargetProfile(activeProfile)}
                    className="h-8 w-8 inline-flex items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-500 shadow-theme-xs hover:border-error-300 hover:bg-error-50 hover:text-error-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:hover:border-error-500/30 dark:hover:bg-error-500/15 dark:hover:text-error-400 transition-all"
                    title="Hapus Profil Rubrik Ini"
                  >
                    <TrashBinIcon />
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Competencies Table Header & Button */}
        {activeProfile && (
          <>
            <div className="mt-5 flex items-center justify-between">
              <h4 className="text-sm font-semibold text-gray-800 dark:text-white/90">
                List of Competency Indicators (
                {activeProfile.competencies.length})
              </h4>
              <Button
                variant="outline"
                size="sm"
                startIcon={<PlusIcon />}
                onClick={handleOpenAddCompetency}
                disabled={!canMutateActiveProfile}
                title={
                  !canMutateActiveProfile
                    ? "Anda hanya dapat mengubah indikator pada profil rubrik milik Anda sendiri."
                    : undefined
                }
              >
                Add Competency Indicator
              </Button>
            </div>

            {/* Competencies Table */}
            <div className="mt-3 overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-800">
              <Table>
                <TableHeader className="bg-gray-50 dark:bg-gray-800/60 border-b border-gray-200 dark:border-gray-800">
                  <TableRow>
                    <TableCell
                      isHeader
                      className="ps-4 pe-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300"
                    >
                      Code
                    </TableCell>
                    <TableCell
                      isHeader
                      className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300"
                    >
                      Competency Name &amp; Reference Question
                    </TableCell>
                    <TableCell
                      isHeader
                      className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300"
                    >
                      Weight (%)
                    </TableCell>
                    <TableCell
                      isHeader
                      className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300"
                    >
                      Target Score
                    </TableCell>
                    <TableCell
                      isHeader
                      className="pe-5 ps-3 py-3 text-end text-xs font-semibold text-gray-600 dark:text-gray-300"
                    >
                      Actions
                    </TableCell>
                  </TableRow>
                </TableHeader>
                <TableBody className="divide-y divide-gray-100 dark:divide-gray-800">
                  {isLoading ? (
                    <TableRow>
                      <TableCell
                        colSpan={5}
                        className="py-8 text-center text-xs text-gray-400"
                      >
                        Loading rubrics from database...
                      </TableCell>
                    </TableRow>
                  ) : activeProfile.competencies.length === 0 ? (
                    <TableRow>
                      <TableCell
                        colSpan={5}
                        className="py-8 text-center text-xs text-gray-400"
                      >
                        Belum ada indikator pertanyaan pada profil rubrik ini. Klik &quot;Add Competency Indicator&quot; untuk menambahkan.
                      </TableCell>
                    </TableRow>
                  ) : (
                    activeProfile.competencies.map((comp) => (
                      <TableRow
                        key={comp.id}
                        className="hover:bg-gray-50/70 dark:hover:bg-white/[0.02] transition-colors"
                      >
                        <TableCell className="ps-4 pe-3 py-3.5">
                          <span className="font-mono text-xs font-semibold text-brand-600 dark:text-brand-400">
                            {comp.code}
                          </span>
                        </TableCell>
                        <TableCell className="px-3 py-3.5">
                          <div className="flex flex-col">
                            <span className="text-xs font-semibold text-gray-800 dark:text-white/90">
                              {comp.name}
                            </span>
                            <span className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">
                              {comp.description}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell className="px-3 py-3.5">
                          <span className="inline-flex items-center rounded-md bg-gray-100 px-2 py-0.5 text-xs font-mono font-medium text-gray-700 dark:bg-gray-800 dark:text-gray-300">
                            {comp.weight}%
                          </span>
                        </TableCell>
                        <TableCell className="px-3 py-3.5">
                          <Badge color="primary" size="sm">
                            {comp.target_score} / 5.0
                          </Badge>
                        </TableCell>
                        <TableCell className="pe-5 ps-3 py-3.5 text-end whitespace-nowrap">
                          {canMutateActiveProfile ? (
                            <div className="flex items-center justify-end gap-1.5">
                              <button
                                type="button"
                                onClick={() => handleOpenEditCompetency(comp)}
                                className="h-8 w-8 inline-flex items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-600 shadow-theme-xs hover:border-brand-300 hover:bg-gray-50 hover:text-brand-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:border-brand-500/30 dark:hover:bg-gray-700/60 dark:hover:text-brand-400 transition-all"
                                title="Edit Competency Indicator"
                              >
                                <PencilIcon />
                              </button>
                              <button
                                type="button"
                                onClick={() => setDeleteTargetComp(comp)}
                                className="h-8 w-8 inline-flex items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-500 shadow-theme-xs hover:border-error-300 hover:bg-error-50 hover:text-error-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:hover:border-error-500/30 dark:hover:bg-error-500/15 dark:hover:text-error-400 transition-all"
                                title="Delete Competency Indicator"
                              >
                                <TrashBinIcon />
                              </button>
                            </div>
                          ) : (
                            <span className="text-xs text-gray-400 italic">
                              Read-only
                            </span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>

            {/* Footer Summary */}
            <div className="mt-4 flex items-center justify-between text-xs text-gray-400">
              <span>
                {activeProfile.competencies.length} active competencies for this
                round
              </span>
              <span className="font-mono">
                Scoped Rubric Ownership: tblm_profile &amp; tblm_competency
              </span>
            </div>
          </>
        )}
      </div>

      {/* Create New Rubric Profile Modal */}
      <Modal
        isOpen={isAddProfileOpen}
        onClose={() => setIsAddProfileOpen(false)}
        className="max-w-2xl m-4"
      >
        <div className="p-8 sm:p-10">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Create New Rubric Profile
          </h3>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Buat paket rubrik pertanyaan baru sesuai posisi/tahap wawancara yang Anda tangani.
          </p>

          <div className="mt-5 space-y-3.5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <FormField label="Profile Code" required>
                <InputField
                  placeholder="e.g., PROFILE-BACKEND-R1"
                  value={newProfileCode}
                  onChange={(e) => setNewProfileCode(e.target.value)}
                />
              </FormField>

              <FormField label="Department / Division" required>
                <InputField
                  placeholder="e.g., Engineering, Finance, HR"
                  value={newProfileDept}
                  onChange={(e) => setNewProfileDept(e.target.value)}
                />
              </FormField>
            </div>

            <FormField label="Interview Round Name" required>
              <InputField
                placeholder="e.g., Backend Engineering Technical Round"
                value={newProfileName}
                onChange={(e) => setNewProfileName(e.target.value)}
              />
            </FormField>

            {role === "ADMIN" && (
              <FormField label="Target Evaluator Role" required>
                <Select
                  options={[
                    { value: "HR", label: "HR (Culture & Screening)" },
                    {
                      value: "INTERVIEWER",
                      label: "Interviewer (Technical / Division User)",
                    },
                  ]}
                  value={newProfileTargetRole}
                  onChange={(e) =>
                    setNewProfileTargetRole(e.target.value as RubricTargetRole)
                  }
                />
              </FormField>
            )}

            <FormField label="Rubric Description">
              <TextArea
                rows={2}
                placeholder="Ringkasan tujuan evaluasi tahap wawancara ini..."
                value={newProfileDesc}
                onChange={(e) => setNewProfileDesc(e.target.value)}
              />
            </FormField>
          </div>

          <div className="mt-6 flex justify-end gap-2.5 pt-3 border-t border-gray-100 dark:border-gray-800">
            <Button
              variant="outline"
              onClick={() => setIsAddProfileOpen(false)}
              disabled={isMutating}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleCreateProfile}
              disabled={isMutating}
            >
              {isMutating ? "Saving..." : "Create Profile"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Add / Edit Competency Modal */}
      <Modal
        isOpen={isCompModalOpen}
        onClose={() => setIsCompModalOpen(false)}
        className="max-w-4xl m-4"
      >
        <div className="p-8 sm:p-10">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {editingComp
              ? "Edit Competency Indicator"
              : "Add New Competency Indicator"}
          </h3>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {editingComp
              ? `Perbarui kriteria pertanyaan kompetensi pada profil ${activeProfile?.round_name}.`
              : `Tambahkan indikator pertanyaan baru pada profil ${activeProfile?.round_name}.`}
          </p>

          <div className="mt-5 space-y-3.5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <FormField label="Competency Code" required>
                <InputField
                  placeholder="cth: SYS-ARCH"
                  value={compCode}
                  onChange={(e) => setCompCode(e.target.value)}
                />
              </FormField>

              <FormField label="Competency Name" required>
                <InputField
                  placeholder="cth: System Architecture & Scalability"
                  value={compName}
                  onChange={(e) => setCompName(e.target.value)}
                />
              </FormField>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <FormField label="Weight (%)" required>
                <InputField
                  type="number"
                  min={5}
                  max={100}
                  step={5}
                  value={compWeight}
                  onChange={(e) =>
                    setCompWeight(parseInt(e.target.value) || 25)
                  }
                />
              </FormField>

              <FormField label="Target Skor Minimal (1 - 5)" required>
                <InputField
                  type="number"
                  min={1}
                  max={5}
                  value={compTarget}
                  onChange={(e) => setCompTarget(parseInt(e.target.value) || 4)}
                />
              </FormField>
            </div>

            <FormField
              label="Reference Question & Evidence Guidelines for AI"
              required
              hint="AI Interview Copilot akan menelusuri bukti jawaban kandidat di transkrip berdasarkan pertanyaan & kriteria ini."
            >
              <TextArea
                rows={3}
                placeholder="Tuliskan pertanyaan acuan wawancara dan indikator bukti yang dicari dari jawaban kandidat..."
                value={compDesc}
                onChange={(e) => setCompDesc(e.target.value)}
              />
            </FormField>
          </div>

          <div className="mt-6 flex justify-end gap-2.5 pt-3 border-t border-gray-100 dark:border-gray-800">
            <Button
              variant="outline"
              onClick={() => setIsCompModalOpen(false)}
              disabled={isMutating}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleSaveCompetency}
              disabled={isMutating}
            >
              {isMutating
                ? "Saving..."
                : editingComp
                ? "Update Indicator"
                : "Save Indicator"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Profile Confirmation Modal */}
      <ConfirmationModal
        isOpen={!!deleteTargetProfile}
        onClose={() => setDeleteTargetProfile(null)}
        onConfirm={handleConfirmDeleteProfile}
        isLoading={isMutating}
        title="Confirm Delete Rubric Profile"
        description={`Hapus profil rubrik "${deleteTargetProfile?.round_name}" (${deleteTargetProfile?.code}) beserta seluruh indikator kompetensinya?`}
        confirmText="Yes, Delete Profile"
        cancelText="Cancel"
        variant="danger"
      />

      {/* Delete Competency Confirmation Modal */}
      <ConfirmationModal
        isOpen={!!deleteTargetComp}
        onClose={() => setDeleteTargetComp(null)}
        onConfirm={handleConfirmDeleteCompetency}
        isLoading={isMutating}
        title="Confirm Delete Competency"
        description={`Apakah Anda yakin ingin menghapus indikator kompetensi "${deleteTargetComp?.name}" (${deleteTargetComp?.code}) dari ${activeProfile?.round_name}?`}
        confirmText="Yes, Delete"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
}
