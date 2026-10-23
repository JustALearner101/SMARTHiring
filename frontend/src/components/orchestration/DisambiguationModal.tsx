"use client";

import Button from "@/components/ui/button/Button";
import { Modal } from "@/components/ui/modal";
import { budiDisambiguationProfiles } from "@/data/mockOrchestrationData";
import { AlertIcon, CheckCircleIcon, InfoIcon } from "@/icons";
import { DisambiguationProfile } from "@/types/orchestration";
import React from "react";

interface DisambiguationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectInterviewer: (profile: DisambiguationProfile) => void;
  candidateName: string;
  targetPosition: string;
}

export default function DisambiguationModal({
  isOpen,
  onClose,
  onSelectInterviewer,
  candidateName,
  targetPosition,
}: DisambiguationModalProps) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} className="max-w-3xl m-4">
      <div className="p-8 sm:p-10">
        {/* Header Alert */}
        <div className="flex items-start gap-3.5 border-b border-gray-100 pb-5 dark:border-gray-800">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-warning-500 text-white shadow-theme-xs">
            <AlertIcon/>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-gray-900 dark:text-white">
                Clarification of Ambiguous Contacts (&quot;Dua Pak Budi&quot;)
              </h3>
              <span className="rounded-md bg-warning-50 px-2 py-0.5 text-[10px] font-mono font-semibold text-warning-700 dark:bg-warning-500/15 dark:text-warning-300">
                Rulebook Mandatory Gate
              </span>
            </div>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
              Your instructions refer to the name <strong>&quot;Pak Budi&quot;</strong>, but the system detected <strong>2 contacts</strong> with that name in the company directory. According to the <em>Admits its limits</em> principle, AI does not guess and asks for human confirmation.
            </p>
          </div>
        </div>

        {/* Candidate Context Pill */}
        <div className="mt-4 flex items-center justify-between rounded-xl bg-gray-50 p-3 text-xs dark:bg-gray-800/50">
          <span className="text-gray-600 dark:text-gray-400">
            Candidate: <strong className="text-gray-900 dark:text-white">{candidateName}</strong>
          </span>
          <span className="text-gray-600 dark:text-gray-400">
            Position: <strong className="text-brand-600 dark:text-brand-400">{targetPosition}</strong>
          </span>
        </div>

        {/* Two Budi Comparison Cards */}
        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
          {budiDisambiguationProfiles.map((budi, idx) => {
            const isEngineering = budi.department === "Engineering";
            return (
              <div
                key={budi.id}
                className={`flex flex-col justify-between rounded-2xl border p-5 transition-all ${
                  isEngineering
                    ? "border-brand-300 bg-brand-50/20 shadow-theme-xs dark:border-brand-500/30 dark:bg-brand-500/5"
                    : "border-gray-200 bg-white hover:border-gray-300 dark:border-gray-800 dark:bg-gray-900"
                }`}
              >
                <div>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-500 text-sm font-bold text-white shadow-theme-xs">
                        {budi.avatar_initials}
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-gray-900 dark:text-white">
                          {budi.name}
                        </h4>
                        <span className="text-[11px] font-mono text-gray-400">
                          {budi.employee_id}
                        </span>
                      </div>
                    </div>
                    {isEngineering && (
                      <span className="inline-flex items-center gap-1 rounded-full bg-success-50 px-2 py-0.5 text-[10px] font-medium text-success-700 dark:bg-success-500/15 dark:text-success-400">
                        <CheckCircleIcon/>
                        Paling Relevan
                      </span>
                    )}
                  </div>

                  <div className="mt-4 space-y-2 text-xs">
                    <div className="flex justify-between border-b border-gray-100/80 pb-1.5 dark:border-gray-800">
                      <span className="text-gray-400">Department</span>
                      <span className="font-semibold text-gray-700 dark:text-gray-300">
                        {budi.department}
                      </span>
                    </div>
                    <div className="flex justify-between border-b border-gray-100/80 pb-1.5 dark:border-gray-800">
                      <span className="text-gray-400">Positions</span>
                      <span className="font-medium text-gray-700 dark:text-gray-300">
                        {budi.role}
                      </span>
                    </div>
                    <div className="flex justify-between border-b border-gray-100/80 pb-1.5 dark:border-gray-800">
                      <span className="text-gray-400">Timezone</span>
                      <span className="font-mono text-gray-700 dark:text-gray-300">
                        {budi.timezone}
                      </span>
                    </div>
                    <div className="flex justify-between border-b border-gray-100/80 pb-1.5 dark:border-gray-800">
                      <span className="text-gray-400">Email</span>
                      <span className="font-mono text-[11px] text-gray-700 dark:text-gray-300">
                        {budi.email}
                      </span>
                    </div>
                  </div>

                  <div className="mt-3 flex items-start gap-1.5 text-[11px] text-gray-500 dark:text-gray-400 bg-gray-50/70 p-2 rounded-lg dark:bg-gray-800/40">
                    <InfoIcon className="text-brand-500 shrink-0 mt-0.5" />
                    <span>{budi.notes}</span>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-gray-100 dark:border-gray-800">
                  <Button
                    variant={isEngineering ? "primary" : "secondary"}
                    size="sm"
                    className="w-full justify-center"
                    onClick={() => onSelectInterviewer(budi)}
                  >
                    Select {budi.name} ({budi.department})
                  </Button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer info */}
        <div className="mt-6 flex items-center justify-between pt-4 border-t border-gray-100 dark:border-gray-800 text-[11px] text-gray-400">
          <span>AI must stop execution when facing data ambiguity.</span>
          <Button variant="outline" size="sm" onClick={onClose}>
            Cancel Command
          </Button>
        </div>
      </div>
    </Modal>
  );
}
