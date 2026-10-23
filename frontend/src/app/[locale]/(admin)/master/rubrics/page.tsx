"use client";

import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import FormField from "@/components/form/FormField";
import InputField from "@/components/form/input/InputField";
import TextArea from "@/components/form/input/TextArea";
import Badge from "@/components/ui/badge/Badge";
import Button from "@/components/ui/button/Button";
import { Modal } from "@/components/ui/modal";
import {
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { initialRubricProfiles } from "@/data/mockMasterData";
import { PlusIcon, TrashBinIcon } from "@/icons";
import { CompetencyItem, RubricProfile } from "@/types/master";
import { useState } from "react";

export default function RubricsPage() {
  const [profiles, setProfiles] = useState<RubricProfile[]>(initialRubricProfiles);
  const [activeProfileId, setActiveProfileId] = useState<string>(profiles[0]?.id || "");

  // Add Competency Modal
  const [isAddCompOpen, setIsAddCompOpen] = useState(false);
  const [newCompCode, setNewCompCode] = useState("");
  const [newCompName, setNewCompName] = useState("");
  const [newCompDesc, setNewCompDesc] = useState("");
  const [newCompWeight, setNewCompWeight] = useState(25);
  const [newCompTarget, setNewCompTarget] = useState(4);

  const activeProfile = profiles.find((p) => p.id === activeProfileId) || profiles[0];

  const handleAddCompetency = () => {
    if (!newCompCode.trim() || !newCompName.trim()) {
      alert("Harap lengkapi kode dan nama kompetensi.");
      return;
    }

    const newItem: CompetencyItem = {
      id: `comp-${Date.now()}`,
      code: newCompCode.toUpperCase(),
      name: newCompName,
      description: newCompDesc,
      weight: newCompWeight,
      target_score: newCompTarget,
    };

    setProfiles(
      profiles.map((p) =>
        p.id === activeProfile.id
          ? { ...p, competencies: [...p.competencies, newItem] }
          : p
      )
    );

    setNewCompCode("");
    setNewCompName("");
    setNewCompDesc("");
    setNewCompWeight(25);
    setNewCompTarget(4);
    setIsAddCompOpen(false);
  };

  const handleDeleteCompetency = (compId: string) => {
    setProfiles(
      profiles.map((p) =>
        p.id === activeProfile.id
          ? { ...p, competencies: p.competencies.filter((c) => c.id !== compId) }
          : p
      )
    );
  };

  const totalWeight = activeProfile?.competencies.reduce((sum, c) => sum + c.weight, 0) || 0;

  return (
    <div>
      <PageBreadcrumb pageTitle="Rubrics & Competencies" />

      {/* Main Container */}
      <div className="rounded-2xl border border-gray-200 bg-white p-5 xl:p-6 dark:border-gray-800 dark:bg-gray-900 shadow-theme-xs">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-gray-100 pb-5 dark:border-gray-800">
          <div>
            <h3 className="text-theme-xl font-semibold text-gray-800 dark:text-white/90">
              Evaluation Rubrics & Competencies
            </h3>
            <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
              The reference criteria for each interview round used by AI Copilot to summarize supporting evidence
            </p>
          </div>
        </div>

        {/* Profile Tabs */}
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
                <span className={`rounded-md px-1.5 py-0.5 text-[10px] font-mono ${
                  isActive ? "bg-white/20 text-white" : "bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300"
                }`}>
                  {prof.code}
                </span>
              </button>
            );
          })}
        </div>

        {/* Profile Info Banner */}
        {activeProfile && (
          <div className="mt-4 rounded-xl border border-gray-100 bg-gray-50/70 p-4 dark:border-gray-800 dark:bg-gray-800/40">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-mono font-medium text-brand-600 dark:text-brand-400">
                  {activeProfile.code}
                </span>
                <h4 className="text-sm font-semibold text-gray-900 dark:text-white mt-0.5">
                  {activeProfile.round_name}
                </h4>
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  {activeProfile.description}
                </p>
              </div>
              <div className="text-end">
                <span className="text-[11px] text-gray-400">Total Weight</span>
                <div className={`text-base font-bold ${totalWeight === 100 ? "text-success-600 dark:text-success-400" : "text-warning-500"}`}>
                  {totalWeight}%
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Competencies Table Header & Button */}
        <div className="mt-5 flex items-center justify-between">
          <h4 className="text-sm font-semibold text-gray-800 dark:text-white/90">
            List of Competency Indicators ({activeProfile?.competencies.length || 0})
          </h4>
          <Button
            variant="outline"
            size="sm"
            startIcon={<PlusIcon/>}
            onClick={() => setIsAddCompOpen(true)}
          >
            Add Competency Indicator
          </Button>
        </div>

        {/* Competencies Table */}
        <div className="mt-3 overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-800">
          <Table>
            <TableHeader className="bg-gray-50 dark:bg-gray-800/60 border-b border-gray-200 dark:border-gray-800">
              <TableRow>
                <TableCell isHeader className="ps-4 pe-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300">
                  Code
                </TableCell>
                <TableCell isHeader className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300">
                  Competency Name & Description
                </TableCell>
                <TableCell isHeader className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300">
                  Weight (%)
                </TableCell>
                <TableCell isHeader className="px-3 py-3 text-start text-xs font-semibold text-gray-600 dark:text-gray-300">
                  Target Score
                </TableCell>
                <TableCell isHeader className="pe-5 ps-3 py-3 text-end text-xs font-semibold text-gray-600 dark:text-gray-300">
                  Actions
                </TableCell>
              </TableRow>
            </TableHeader>
            <TableBody className="divide-y divide-gray-100 dark:divide-gray-800">
              {activeProfile?.competencies.map((comp) => (
                <TableRow key={comp.id} className="hover:bg-gray-50/70 dark:hover:bg-white/[0.02] transition-colors">
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
                    <button
                      type="button"
                      onClick={() => handleDeleteCompetency(comp.id)}
                      className="h-8 w-8 inline-flex items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-500 shadow-theme-xs hover:border-error-300 hover:bg-error-50 hover:text-error-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:hover:border-error-500/30 dark:hover:bg-error-500/15 dark:hover:text-error-400 transition-all"
                      title="Delete Competency"
                    >
                      <TrashBinIcon/>
                    </button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Footer Summary */}
        <div className="mt-4 flex items-center justify-between text-xs text-gray-400">
          <span>{activeProfile?.competencies.length || 0} active competencies for this round</span>
        </div>
      </div>

      {/* Add Competency Modal */}
      <Modal isOpen={isAddCompOpen} onClose={() => setIsAddCompOpen(false)} className="max-w-4xl m-4">
        <div className="p-10">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Add New Competency Indicator
          </h3>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Register a new assessment parameter for the {activeProfile?.round_name} profile.
          </p>

          <div className="mt-5 space-y-3.5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <FormField label="Competency Code" required>
                <InputField
                  placeholder="cth: SYS-ARCH"
                  value={newCompCode}
                  onChange={(e) => setNewCompCode(e.target.value)}
                />
              </FormField>

              <FormField label="Competency Name" required>
                <InputField
                  placeholder="cth: System Architecture & Scalability"
                  value={newCompName}
                  onChange={(e) => setNewCompName(e.target.value)}
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
                  value={newCompWeight}
                  onChange={(e) => setNewCompWeight(parseInt(e.target.value) || 20)}
                />
              </FormField>

              <FormField label="Target Skor Minimal (1 - 5)" required>
                <InputField
                  type="number"
                  min={1}
                  max={5}
                  value={newCompTarget}
                  onChange={(e) => setNewCompTarget(parseInt(e.target.value) || 4)}
                />
              </FormField>
            </div>

            <FormField label="Description & Evidence Guidelines for AI" required hint="AI will search for sentence evidence in the transcript that is relevant to these criteria.">
              <TextArea
                rows={3}
                placeholder="Explain the specific skill criteria sought from the candidate's answers..."
                value={newCompDesc}
                onChange={(e) => setNewCompDesc(e.target.value)}
              />
            </FormField>
          </div>

          <div className="mt-6 flex justify-end gap-2.5 pt-3 border-t border-gray-100 dark:border-gray-800">
            <Button variant="outline" onClick={() => setIsAddCompOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleAddCompetency}>
              Save
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
