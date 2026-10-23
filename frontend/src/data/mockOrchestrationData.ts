import { ActionPlan, AuditEvent, DisambiguationProfile, PresetScenario } from "@/types/orchestration";

/**
 * 4 Preset Scenarios for 1-Click Hackathon Jury Demo
 */
export const presetScenarios: PresetScenario[] = [
  {
    id: "scenario-disambiguation",
    label: "Uji Disambiguasi 'Dua Pak Budi'",
    tag: "LIMITS",
    prompt: "Jadwalkan interview Rina Kusuma dengan Pak Budi minggu depan",
    description: "AI mendeteksi 2 kontak bernama Budi dan meminta konfirmasi manusia.",
  },
  {
    id: "scenario-friday-prayer",
    label: "Uji Blokir Sholat Jumat",
    tag: "PERMISSIONS",
    prompt: "Jadwalkan interview Dimas Prasetyo dengan Siti Rahmawati hari Jumat jam 12:00 WIB",
    description: "AI otomatis memblokir jam 11:30–13:00 WIB dan menggeser slot ke 14:00 WIB.",
  },
  {
    id: "scenario-straight-escalation",
    label: "Eskalasi Cepat & 60s Undo",
    tag: "APPROVAL & SOURCES",
    prompt: "Eskalasi Rina Kusuma ke User Technical Interview dengan Budi Santoso",
    description: "Langsung menghasilkan Confirmation Card lengkap dengan sitasi sumber dan undo window.",
  },
  {
    id: "scenario-triage-round-3",
    label: "Batas Negosiasi Triage (Putaran 3)",
    tag: "LIMITS (Max 3)",
    prompt: "Proses balasan reschedule putaran ke-3 untuk kandidat Fajar Nugroho",
    description: "Mendemonstrasikan batas 3 putaran sebelum AI eskalasi manual ke HR.",
  },
];

/**
 * "Dua Pak Budi" Profiles for LIMITS Disambiguation Gate
 */
export const budiDisambiguationProfiles: DisambiguationProfile[] = [
  {
    id: "emp-001",
    name: "Budi Santoso",
    employee_id: "EMP-ENG-001",
    role: "VP of Engineering",
    department: "Engineering",
    timezone: "WIB (UTC+7, Jakarta)",
    email: "budi.santoso@company.com",
    phone: "+6281211112222",
    working_hours: "09:00 - 17:00",
    avatar_initials: "BS",
    notes: "Hiring Manager yang relevan untuk posisi Senior Frontend Engineer (Next.js)",
  },
  {
    id: "emp-004",
    name: "Budi Raharjo",
    employee_id: "EMP-FIN-001",
    role: "Head of Finance & Treasury",
    department: "Finance",
    timezone: "WITA (UTC+8, Makassar)",
    email: "budi.raharjo@company.com",
    phone: "+6281244445555",
    working_hours: "09:00 - 17:00",
    avatar_initials: "BR",
    notes: "Department Finance (Tidak sesuai dengan divisi engineering yang dilamar)",
  },
];

/**
 * Generator for ActionPlan based on Candidate & Interviewer
 */
export function generateSampleActionPlan(
  candidateName = "Rina Kusuma",
  candidatePosition = "Senior Frontend Engineer (Next.js)",
  interviewer = budiDisambiguationProfiles[0],
  command = "Jadwalkan interview Rina Kusuma dengan Budi Santoso",
  round = 1
): ActionPlan {
  return {
    id: `plan-${Date.now().toString().slice(-6)}`,
    candidate_id: "cand-001",
    candidate_name: candidateName,
    candidate_position: candidatePosition,
    interviewer_id: interviewer.id,
    interviewer_name: interviewer.name,
    interviewer_role: interviewer.role,
    interviewer_dept: interviewer.department,
    raw_command: command,
    negotiation_round: round,
    max_rounds: 3,
    status: "PENDING_APPROVAL",
    is_high_impact: true, // Candidate message via WhatsApp triggers high-impact
    guardrail_passed: true,
    guardrail_notes: "Prompt Injection Scanner: 0 malicious patterns detected. CV & chat inputs treated as pure data.",
    secondary_validator_passed: true,
    validator_notes: "Secondary Validator Agent: Slot Kamis 29 Okt 10:00 WIB verified against calendar slots, 09:00-17:00 working hours, and Friday prayer policies.",
    proposed_slot: {
      title: "User Technical Interview (Next.js & Frontend Architecture)",
      start_utc: "2026-10-29T03:00:00Z",
      end_utc: "2026-10-29T04:00:00Z",
      formatted_wib: "Kamis, 29 Oktober 2026 — 10:00 - 11:00 WIB",
      formatted_wita: "Kamis, 29 Oktober 2026 — 11:00 - 12:00 WITA",
      duration_minutes: 60,
      location_type: "Google Meet",
      meeting_link: "https://meet.google.com/smarthiring-eng-rina",
    },
    sources_cited: [
      {
        id: "src-cal-01",
        ref_code: "[cal-budi-01]",
        source_type: "CALENDAR",
        title: `Kalender ${interviewer.name}`,
        detail: "Slot kosong terkonfirmasi pada Kamis, 29 Okt 2026 pukul 10:00-11:00 WIB (tidak ada agenda lain).",
      },
      {
        id: "src-rule-01",
        ref_code: "[rule-office-hours]",
        source_type: "OPERATIONAL_RULE",
        title: "Aturan Jam Kerja (WIB/WITA)",
        detail: "Sesuai rentang operasional resmi 09:00 - 17:00 WIB. Tidak menabrak waktu istirahat.",
      },
      {
        id: "src-rule-02",
        ref_code: "[rule-jumatan-safe]",
        source_type: "OPERATIONAL_RULE",
        title: "Aturan Sholat Jumat (11:30 - 13:00)",
        detail: "Bebas dari waktu larangan (Jadwal di hari Kamis, bukan hari Jumat).",
      },
      {
        id: "src-ats-01",
        ref_code: "[cand-ats-rina]",
        source_type: "CANDIDATE_ATS",
        title: "Profil Pelamar & Channel Preferensi",
        detail: "Kandidat memilih WhatsApp (+6281234567890) sebagai jalur komunikasi utama (WIB).",
      },
      {
        id: "src-rubric-01",
        ref_code: "[rubric-eng-tech]",
        source_type: "OPERATIONAL_RULE",
        title: "Rubrik Penilaian: User Interview",
        detail: "Kompetensi target: SYS-ARCH (35%), REACT-ADV (35%), API-INT (30%).",
      },
    ],
    items: [
      {
        id: "item-email-user",
        action_type: "send_email",
        recipient_name: interviewer.name,
        recipient_role: `${interviewer.role} (${interviewer.department})`,
        recipient_contact: interviewer.email,
        channel: "email",
        subject: `[Interview Request] User Technical Interview: ${candidateName} — Senior Frontend Engineer`,
        content_preview: `Halo ${interviewer.name},\n\nSesuai arahan eskalasi dari HR, kami telah mencocokkan kalender Anda untuk sesi User Technical Interview bersama kandidat:\n\n• Nama: ${candidateName}\n• Posisi: ${candidatePosition}\n• Jadwal: Kamis, 29 Oktober 2026 (10:00 - 11:00 WIB)\n• Link Meeting: https://meet.google.com/smarthiring-eng-rina\n\nRingkasan profil dan portofolio kandidat dapat diakses pada tautan terlampir.\n\nSalam,\nSmartHiring AI Orchestrator on behalf of People Operations`,
        is_external: false,
      },
      {
        id: "item-wa-candidate",
        action_type: "send_whatsapp",
        recipient_name: candidateName,
        recipient_role: "Pelamar Kerja",
        recipient_contact: "+6281234567890",
        channel: "whatsapp",
        content_preview: `Halo Kak ${candidateName}! 👋\n\nSelamat! Berdasarkan hasil seleksi awal tim kami, Anda diundang ke tahap User Technical Interview untuk posisi ${candidatePosition}.\n\n📅 Jadwal: Kamis, 29 Oktober 2026\n⏰ Waktu: 10:00 - 11:00 WIB\n👤 Pewawancara: ${interviewer.name} (${interviewer.role})\n📍 Link Video Call: https://meet.google.com/smarthiring-eng-rina\n\nMohon konfirmasi ketersediaan Anda dengan membalas pesan ini. Terima kasih! 🙏`,
        is_external: true, // Triggers High-Impact confirmation
      },
      {
        id: "item-cal-booking",
        action_type: "book_calendar",
        recipient_name: "Internal Calendar System",
        recipient_role: "Work Calendar",
        recipient_contact: "tblm_calendar_event",
        channel: "calendar",
        subject: `Interview: ${candidateName} x ${interviewer.name}`,
        content_preview: `HOLD Slot: 29 Oct 2026, 10:00-11:00 WIB. Attendees: ${interviewer.email}, rina.kusuma@example.com.`,
        is_external: false,
      },
    ],
    created_at: new Date().toISOString(),
  };
}

/**
 * Initial Audit Events Stream
 */
export const initialAuditLogs: AuditEvent[] = [
  {
    id: "aud-001",
    timestamp: "21:05:12",
    event_type: "REQUEST_RECEIVED",
    title: "Natural Language Command Received",
    description: "HR menginstruksikan eskalasi kandidat via natural language bar.",
    actor: "HR Admin (You)",
    status_badge: "info",
  },
  {
    id: "aud-002",
    timestamp: "21:05:13",
    event_type: "GUARDRAIL_PASSED",
    title: "Prompt Injection Scanner: Clean",
    description: "Scan dokumen CV dan pesan masuk aman dari instruksi manipulasi LLM.",
    actor: "Guardrail Scanner Node",
    status_badge: "success",
  },
  {
    id: "aud-003",
    timestamp: "21:05:14",
    event_type: "SOURCES_RETRIEVED",
    title: "5 Evidence Sources Retrieved",
    description: "Kutipan [cal-budi-01], [rule-office-hours], dan [cand-ats-rina] diverifikasi.",
    actor: "Context Retriever Node",
    status_badge: "info",
  },
  {
    id: "aud-004",
    timestamp: "21:05:15",
    event_type: "PLAN_VALIDATED",
    title: "Secondary Validator Approved",
    description: "Rencana diverifikasi bebas dari pelanggaran jam ibadah & konversi WIB/WITA tepat.",
    actor: "Secondary Validator Agent",
    status_badge: "success",
  },
];
