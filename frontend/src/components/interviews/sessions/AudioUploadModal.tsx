"use client";

import React, { useEffect, useState } from "react";
import { Link } from "@/i18n/navigation";
import { Modal } from "@/components/ui/modal";
import Button from "@/components/ui/button/Button";
import FormField from "@/components/form/FormField";
import InputField from "@/components/form/input/InputField";
import Select from "@/components/form/Select";
import { InterviewSession, ConsentStatus } from "@/types/interview";
import { getInterviewSessionStatus } from "@/services/interviewService";
import {
  AudioIcon,
  AlertIcon,
  LockIcon,
  UploadIcon,
  CheckCircleIcon,
  DocsIcon,
  TimeIcon,
  BoltIcon,
} from "@/icons";

interface AudioUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (session: InterviewSession, file?: File | null) => Promise<InterviewSession | null>;
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
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Live Async Progress State
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeSession, setActiveSession] = useState<InterviewSession | null>(null);
  const [progress, setProgress] = useState(15);
  const [statusMessage, setStatusMessage] = useState("Mengunggah berkas rekaman...");

  // Reset modal state
  const handleClose = () => {
    setIsProcessing(false);
    setActiveSession(null);
    setProgress(15);
    setStatusMessage("Mengunggah berkas rekaman...");
    onClose();
  };

  // Polling effect while modal is in processing view
  useEffect(() => {
    if (!isProcessing || !activeSession?.id) return;
    if (progress >= 100 || activeSession.job_status === "COMPLETED" || activeSession.job_status === "REJECTED_NO_CONSENT") {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const fresh = await getInterviewSessionStatus(activeSession.id);
        if (fresh) {
          setActiveSession(fresh);
          const pct = fresh.progress_percentage ?? (fresh.job_status === "COMPLETED" ? 100 : 30);
          setProgress(pct);
          if (fresh.current_step) {
            setStatusMessage(fresh.current_step);
          }
        }
      } catch (err) {
        console.error("Error polling interview progress:", err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [isProcessing, activeSession?.id, progress, activeSession?.job_status]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setFileName(file.name);
      setFileSize(`${(file.size / (1024 * 1024)).toFixed(1)} MB`);
      if (!audioDuration || audioDuration === "00:00") {
        setAudioDuration("45:20");
      }
    }
  };

  const handleLoadSample = () => {
    setSelectedFile(null);
    setFileName("interview_rina_kusuma_round1.mp3");
    setFileSize("42.8 MB");
    setAudioDuration("45:20");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const consentStatus: ConsentStatus = consentGranted ? "GRANTED" : "NOT_GRANTED";

    const newSession: InterviewSession = {
      id: `int-${Date.now()}`,
      candidate_id: "1",
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
      job_status: consentGranted ? "RECEIVED" : "REJECTED_NO_CONSENT",
      progress_percentage: 15,
      current_step: "Menginisiasi antrean transkripsi ElevenLabs Scribe...",
    };

    setIsProcessing(true);
    setProgress(15);
    setStatusMessage("Mengunggah berkas rekaman audio...");

    try {
      const created = await onSubmit(newSession, selectedFile);
      if (created) {
        setActiveSession(created);
        setProgress(created.progress_percentage ?? 25);
        if (created.current_step) {
          setStatusMessage(created.current_step);
        }
        if (!consentGranted || created.job_status === "REJECTED_NO_CONSENT") {
          handleClose();
        }
      }
    } catch (err) {
      console.error("Submission failed:", err);
      setIsProcessing(false);
    }
  };

  const isComplete = progress >= 100 || activeSession?.job_status === "COMPLETED";

  return (
    <Modal isOpen={isOpen} onClose={handleClose} className="max-w-xl p-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b border-gray-100 dark:border-gray-800 pe-12">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400">
          <AudioIcon />
        </div>
        <div className="flex-1">
          <h3 className="text-base font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <span>{isProcessing ? "Processing Interview Audio" : "Ingest Audio Recording & Session"}</span>
            <span className="rounded bg-purple-50 text-purple-700 dark:bg-purple-500/15 dark:text-purple-300 px-2 py-0.5 text-[10px] font-bold">
              ELEVENLABS SCRIBE ASR
            </span>
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {isProcessing
              ? "Asynchronous speech-to-text diarization & Copilot rubric analysis pipeline in progress."
              : "Upload interview audio file to trigger speech-to-text and AI Copilot rubric evaluation."}
          </p>
        </div>
      </div>

      {/* --- LIVE PROCESSING VIEW --- */}
      {isProcessing ? (
        <div className="mt-5 space-y-5">
          {/* Progress Bar Card */}
          <div className="rounded-2xl border border-gray-200 bg-gray-50/80 p-5 dark:border-gray-800 dark:bg-gray-850">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
                {!isComplete && <TimeIcon className="animate-spin text-brand-500" />}
                {isComplete ? "Pemrosesan Berhasil Selesai" : "Memproses Berkas Rekaman..."}
              </span>
              <span className="text-sm font-mono font-bold text-brand-600 dark:text-brand-400">
                {progress}%
              </span>
            </div>

            {/* Visual Animated Progress Bar */}
            <div className="w-full h-2.5 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ease-out ${
                  isComplete
                    ? "bg-success-500"
                    : "bg-linear-to-r from-brand-500 via-purple-500 to-brand-600 animate-pulse"
                }`}
                style={{ width: `${progress}%` }}
              />
            </div>

            <p className="mt-3 text-xs text-gray-600 dark:text-gray-300 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-brand-500 animate-ping shrink-0" />
              <span>{statusMessage}</span>
            </p>
          </div>

          {/* 4 Pipeline Stages Checklist */}
          <div className="space-y-2.5">
            <div
              className={`flex items-center justify-between p-3 rounded-xl border text-xs transition-colors ${
                progress >= 20
                  ? "border-success-200 bg-success-50/50 text-success-800 dark:border-success-500/20 dark:bg-success-500/10 dark:text-success-300"
                  : "border-gray-200 bg-white text-gray-500 dark:border-gray-800 dark:bg-gray-900"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <CheckCircleIcon className={progress >= 20 ? "text-success-600 dark:text-success-400" : "text-gray-300"} />
                <span className="font-semibold">1. Validasi Persetujuan &amp; Integritas Berkas</span>
              </div>
              <span className="text-[10px] font-mono font-bold">
                {progress >= 20 ? "DONE" : "QUEUED"}
              </span>
            </div>

            <div
              className={`flex items-center justify-between p-3 rounded-xl border text-xs transition-colors ${
                progress >= 60
                  ? "border-success-200 bg-success-50/50 text-success-800 dark:border-success-500/20 dark:bg-success-500/10 dark:text-success-300"
                  : progress >= 25
                  ? "border-brand-200 bg-brand-50/60 text-brand-800 dark:border-brand-500/20 dark:bg-brand-500/10 dark:text-brand-300 animate-pulse"
                  : "border-gray-200 bg-white text-gray-500 dark:border-gray-800 dark:bg-gray-900"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <CheckCircleIcon className={progress >= 60 ? "text-success-600 dark:text-success-400" : "text-gray-300"} />
                <div>
                  <span className="font-semibold block">2. ElevenLabs Scribe ASR &amp; Diarization</span>
                  <span className="text-[10px] text-gray-500 dark:text-gray-400">
                    Transkripsi Bahasa Indonesia &amp; deteksi pembicara (Candidate vs Interviewer)
                  </span>
                </div>
              </div>
              <span className="text-[10px] font-mono font-bold">
                {progress >= 60 ? "DONE" : progress >= 25 ? "IN PROGRESS" : "WAITING"}
              </span>
            </div>

            <div
              className={`flex items-center justify-between p-3 rounded-xl border text-xs transition-colors ${
                progress >= 85
                  ? "border-success-200 bg-success-50/50 text-success-800 dark:border-success-500/20 dark:bg-success-500/10 dark:text-success-300"
                  : progress >= 60
                  ? "border-brand-200 bg-brand-50/60 text-brand-800 dark:border-brand-500/20 dark:bg-brand-500/10 dark:text-brand-300 animate-pulse"
                  : "border-gray-200 bg-white text-gray-500 dark:border-gray-800 dark:bg-gray-900"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <CheckCircleIcon className={progress >= 85 ? "text-success-600 dark:text-success-400" : "text-gray-300"} />
                <div>
                  <span className="font-semibold block">3. Evaluasi Rubrik Kompetensi Copilot</span>
                  <span className="text-[10px] text-gray-500 dark:text-gray-400">
                    Pemetaan jawaban deskriptif netral &amp; penelusuran bukti kutipan
                  </span>
                </div>
              </div>
              <span className="text-[10px] font-mono font-bold">
                {progress >= 85 ? "DONE" : progress >= 60 ? "IN PROGRESS" : "WAITING"}
              </span>
            </div>

            <div
              className={`flex items-center justify-between p-3 rounded-xl border text-xs transition-colors ${
                isComplete
                  ? "border-success-200 bg-success-50/50 text-success-800 dark:border-success-500/20 dark:bg-success-500/10 dark:text-success-300"
                  : progress >= 85
                  ? "border-brand-200 bg-brand-50/60 text-brand-800 dark:border-brand-500/20 dark:bg-brand-500/10 dark:text-brand-300 animate-pulse"
                  : "border-gray-200 bg-white text-gray-500 dark:border-gray-800 dark:bg-gray-900"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <CheckCircleIcon className={isComplete ? "text-success-600 dark:text-success-400" : "text-gray-300"} />
                <span className="font-semibold">4. Audit Verifikasi Kutipan &amp; Deteksi Flag</span>
              </div>
              <span className="text-[10px] font-mono font-bold">
                {isComplete ? "DONE" : progress >= 85 ? "IN PROGRESS" : "WAITING"}
              </span>
            </div>
          </div>

          {/* Action Footer */}
          <div className="flex items-center justify-between pt-4 border-t border-gray-100 dark:border-gray-800">
            <Button variant="outline" type="button" onClick={handleClose} size="sm">
              {isComplete ? "Tutup" : "Jalankan di Latar Belakang"}
            </Button>

            {isComplete && activeSession && (
              <Link
                href={`/interviews/review?id=${activeSession.id}`}
                onClick={handleClose}
                className="inline-flex items-center gap-2 rounded-xl bg-brand-500 px-4 py-2.5 text-xs font-semibold text-white shadow-brand hover:bg-brand-600 transition-all"
              >
                <DocsIcon />
                <span>Buka Review Evidence &rarr;</span>
              </Link>
            )}
          </div>
        </div>
      ) : (
        /* --- FORM VIEW --- */
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
                  <UploadIcon />
                </div>
                <span className="text-xs font-semibold text-gray-800 dark:text-white">
                  Click to browse or drag &amp; drop audio recording
                </span>
                <span className="mt-0.5 text-[11px] text-gray-400">
                  Supports MP3, WAV, M4A &bull; ElevenLabs Scribe Diarization
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
                    <span className="inline-flex items-center gap-1 rounded bg-purple-50 px-2 py-0.5 text-[10px] font-semibold text-purple-700 dark:bg-purple-500/15 dark:text-purple-300">
                      <BoltIcon />
                      Scribe ASR Ready
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

          {/* Consent Verification Section */}
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
            <Button variant="outline" type="button" onClick={handleClose}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" startIcon={<LockIcon className="mr-1.5" />}>
              Process Ingestion (Async)
            </Button>
          </div>
        </form>
      )}
    </Modal>
  );
}
