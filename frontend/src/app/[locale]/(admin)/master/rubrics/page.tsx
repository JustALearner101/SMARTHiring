"use client";

import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import FormField from "@/components/form/FormField";
import InputField from "@/components/form/input/InputField";
import TextArea from "@/components/form/input/TextArea";
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
import {
  BoltIcon,
  CheckCircleIcon,
  PencilIcon,
  PlusIcon,
  TimeIcon,
  TrashBinIcon,
  UserIcon,
} from "@/icons";
import { masterService } from "@/services";
import {
  Candidate,
  CompetencyItem,
  RubricProfile,
} from "@/types/master";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

export default function RubricsPage() {
  const { user, role } = useAuth();
  const { showSuccess, showError } = useToast();
  const [selectedCandidateId, setSelectedCandidateId] = useState<string>("");
  const [isMutating, setIsMutating] = useState(false);
  const [isReEvaluating, setIsReEvaluating] = useState(false);

  // Add Competency Modal
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

  // Create Profile for Candidate Modal
  const [isCreateProfileOpen, setIsCreateProfileOpen] = useState(false);
  const [customRoundTitle, setCustomRoundTitle] = useState("");

  const queryClient = useQueryClient();

  // 1. Fetch Candidates List
  const { data: candidatesData, isLoading: isCandidatesLoading } = useQuery({
    queryKey: ["candidates", "for-rubrics"],
    queryFn: async () => {
      const res = await masterService.listCandidates({ page_size: 100 });
      return Array.isArray(res?.items) ? res.items : [];
    },
  });

  const candidates = useMemo(() => candidatesData || [], [candidatesData]);

  // Derived Active Candidate
  const activeCandidate = useMemo<Candidate | null>(() => {
    if (candidates.length === 0) return null;
    return (
      candidates.find((c) => c.id === selectedCandidateId) || candidates[0]
    );
  }, [candidates, selectedCandidateId]);

  // 2. Fetch Scoped Rubric Profiles
  const { data: rubricsData, isLoading: isRubricsLoading } = useQuery({
    queryKey: ["rubrics", user?.id || "anon", role || "anon"],
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

  // Find Rubric Profile for currently active candidate
  const activeProfile = useMemo(() => {
    if (!activeCandidate) return null;
    return (
      profiles.find(
        (p) =>
          p.candidate_id === activeCandidate.id ||
          p.code.toUpperCase().includes(activeCandidate.candidate_code.toUpperCase())
      ) || null
    );
  }, [profiles, activeCandidate]);

  const canMutateActiveProfile = useMemo(() => {
    if (!activeProfile || !role) return true;
    if (role === "ADMIN") return true;
    if (role === "INTERVIEWER") {
      return activeProfile.owner_user_id === user?.id || !activeProfile.owner_user_id;
    }
    if (role === "HR") {
      return (
        activeProfile.owner_user_id === user?.id ||
        activeProfile.target_role === "HR" ||
        Boolean(activeProfile.candidate_id)
      );
    }
    return true;
  }, [activeProfile, role, user?.id]);

  // Re-Evaluate from Transcript
  const handleReEvaluate = async () => {
    if (!activeProfile) return;
    setIsReEvaluating(true);
    try {
      const updated = await masterService.reEvaluateRubric(activeProfile.id);
      queryClient.setQueryData(
        ["rubrics", user?.id || "anon", role || "anon"],
        (old: RubricProfile[] | undefined) =>
          (old || []).map((p) => (p.id === updated.id ? updated : p))
      );
      void queryClient.invalidateQueries({ queryKey: ["rubrics"] });
      showSuccess(
        "Evaluasi Ulang Berhasil",
        `AI berhasil mengevaluasi ulang transkrip wawancara ${activeCandidate?.name} untuk ${updated.competencies.length} indikator kompetensi.`
      );
    } catch (error) {
      console.error("Failed to re-evaluate rubric:", error);
      showError(
        "Gagal Menilai Ulang",
        error instanceof Error
          ? error.message
          : "Sesi wawancara kandidat belum memiliki rekaman atau transkrip audio."
      );
    } finally {
      setIsReEvaluating(false);
    }
  };

  // Open Create Profile for Candidate
  const handleOpenCreateProfile = () => {
    if (!activeCandidate) return;
    setCustomRoundTitle(`Interview Evaluation - ${activeCandidate.name}`);
    setIsCreateProfileOpen(true);
  };

  const handleConfirmCreateProfile = async () => {
    if (!activeCandidate) return;
    setIsMutating(true);
    try {
      await masterService.createRubricProfile({
        candidate_id: activeCandidate.id,
        round_name: customRoundTitle.trim() || `Interview Assessment - ${activeCandidate.name}`,
        target_role: role === "INTERVIEWER" ? "INTERVIEWER" : "HR",
        department: activeCandidate.applied_position || user?.department || "General",
      });
      void queryClient.invalidateQueries({ queryKey: ["rubrics"] });
      setIsCreateProfileOpen(false);
      showSuccess(
        "Rubrik Kandidat Dibuat",
        `Profil rubrik penilaian untuk kandidat "${activeCandidate.name}" berhasil disiapkan.`
      );
    } catch (error) {
      console.error("Failed to create candidate profile:", error);
      showError(
        "Gagal Menyiapkan Rubrik",
        error instanceof Error ? error.message : "Terjadi kesalahan saat menyiapkan rubrik kandidat."
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

  // Save Competency
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
        showSuccess(
          "Indikator Diperbarui",
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
        showSuccess(
          "Indikator Ditambahkan",
          `Indikator kompetensi "${created.name}" berhasil ditambahkan ke rubrik kandidat.`
        );
      }
      void queryClient.invalidateQueries({ queryKey: ["rubrics"] });
      setIsCompModalOpen(false);
      setEditingComp(null);
    } catch (error) {
      console.error("Failed to save competency:", error);
      showError(
        "Gagal Menyimpan Indikator",
        error instanceof Error
          ? error.message
          : "Terjadi kesalahan saat menyimpan indikator kompetensi."
      );
    } finally {
      setIsMutating(false);
    }
  };

  // Confirm Delete Competency
  const handleConfirmDeleteCompetency = async () => {
    if (!activeProfile || !deleteTargetComp) return;
    const compName = deleteTargetComp.name;
    const targetCompId = deleteTargetComp.id;
    setIsMutating(true);
    try {
      await masterService.deleteCompetency(activeProfile.id, targetCompId);
      void queryClient.invalidateQueries({ queryKey: ["rubrics"] });
      setDeleteTargetComp(null);
      showSuccess(
        "Indikator Dihapus",
        `Indikator kompetensi "${compName}" berhasil dihapus dari rubrik kandidat.`
      );
    } catch (error) {
      console.error("Failed to delete competency:", error);
      showError(
        "Tidak Dapat Menghapus Indikator",
        error instanceof Error
          ? error.message
          : "Indikator kompetensi sudah tertaut pada rekaman evaluasi yang ada."
      );
    } finally {
      setIsMutating(false);
    }
  };

  const totalWeight =
    activeProfile?.competencies.reduce((sum, c) => sum + c.weight, 0) || 0;

  return (
    <div className="space-y-5">
      <PageBreadcrumb pageTitle="Rubrics & Competencies" />

      {/* Role-Based Scoping Banner */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-brand-200 bg-brand-50/60 p-4 dark:border-brand-500/20 dark:bg-brand-500/10">
        <div className="flex items-center gap-3 text-start">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-500 text-white shadow-2xs">
            <BoltIcon />
          </div>
          <div>
            <h4 className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <span>Candidate-Scoped &amp; Auto-Generated Rubrics</span>
              <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-mono font-bold text-brand-700 shadow-2xs dark:bg-gray-900 dark:text-brand-300">
                TRANSCRIPT DRIVEN
              </span>
            </h4>
            <p className="text-xs text-gray-600 dark:text-gray-300 mt-0.5">
              Rubrik dan kompetensi dipisahkan per kandidat dan di-generate otomatis oleh AI mengikuti bahasa (ID/EN) serta topik transkrip wawancara.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {activeProfile && (
            <Button
              variant="primary"
              size="sm"
              startIcon={
                isReEvaluating ? (
                  <TimeIcon className="animate-spin" />
                ) : (
                  <BoltIcon />
                )
              }
              onClick={handleReEvaluate}
              disabled={isReEvaluating || isMutating}
            >
              {isReEvaluating ? "Mengevaluasi Transkrip..." : "Re-Evaluate dari Transkrip"}
            </Button>
          )}
        </div>
      </div>

      {/* Main Two-Column Layout: Left Candidate Selector, Right Rubric & Competencies */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Left Column: Candidate Selector */}
        <div className="lg:col-span-4 rounded-2xl border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
          <div className="flex items-center justify-between pb-3 border-b border-gray-100 dark:border-gray-800">
            <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 flex items-center gap-1.5">
              <UserIcon />
              <span>Daftar Kandidat ({candidates.length})</span>
            </h4>
            <span className="text-[11px] font-mono text-gray-400">Pilih Kandidat</span>
          </div>

          <div className="mt-3 space-y-2 max-h-[620px] overflow-y-auto pe-1">
            {isCandidatesLoading ? (
              <div className="p-8 text-center text-xs text-gray-400">
                Memuat daftar kandidat...
              </div>
            ) : candidates.length === 0 ? (
              <div className="p-6 text-center text-xs text-gray-400 border border-dashed rounded-xl">
                Belum ada data kandidat. Tambahkan kandidat di menu Candidates.
              </div>
            ) : (
              candidates.map((cand) => {
                const isSelected = activeCandidate?.id === cand.id;
                const candProfile = profiles.find(
                  (p) =>
                    p.candidate_id === cand.id ||
                    p.code.toUpperCase().includes(cand.candidate_code.toUpperCase())
                );
                const compCount = candProfile?.competencies.length ?? 0;

                return (
                  <button
                    key={cand.id}
                    type="button"
                    onClick={() => setSelectedCandidateId(cand.id)}
                    className={`w-full text-start p-3 rounded-xl border transition-all ${
                      isSelected
                        ? "border-brand-500 bg-brand-50/70 shadow-theme-xs dark:border-brand-500/40 dark:bg-brand-500/10"
                        : "border-gray-100 bg-gray-50/50 hover:bg-gray-100/70 dark:border-gray-800 dark:bg-gray-800/40 dark:hover:bg-gray-800/80"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="font-semibold text-xs text-gray-900 dark:text-white block">
                          {cand.name}
                        </span>
                        <span className="text-[11px] text-gray-500 dark:text-gray-400 block truncate">
                          {cand.applied_position}
                        </span>
                      </div>
                      <span className="font-mono text-[10px] font-bold text-gray-500 dark:text-gray-400 shrink-0">
                        {cand.candidate_code}
                      </span>
                    </div>

                    <div className="mt-2.5 flex items-center justify-between text-[10px]">
                      <span className="text-gray-400 font-mono">
                        {cand.status.replace("_", " ")}
                      </span>
                      {compCount > 0 ? (
                        <span className="inline-flex items-center gap-1 rounded bg-success-50 text-success-700 px-1.5 py-0.5 font-bold dark:bg-success-500/15 dark:text-success-300">
                          <CheckCircleIcon className="w-3 h-3 text-success-500" />
                          {compCount} Kompetensi
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded bg-warning-50 text-warning-700 px-1.5 py-0.5 font-semibold dark:bg-warning-500/15 dark:text-warning-300">
                          Menunggu Transkrip
                        </span>
                      )}
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Rubric Details & Competencies */}
        <div className="lg:col-span-8 rounded-2xl border border-gray-200 bg-white p-5 xl:p-6 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
          {!activeCandidate ? (
            <div className="p-12 text-center text-xs text-gray-400">
              Pilih salah satu kandidat di sebelah kiri untuk melihat rubrik penilaiannya.
            </div>
          ) : !activeProfile ? (
            /* Empty State for Selected Candidate without Rubric */
            <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50/60 p-8 text-center dark:border-gray-700 dark:bg-gray-800/30">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400 mx-auto mb-3">
                <BoltIcon />
              </div>
              <h4 className="text-sm font-semibold text-gray-800 dark:text-white">
                Rubrik Belum Dibuat untuk {activeCandidate.name} ({activeCandidate.candidate_code})
              </h4>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 max-w-md mx-auto">
                Saat rekaman wawancara kandidat diunggah, AI akan otomatis mentranskripsi dan meng-generate daftar kompetensi sesuai percakapan. Anda juga dapat membuat profil rubrik draft secara manual sekarang.
              </p>
              <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
                <Button
                  variant="primary"
                  size="sm"
                  startIcon={<PlusIcon />}
                  onClick={handleOpenCreateProfile}
                  disabled={isMutating}
                >
                  Siapkan Rubrik Manual
                </Button>
              </div>
            </div>
          ) : (
            /* Candidate Profile & Competencies Table */
            <div className="space-y-4">
              {/* Header Profile Info Banner */}
              <div className="rounded-xl border border-gray-200 bg-gray-50/80 p-4 dark:border-gray-800 dark:bg-gray-800/50">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-mono font-bold text-brand-600 dark:text-brand-400">
                        {activeProfile.code}
                      </span>
                      <Badge color="primary" size="sm">
                        {activeCandidate.name} ({activeCandidate.candidate_code})
                      </Badge>
                      <Badge
                        color={
                          activeProfile.target_role === "INTERVIEWER"
                            ? "info"
                            : "success"
                        }
                        size="sm"
                      >
                        {activeProfile.target_role === "INTERVIEWER"
                          ? "Pewawancara User"
                          : "HR Assessment"}
                      </Badge>
                      {activeProfile.owner_name && (
                        <span className="text-[11px] text-gray-500 dark:text-gray-400">
                          Owner: <strong>{activeProfile.owner_name}</strong>
                        </span>
                      )}
                    </div>

                    <h4 className="text-sm font-bold text-gray-900 dark:text-white mt-1.5">
                      {activeProfile.round_name}
                    </h4>
                    <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
                      {activeProfile.description}
                    </p>
                  </div>

                  <div className="flex items-center gap-4 self-end sm:self-center">
                    <div className="text-end">
                      <span className="text-[11px] text-gray-400 block">Total Bobot</span>
                      <div
                        className={`text-base font-bold font-mono ${
                          totalWeight === 100
                            ? "text-success-600 dark:text-success-400"
                            : "text-warning-500"
                        }`}
                      >
                        {totalWeight}%
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Toolbar */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
                <div>
                  <h4 className="text-sm font-semibold text-gray-800 dark:text-white/90">
                    Indikator Kompetensi Penilaian ({activeProfile.competencies.length})
                  </h4>
                  <p className="text-[11px] text-gray-500 dark:text-gray-400">
                    Diekstrak otomatis dari transkrip atau ditambahkan manual oleh HR/Pewawancara.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    startIcon={<PlusIcon />}
                    onClick={handleOpenAddCompetency}
                    disabled={!canMutateActiveProfile || isMutating}
                  >
                    Tambah Indikator Manual
                  </Button>
                </div>
              </div>

              {/* Competencies Table */}
              <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-800">
                <Table>
                  <TableHeader className="bg-gray-50 dark:bg-gray-800/60 border-b border-gray-200 dark:border-gray-800">
                    <TableRow>
                      <TableCell
                        isHeader
                        className="ps-4 pe-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300"
                      >
                        Kode
                      </TableCell>
                      <TableCell
                        isHeader
                        className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300"
                      >
                        Nama Kompetensi &amp; Pertanyaan Acuan Transkrip
                      </TableCell>
                      <TableCell
                        isHeader
                        className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300"
                      >
                        Bobot (%)
                      </TableCell>
                      <TableCell
                        isHeader
                        className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300"
                      >
                        Target Skor
                      </TableCell>
                      <TableCell
                        isHeader
                        className="pe-5 ps-3 py-3 text-end text-xs font-semibold text-gray-600 dark:text-gray-300"
                      >
                        Aksi
                      </TableCell>
                    </TableRow>
                  </TableHeader>
                  <TableBody className="divide-y divide-gray-100 dark:divide-gray-800">
                    {isRubricsLoading ? (
                      <TableRow>
                        <TableCell
                          colSpan={5}
                          className="py-8 text-center text-xs text-gray-400"
                        >
                          Memuat indikator kompetensi...
                        </TableCell>
                      </TableRow>
                    ) : activeProfile.competencies.length === 0 ? (
                      <TableRow>
                        <TableCell
                          colSpan={5}
                          className="py-8 text-center text-xs text-gray-400"
                        >
                          Belum ada indikator kompetensi. Unggah rekaman interview atau klik &quot;Tambah Indikator Manual&quot;.
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
                            <div className="flex flex-col text-start">
                              <span className="text-xs font-semibold text-gray-800 dark:text-white/90">
                                {comp.name}
                              </span>
                              <span className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5 leading-relaxed">
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
                                  title="Edit Indikator Kompetensi"
                                >
                                  <PencilIcon />
                                </button>
                                <button
                                  type="button"
                                  onClick={() => setDeleteTargetComp(comp)}
                                  className="h-8 w-8 inline-flex items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-500 shadow-theme-xs hover:border-error-300 hover:bg-error-50 hover:text-error-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:hover:border-error-500/30 dark:hover:bg-error-500/15 dark:hover:text-error-400 transition-all"
                                  title="Hapus Indikator Kompetensi"
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

              {/* Informational Guidance Footer */}
              <div className="rounded-xl border border-gray-200 bg-gray-50/70 p-3.5 dark:border-gray-800 dark:bg-gray-800/30 flex items-start gap-2.5 text-start">
                <span className="text-brand-500 mt-0.5 shrink-0">
                  <CheckCircleIcon />
                </span>
                <p className="text-[11px] text-gray-500 dark:text-gray-400 leading-relaxed">
                  Perubahan manual pada indikator di atas akan disinkronkan saat evaluasi berlangsung. Gunakan tombol <strong>&quot;Re-Evaluate dari Transkrip&quot;</strong> di atas untuk memerintahkan AI menilai ulang rekaman interview kandidat terhadap indikator terbaru.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Create Profile for Candidate Modal */}
      <Modal
        isOpen={isCreateProfileOpen}
        onClose={() => setIsCreateProfileOpen(false)}
        className="max-w-lg m-4"
      >
        <div className="p-6 sm:p-8">
          <h3 className="text-base font-bold text-gray-900 dark:text-white">
            Siapkan Rubrik Wawancara Kandidat
          </h3>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Buat rubrik penilaian terisolasi untuk <strong>{activeCandidate?.name}</strong> ({activeCandidate?.candidate_code}).
          </p>

          <div className="mt-4 space-y-3">
            <FormField label="Nama Tahap Wawancara / Rubrik" required>
              <InputField
                value={customRoundTitle}
                onChange={(e) => setCustomRoundTitle(e.target.value)}
                placeholder="cth: Technical Round - Senior Frontend Engineer"
              />
            </FormField>
          </div>

          <div className="mt-6 flex justify-end gap-2.5 pt-3 border-t border-gray-100 dark:border-gray-800">
            <Button
              variant="outline"
              onClick={() => setIsCreateProfileOpen(false)}
              disabled={isMutating}
            >
              Batal
            </Button>
            <Button
              variant="primary"
              onClick={handleConfirmCreateProfile}
              disabled={isMutating}
            >
              {isMutating ? "Menyimpan..." : "Buat Rubrik"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Add / Edit Competency Modal */}
      <Modal
        isOpen={isCompModalOpen}
        onClose={() => setIsCompModalOpen(false)}
        className="max-w-xl m-4"
      >
        <div className="p-6 sm:p-8">
          <h3 className="text-base font-bold text-gray-900 dark:text-white">
            {editingComp
              ? "Edit Indikator Kompetensi"
              : "Tambah Indikator Kompetensi Manual"}
          </h3>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {editingComp
              ? `Perbarui kriteria pertanyaan pada rubrik ${activeProfile?.round_name}.`
              : `Tambahkan indikator pertanyaan acuan khusus pada rubrik ${activeProfile?.round_name}.`}
          </p>

          <div className="mt-4 space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <FormField label="Kode Indikator" required>
                <InputField
                  placeholder="cth: C1, SYS-ARCH"
                  value={compCode}
                  onChange={(e) => setCompCode(e.target.value)}
                />
              </FormField>

              <FormField label="Nama Kompetensi" required>
                <InputField
                  placeholder="cth: Technical Problem Solving"
                  value={compName}
                  onChange={(e) => setCompName(e.target.value)}
                />
              </FormField>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <FormField label="Bobot Penilaian (%)" required>
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

              <FormField label="Target Skor (1 - 5)" required>
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
              label="Pertanyaan Acuan / Indikator Bukti dari Transkrip"
              required
              hint="AI akan mencari bukti kalimat atau kutipan di transkrip wawancara berdasarkan panduan ini."
            >
              <TextArea
                rows={3}
                placeholder="Tuliskan pertanyaan yang diajukan dan bukti yang dicari dari jawaban kandidat..."
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
              Batal
            </Button>
            <Button
              variant="primary"
              onClick={handleSaveCompetency}
              disabled={isMutating}
            >
              {isMutating
                ? "Menyimpan..."
                : editingComp
                ? "Perbarui Indikator"
                : "Simpan Indikator"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Competency Confirmation Modal */}
      <ConfirmationModal
        isOpen={!!deleteTargetComp}
        onClose={() => setDeleteTargetComp(null)}
        onConfirm={handleConfirmDeleteCompetency}
        isLoading={isMutating}
        title="Hapus Indikator Kompetensi"
        description={`Apakah Anda yakin ingin menghapus indikator kompetensi "${deleteTargetComp?.name}" (${deleteTargetComp?.code}) dari rubrik ${activeProfile?.round_name}?`}
        confirmText="Ya, Hapus"
        cancelText="Batal"
        variant="danger"
      />
    </div>
  );
}
