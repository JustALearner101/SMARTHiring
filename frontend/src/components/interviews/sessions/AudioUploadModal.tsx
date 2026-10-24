"use client";

import React, { useState } from "react";
import { Modal } from "@/components/ui/modal";
import Button from "@/components/ui/button/Button";
import FormField from "@/components/form/FormField";
import InputField from "@/components/form/input/InputField";
import Select from "@/components/form/Select";
import { InterviewSession, ConsentStatus } from "@/types/interview";
import { AudioIcon, AlertIcon, LockIcon, UploadIcon, CheckCircleIcon } from "@/icons";

interface AudioUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (session: InterviewSession) => void;
}

export default function AudioUploadModal({
  isOpen,
  onClose,
  onSubmit,
}: AudioUploadModalProps) {
  const [candidateName, setCandidateName] = useState("Rina Kusuma");
  const [candidateCode, setCandidateCode] = useState("K-014");
  const [position, setPosition] = useState("Senior Frontend Developer");
  const [roundName, setRoundName] = useState("User Technical Interview (Round 1)");
  const [interviewerName, setInterviewerName] = useState("Budi Santoso");
  const [interviewerRole, setInterviewerRole] = useState("VP of Engineering");
  const [consentGranted, setConsentGranted] = useState(true);
  const [audioDuration, setAudioDuration] = useState("45:20");
  const [fileName, setFileName] = useState("interview_rina_kusuma_round1.mp3");
  const [fileSize, setFileSize] = useState("42.8 MB");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setFileName(file.name);
      setFileSize(`${(file.size / (1024 * 1024)).toFixed(1)} MB`);
      if (!audioDuration || audioDuration === "00:00") {
        setAudioDuration("45:20");
      }
    }
  };

  const handleLoadSample = () => {
    setFileName("interview_rina_kusuma_round1.mp3");
    setFileSize("42.8 MB");
    setAudioDuration("45:20");
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const consentStatus: ConsentStatus = consentGranted ? "GRANTED" : "NOT_GRANTED";

    const newSession: InterviewSession = {
      id: `int-${Date.now()}`,
      candidate_id: `cand-${Date.now()}`,
      candidate_name: candidateName,
      candidate_code: candidateCode,
      position,
      round_name: roundName,
      interviewer_name: interviewerName,
      interviewer_role: interviewerRole,
      scheduled_at: "Today — 10:00 - 11:00 WIB",
      consent_status: consentStatus,
      consent_at: consentGranted ? new Date().toISOString() : undefined,
      consent_notice_version: consentGranted ? "v2.1-id-recording-consent" : undefined,
      audio_url: `https://storage.internal/interviews/${fileName}`,
      audio_duration: audioDuration,
      job_status: consentGranted ? "IN_REVIEW" : "REJECTED_NO_CONSENT",
    };

    onSubmit(newSession);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} className="max-w-xl p-6">
      <div className="flex items-center gap-3 pb-4 border-b border-gray-100 dark:border-gray-800 pe-12">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
          <AudioIcon/>
        </div>
        <div className="flex-1">
          <h3 className="text-base font-semibold text-gray-900 dark:text-white">
            Ingest Audio Recording & Session
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Upload interview audio file to trigger speech-to-text and AI Copilot rubric evaluation.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="mt-4 space-y-4">
        {/* Candidate & Code */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <FormField label="Candidate Name" required>
            <InputField
              type="text"
              value={candidateName}
              onChange={(e) => setCandidateName(e.target.value)}
              placeholder="e.g. Rina Kusuma"
            />
          </FormField>

          <FormField label="Candidate Pseudonym Code" required>
            <InputField
              type="text"
              value={candidateCode}
              onChange={(e) => setCandidateCode(e.target.value)}
              placeholder="e.g. K-014 (per SDD D-03)"
            />
          </FormField>
        </div>

        {/* Position & Round */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <FormField label="Target Position" required>
            <InputField
              type="text"
              value={position}
              onChange={(e) => setPosition(e.target.value)}
              placeholder="e.g. Senior Frontend Developer"
            />
          </FormField>

          <FormField label="Interview Round" required>
            <Select
              options={[
                { value: "User Technical Interview (Round 1)", label: "User Technical (Round 1)" },
                { value: "HR Culture Fit Interview (Round 2)", label: "HR Culture Fit (Round 2)" },
                { value: "Executive Leadership (Round 3)", label: "Executive Leadership (Round 3)" },
              ]}
              defaultValue={roundName}
              onChange={(e) => setRoundName(e.target.value)}
            />
          </FormField>
        </div>

        {/* Interviewer */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <FormField label="Interviewer" required>
            <Select
              options={[
                { value: "Budi Santoso", label: "Budi Santoso (VP Engineering, WIB)" },
                { value: "Budi Raharjo", label: "Budi Raharjo (Head of Finance, WITA)" },
              ]}
              defaultValue={interviewerName}
              onChange={(e) => {
                const val = e.target.value;
                setInterviewerName(val);
                setInterviewerRole(val === "Budi Santoso" ? "VP of Engineering" : "Head of Finance");
              }}
            />
          </FormField>

          <FormField label="Detected Duration">
            <InputField
              type="text"
              value={audioDuration}
              onChange={(e) => setAudioDuration(e.target.value)}
              placeholder="MM:SS (e.g. 45:20)"
            />
          </FormField>
        </div>

        {/* Audio Recording File Upload Dropzone */}
        <FormField label="Upload Audio Recording File (.mp3, .wav, .m4a)" required>
          <div className="rounded-xl border-2 border-dashed border-gray-300 bg-gray-50/60 p-4 text-center transition-all hover:border-brand-500 hover:bg-brand-50/10 dark:border-gray-700 dark:bg-gray-800/40">
            <input
              type="file"
              id="audio-file-input"
              accept="audio/*,.mp3,.wav,.m4a"
              onChange={handleFileChange}
              className="hidden"
            />
            <label htmlFor="audio-file-input" className="cursor-pointer flex flex-col items-center">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400 mb-2 shadow-2xs">
                <UploadIcon/>
              </div>
              <span className="text-xs font-semibold text-gray-800 dark:text-white">
                Click to browse or drag &amp; drop audio recording
              </span>
              <span className="mt-0.5 text-[11px] text-gray-400">
                Supports MP3, WAV, M4A (Max. 100MB)
              </span>
            </label>

            {/* Selected File Card */}
            {fileName && (
              <div className="mt-3 flex items-center justify-between rounded-lg border border-brand-200 bg-white p-2.5 text-xs dark:border-brand-500/30 dark:bg-gray-900 shadow-2xs">
                <div className="flex items-center gap-2">
                  <AudioIcon className="text-brand-500 shrink-0" />
                  <div className="text-left">
                    <span className="font-semibold text-gray-900 dark:text-white block truncate max-w-[220px]">
                      {fileName}
                    </span>
                    <span className="text-[10px] text-gray-400">{fileSize} &bull; Audio Verified</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center gap-1 rounded bg-success-50 px-2 py-0.5 text-[10px] font-semibold text-success-700 dark:bg-success-500/15 dark:text-success-300">
                    <CheckCircleIcon/>
                    Ready for ASR
                  </span>
                  <button
                    type="button"
                    onClick={handleLoadSample}
                    className="text-[10px] text-brand-600 hover:underline dark:text-brand-400"
                    title="Reset to demo sample"
                  >
                    Reset
                  </button>
                </div>
              </div>
            )}
          </div>
        </FormField>

        {/* Consent Verification Section*/}
        <div className="rounded-xl border border-gray-200 bg-gray-50/70 p-4 dark:border-gray-800 dark:bg-gray-800/40">
          <div className="flex items-start gap-3">
            <input
              id="consent-check"
              type="checkbox"
              checked={consentGranted}
              onChange={(e) => setConsentGranted(e.target.checked)}
              className="mt-0.5 h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500 dark:border-gray-700 dark:bg-gray-900"
            />
            <label htmlFor="consent-check" className="cursor-pointer">
              <span className="block text-xs font-semibold text-gray-800 dark:text-gray-200">
                Candidate Recording Consent Granted (vconsent_status = GRANTED)
              </span>
              <span className="block mt-0.5 text-[11px] text-gray-500 dark:text-gray-400">
                Candidate explicitly consented to recording notification (version: v2.1-id-recording-consent) before the interview started.
              </span>
            </label>
          </div>

          {!consentGranted && (
            <div className="mt-3 flex items-start gap-2 rounded-lg bg-warning-50 p-2.5 text-xs text-warning-800 dark:bg-warning-500/10 dark:text-warning-300 border border-warning-200 dark:border-warning-500/20">
              <AlertIcon className="shrink-0 text-warning-600" />
              <span>
                <strong>Consent Check Warning (Rule BR-08):</strong> Without granted consent, AI pipeline will reject processing and assign status <code className="font-mono font-bold">REJECTED_NO_CONSENT</code>.
              </span>
            </div>
          )}
        </div>

        <div className="flex justify-end gap-2.5 pt-3 border-t border-gray-100 dark:border-gray-800">
          <Button variant="outline" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="primary" type="submit" startIcon={<LockIcon className="mr-1.5"/>}>
            Process Ingestion
          </Button>
        </div>
      </form>
    </Modal>
  );
}
