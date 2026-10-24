"use client";

import React, { createContext, useContext, useState } from "react";
import {
  SimulatedEmail,
  SimulatedWhatsAppMessage,
  QuickPresetType,
  SimulatorNotification,
} from "@/types/simulator";
import {
  initialEmails,
  initialWhatsAppMessages,
} from "@/data/mockSimulatorData";

interface GuardrailIncident {
  id: string;
  payload: string;
  reason: string;
  timestamp: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM";
}

interface SimulatorContextType {
  emails: SimulatedEmail[];
  whatsappMessages: SimulatedWhatsAppMessage[];
  isBotTyping: boolean;
  activeEmailId: string;
  selectedInterviewer: string;
  activeNegotiationRound: number;
  lastGuardrailIncident: GuardrailIncident | null;
  notifications: SimulatorNotification[];
  setActiveEmailId: (id: string) => void;
  setSelectedInterviewer: (name: string) => void;
  sendWhatsAppMessage: (text: string, presetType?: QuickPresetType) => void;
  sendEmailReply: (emailId: string, replyText: string) => void;
  dismissGuardrailAlert: () => void;
  resetSimulator: () => void;
}

const SimulatorContext = createContext<SimulatorContextType | undefined>(undefined);

const STORAGE_KEY_EMAILS = "smarthiring_sim_emails";
const STORAGE_KEY_WA = "smarthiring_sim_wa";
const STORAGE_KEY_ROUND = "smarthiring_sim_round";

export function SimulatorProvider({ children }: { children: React.ReactNode }) {
  const [emails, setEmails] = useState<SimulatedEmail[]>(() => {
    if (typeof window !== "undefined") {
      try {
        const saved = localStorage.getItem(STORAGE_KEY_EMAILS);
        if (saved) return JSON.parse(saved);
      } catch {
        // Fallback
      }
    }
    return initialEmails;
  });

  const [whatsappMessages, setWhatsAppMessages] = useState<SimulatedWhatsAppMessage[]>(() => {
    if (typeof window !== "undefined") {
      try {
        const saved = localStorage.getItem(STORAGE_KEY_WA);
        if (saved) return JSON.parse(saved);
      } catch {
        // Fallback
      }
    }
    return initialWhatsAppMessages;
  });

  const [isBotTyping, setIsBotTyping] = useState<boolean>(false);
  const [activeEmailId, setActiveEmailId] = useState<string>("mail-001");
  const [selectedInterviewer, setSelectedInterviewer] = useState<string>("Budi Santoso");
  const [activeNegotiationRound, setActiveNegotiationRound] = useState<number>(() => {
    if (typeof window !== "undefined") {
      try {
        const saved = localStorage.getItem(STORAGE_KEY_ROUND);
        if (saved) return parseInt(saved, 10);
      } catch {
        // Fallback
      }
    }
    return 1;
  });
  const [lastGuardrailIncident, setLastGuardrailIncident] = useState<GuardrailIncident | null>(null);
  const [notifications, setNotifications] = useState<SimulatorNotification[]>([]);

  // Save to localStorage
  const persistState = (newEmails: SimulatedEmail[], newWa: SimulatedWhatsAppMessage[], round: number) => {
    try {
      localStorage.setItem(STORAGE_KEY_EMAILS, JSON.stringify(newEmails));
      localStorage.setItem(STORAGE_KEY_WA, JSON.stringify(newWa));
      localStorage.setItem(STORAGE_KEY_ROUND, round.toString());
    } catch {
      // Ignore storage errors
    }
  };

  const dismissGuardrailAlert = () => {
    setLastGuardrailIncident(null);
  };

  const resetSimulator = () => {
    setEmails(initialEmails);
    setWhatsAppMessages(initialWhatsAppMessages);
    setActiveEmailId("mail-001");
    setActiveNegotiationRound(1);
    setLastGuardrailIncident(null);
    setNotifications([]);
    try {
      localStorage.removeItem(STORAGE_KEY_EMAILS);
      localStorage.removeItem(STORAGE_KEY_WA);
      localStorage.removeItem(STORAGE_KEY_ROUND);
    } catch {
      // Ignore
    }
  };

  const sendWhatsAppMessage = (text: string, presetType?: QuickPresetType) => {
    const nowTime = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    // Skenario 4: Prompt Injection Attack Interception
    if (presetType === "prompt_injection" || text.toLowerCase().includes("ignore") && text.toLowerCase().includes("system")) {
      const flaggedMsg: SimulatedWhatsAppMessage = {
        id: `wa-inj-${Date.now()}`,
        thread_id: "thread-orchestrate-001",
        sender: "candidate",
        sender_name: "Rina Kusuma",
        text,
        timestamp: nowTime,
        status: "delivered",
        is_guardrail_flagged: true,
        guardrail_reason: "Prompt Injection Detected: Directive override and unauthorized elevation attempt intercepted by Guardrail Scanner.",
      };

      const updatedWa = [...whatsappMessages, flaggedMsg];
      setWhatsAppMessages(updatedWa);
      persistState(emails, updatedWa, activeNegotiationRound);

      setLastGuardrailIncident({
        id: `inc-${Date.now()}`,
        payload: text,
        reason: "Guardrail Scanner detected adversarial prompt injection string in candidate WhatsApp stream.",
        timestamp: nowTime,
        severity: "CRITICAL",
      });

      return;
    }

    // Normal or Reschedule or Friday conflict message from Candidate
    const userMsg: SimulatedWhatsAppMessage = {
      id: `wa-cand-${Date.now()}`,
      thread_id: "thread-orchestrate-001",
      sender: "candidate",
      sender_name: "Rina Kusuma",
      text,
      timestamp: nowTime,
      status: "read",
    };

    const newWa = [...whatsappMessages, userMsg];
    setWhatsAppMessages(newWa);
    setIsBotTyping(true);

    // Bot autonomous reaction after 1200ms
    setTimeout(() => {
      setIsBotTyping(false);
      let botResponseText = "";
      let nextRound = activeNegotiationRound;
      let newEmailsList = [...emails];

      if (presetType === "friday_conflict" || text.toLowerCase().includes("jumat")) {
        // Skenario 3: Secondary Validator Friday Prayer Block
        botResponseText =
          "Mohon maaf Kak Rina, berdasarkan aturan operasional kantor, hari Jumat pukul 11:30 - 13:00 WIB dialokasikan khusus untuk waktu ibadah Sholat Jumat dan istirahat kerja (PERMISSIONS).\n\nKami menyarankan alternatif hari yang sama pukul 14:00 - 15:00 WIB atau hari Kamis jam kerja. Apakah Kak Rina berkenan dengan slot jam 14:00 WIB?";
      } else if (presetType === "reschedule" || text.toLowerCase().includes("jadwal ulang") || text.toLowerCase().includes("sidang")) {
        // Skenario 2: Reschedule Triage Request (Putaran 2 dari 3)
        nextRound = Math.min(3, activeNegotiationRound + 1);
        setActiveNegotiationRound(nextRound);

        botResponseText = `Terima kasih atas konfirmasinya, Kak Rina! Permohonan reschedule ke hari Kamis pukul 14:00 WIB telah kami terima.\n\nSistem SmartHiring AI sedang menyelaraskan dengan kalender Pak Budi Santoso (Putaran Negosiasi ${nextRound}/3). Draf perubahan jadwal telah dikirimkan ke email Hiring Manager untuk verifikasi.`;

        // Masukkan email reschedule ke inbox Interviewer
        const newRescheduleEmail: SimulatedEmail = {
          id: `mail-resched-${Date.now()}`,
          thread_id: "thread-orchestrate-001",
          sender_name: "SmartHiring AI Orchestrator",
          sender_email: "orchestrator@smarthiring.internal",
          sender_role: "AI Autonomous Agent",
          recipient_name: "Budi Santoso",
          recipient_email: "budi.santoso@company.internal",
          subject: `[Triage Round ${nextRound}/3] Reschedule Request: Rina Kusuma proposes Thursday 14:00 WIB`,
          body_text: `Halo Pak Budi Santoso,\n\nKandidat Rina Kusuma memohon penyesuaian jadwal wawancara karena berhalangan (jadwal sidang skripsi pada slot Rabu 10:00 WIB).\n\nKandidat mengusulkan waktu alternatif:\n• Tanggal: Kamis, 30 Oktober 2026\n• Waktu: 14:00 - 15:00 WIB (15:00 - 16:00 WITA)\n• Status Kalender Anda: TERSEDIA (Slot kosong terdeteksi)\n• Format: Google Meet\n\nSistem AI Orchestrator menunggu konfirmasi Anda melalui tombol di bawah atau melalui dashboard /orchestration/scheduling.`,
          sent_at: "Just now",
          is_read: false,
          is_starred: true,
          folder: "inbox",
          tags: ["Reschedule", "High-Impact"],
          meeting_details: {
            platform: "Google Meet",
            meeting_link: "https://meet.google.com/abc-defg-hij",
            date_formatted: "Thursday, 30 Oct 2026",
            time_wib: "14:00 - 15:00 WIB",
            time_wita: "15:00 - 16:00 WITA",
            calendar_ref: "cal-budi-slot-02",
          },
        };

        newEmailsList = [newRescheduleEmail, ...newEmailsList];
        setEmails(newEmailsList);
        setActiveEmailId(newRescheduleEmail.id);
      } else if (presetType === "confirm" || text.toLowerCase().includes("konfirmasi") || text.toLowerCase().includes("siap")) {
        // Skenario 1: Happy Path Confirmation
        botResponseText =
          "Terima kasih atas konfirmasinya, Kak Rina! 🎉 Kehadiran Anda telah tercatat secara resmi di sistem kami. Undangan kalender dengan Google Meet telah disinkronkan.\n\nTips: Mohon siapkan koneksi internet stabil dan bergabung 5 menit sebelum sesi dimulai. Semoga sukses!";
      } else {
        // Generic response
        botResponseText =
          "Pesan Anda telah kami terima dan diteruskan ke sistem AI SmartHiring untuk diverifikasi bersama jadwal Hiring Manager.";
      }

      const botMsg: SimulatedWhatsAppMessage = {
        id: `wa-bot-${Date.now()}`,
        thread_id: "thread-orchestrate-001",
        sender: "bot",
        sender_name: "SmartHiring Assistant",
        text: botResponseText,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        status: "read",
      };

      const finalWa = [...newWa, botMsg];
      setWhatsAppMessages(finalWa);
      persistState(newEmailsList, finalWa, nextRound);
    }, 1200);
  };

  const sendEmailReply = (emailId: string, replyText: string) => {
    const targetEmail = emails.find((e) => e.id === emailId);
    if (!targetEmail) return;

    const sentEmail: SimulatedEmail = {
      id: `mail-reply-${Date.now()}`,
      thread_id: targetEmail.thread_id,
      sender_name: selectedInterviewer,
      sender_email: `${selectedInterviewer.toLowerCase().replace(/\s+/g, ".")}@company.internal`,
      sender_role: "Hiring Manager",
      recipient_name: "SmartHiring AI Orchestrator",
      recipient_email: "orchestrator@smarthiring.internal",
      subject: `Re: ${targetEmail.subject}`,
      body_text: replyText,
      sent_at: "Just now",
      is_read: true,
      is_starred: false,
      folder: "sent",
      tags: ["Confirmation"],
    };

    const updatedEmails = [sentEmail, ...emails];
    setEmails(updatedEmails);
    persistState(updatedEmails, whatsappMessages, activeNegotiationRound);

    // Also trigger bot message in WhatsApp if HM confirmed the reschedule
    if (replyText.toLowerCase().includes("setuju") || replyText.toLowerCase().includes("oke") || replyText.toLowerCase().includes("bisa")) {
      setIsBotTyping(true);
      setTimeout(() => {
        setIsBotTyping(false);
        const confirmationWa: SimulatedWhatsAppMessage = {
          id: `wa-bot-hm-confirm-${Date.now()}`,
          thread_id: "thread-orchestrate-001",
          sender: "bot",
          sender_name: "SmartHiring Assistant",
          text: "Kabar baik Kak Rina! Pak Budi Santoso telah menyetujui usulan jadwal Kamis pukul 14:00 - 15:00 WIB. Tautan Google Meet telah diperbarui di kalender Anda. Sampai jumpa!",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          status: "read",
        };
        const finalWa = [...whatsappMessages, confirmationWa];
        setWhatsAppMessages(finalWa);
        persistState(updatedEmails, finalWa, activeNegotiationRound);
      }, 1500);
    }
  };

  return (
    <SimulatorContext.Provider
      value={{
        emails,
        whatsappMessages,
        isBotTyping,
        activeEmailId,
        selectedInterviewer,
        activeNegotiationRound,
        lastGuardrailIncident,
        notifications,
        setActiveEmailId,
        setSelectedInterviewer,
        sendWhatsAppMessage,
        sendEmailReply,
        dismissGuardrailAlert,
        resetSimulator,
      }}
    >
      {children}
    </SimulatorContext.Provider>
  );
}

export function useSimulator() {
  const context = useContext(SimulatorContext);
  if (!context) {
    throw new Error("useSimulator must be used within a SimulatorProvider");
  }
  return context;
}
