import {
  CalendarMatrixEvent,
  NegotiationThread,
  SlotConflictCheckRequest,
  SlotConflictCheckResult,
} from "@/types/orchestration";

/**
 * 5 Realistic Negotiation Threads demonstrating Pillar LIMITS (Max 3 Rounds & Deadlock Escalation)
 */
export const initialNegotiationThreads: NegotiationThread[] = [
  {
    id: "th-001",
    candidate_id: "cand-001",
    candidate_name: "Rina Kusuma",
    candidate_channel: "whatsapp",
    candidate_position: "Senior Frontend Engineer (Next.js)",
    candidate_phone: "+6281234567890",
    interviewer_id: "int-001",
    interviewer_name: "Budi Santoso",
    interviewer_role: "VP of Engineering",
    interviewer_dept: "Engineering",
    interviewer_timezone: "WIB",
    current_round: 1,
    max_rounds: 3,
    status: "NEGOTIATING",
    last_activity_at: "2026-10-24T08:45:00Z",
    last_message_preview: "AI mengajukan slot: Kamis, 29 Okt 2026, 10:00 - 11:00 WIB via Google Meet.",
    deadline_at: "2026-10-25T08:45:00Z",
    messages: [
      {
        id: "msg-001-1",
        round_number: 1,
        sender_role: "AI_ORCHESTRATOR",
        sender_name: "SmartHiring AI",
        channel: "whatsapp",
        sent_at: "2026-10-24T08:45:00Z",
        content:
          "Halo Rina, selamat! Tim People Operations PT Solusi Inovasi mengundang Anda untuk sesi User Technical Interview bersama Pak Budi Santoso (VP of Engineering). Kami mengusulkan jadwal: Kamis, 29 Oktober 2026 pukul 10:00 - 11:00 WIB via Google Meet. Mohon konfirmasi apakah Anda bersedia, atau kabari kami jika butuh opsi jadwal lain.",
        proposed_slot: "Kamis, 29 Oktober 2026, 10:00 - 11:00 WIB",
        source_citation: "[cal-budi-01]",
      },
    ],
  },
  {
    id: "th-002",
    candidate_id: "cand-002",
    candidate_name: "Ahmad Fauzi",
    candidate_channel: "whatsapp",
    candidate_position: "Backend AI Orchestration Lead",
    candidate_phone: "+6281398765432",
    interviewer_id: "int-001",
    interviewer_name: "Budi Santoso",
    interviewer_role: "VP of Engineering",
    interviewer_dept: "Engineering",
    interviewer_timezone: "WIB",
    current_round: 2,
    max_rounds: 3,
    status: "NEGOTIATING",
    last_activity_at: "2026-10-24T09:15:00Z",
    last_message_preview: "AI mengajukan slot alternatif: Rabu, 28 Okt 2026, 14:30 - 15:30 WIB (15:30 WITA).",
    deadline_at: "2026-10-25T09:15:00Z",
    messages: [
      {
        id: "msg-002-1",
        round_number: 1,
        sender_role: "AI_ORCHESTRATOR",
        sender_name: "SmartHiring AI",
        channel: "whatsapp",
        sent_at: "2026-10-23T14:00:00Z",
        content:
          "Halo Ahmad, mengundang sesi wawancara teknikal untuk posisi Backend AI Lead bersama Budi Santoso pada Rabu, 28 Okt pukul 10:00 WIB (11:00 WITA). Apakah waktu ini cocok untuk Anda?",
        proposed_slot: "Rabu, 28 Oktober 2026, 10:00 - 11:00 WIB",
        source_citation: "[cal-budi-01]",
      },
      {
        id: "msg-002-2",
        round_number: 1,
        sender_role: "CANDIDATE",
        sender_name: "Ahmad Fauzi",
        channel: "whatsapp",
        sent_at: "2026-10-24T08:30:00Z",
        content:
          "Pagi min, kebetulan Rabu jam 11 WITA saya ada sprint planning rutin di kantor. Apakah bisa geser ke sore hari sekitar jam 15:30 WITA (14:30 WIB)?",
        is_rejection: true,
      },
      {
        id: "msg-002-3",
        round_number: 2,
        sender_role: "AI_ORCHESTRATOR",
        sender_name: "SmartHiring AI",
        channel: "whatsapp",
        sent_at: "2026-10-24T09:15:00Z",
        content:
          "Terima kasih atas konfirmasinya, Ahmad. Kami telah memeriksa kalender Pak Budi dan slot Rabu, 28 Oktober 2026 pukul 14:30 - 15:30 WIB (15:30 - 16:30 WITA) tersedia. Kami reservasi slot ini untuk Anda, mohon balas 'OK' untuk finalisasi undangan rapat.",
        proposed_slot: "Rabu, 28 Oktober 2026, 14:30 - 15:30 WIB (15:30 WITA)",
        source_citation: "[cal-budi-02]",
      },
    ],
  },
  {
    id: "th-003",
    candidate_id: "cand-007",
    candidate_name: "Fajar Nugroho",
    candidate_channel: "whatsapp",
    candidate_position: "Data Platform Engineer",
    candidate_phone: "+6281777889900",
    interviewer_id: "int-002",
    interviewer_name: "Siti Rahmawati",
    interviewer_role: "Principal Systems Engineer",
    interviewer_dept: "Engineering",
    interviewer_timezone: "WIB",
    current_round: 3,
    max_rounds: 3,
    status: "DEADLOCK_ESCALATED",
    last_activity_at: "2026-10-24T07:20:00Z",
    last_message_preview: "Kandidat: 'Jumat sore saya luar kota. Mau tanya apa ada benefit remote full dan kisaran gaji?'",
    deadline_at: "2026-10-24T12:00:00Z",
    escalation_reason:
      "Batas 3 putaran negosiasi tercapai tanpa kesepakatan jadwal (Round 3/3 Limit Reached) + Kandidat mengajukan pertanyaan kompensasi & remote policy yang memerlukan wewenang manual HR (Pilar LIMITS & APPROVAL).",
    messages: [
      {
        id: "msg-003-1",
        round_number: 1,
        sender_role: "AI_ORCHESTRATOR",
        sender_name: "SmartHiring AI",
        channel: "whatsapp",
        sent_at: "2026-10-22T10:00:00Z",
        content:
          "Halo Fajar, kami mengundang Anda untuk sesi User Technical Interview bersama Bu Siti Rahmawati pada Selasa, 27 Okt pukul 11:00 WIB via Google Meet.",
        proposed_slot: "Selasa, 27 Oktober 2026, 11:00 - 12:00 WIB",
        source_citation: "[cal-siti-01]",
      },
      {
        id: "msg-003-2",
        round_number: 1,
        sender_role: "CANDIDATE",
        sender_name: "Fajar Nugroho",
        channel: "whatsapp",
        sent_at: "2026-10-22T14:10:00Z",
        content: "Halo, maaf Selasa seharian saya ada jadwal deployment ke klien, belum bisa.",
        is_rejection: true,
      },
      {
        id: "msg-003-3",
        round_number: 2,
        sender_role: "AI_ORCHESTRATOR",
        sender_name: "SmartHiring AI",
        channel: "whatsapp",
        sent_at: "2026-10-23T09:00:00Z",
        content:
          "Baik Fajar, bagaimana jika dialihkan ke hari Rabu, 28 Oktober 2026 pukul 15:00 - 16:00 WIB?",
        proposed_slot: "Rabu, 28 Oktober 2026, 15:00 - 16:00 WIB",
        source_citation: "[cal-siti-02]",
      },
      {
        id: "msg-003-4",
        round_number: 2,
        sender_role: "CANDIDATE",
        sender_name: "Fajar Nugroho",
        channel: "whatsapp",
        sent_at: "2026-10-23T16:30:00Z",
        content: "Rabu sore saya ada kursus. Bisakah Jumat jam 12:00 siang saja?",
        is_rejection: true,
      },
      {
        id: "msg-003-5",
        round_number: 3,
        sender_role: "AI_ORCHESTRATOR",
        sender_name: "SmartHiring AI",
        channel: "whatsapp",
        sent_at: "2026-10-24T06:00:00Z",
        content:
          "Mohon maaf, Jumat pukul 11:30 - 13:00 WIB adalah waktu istirahat & ibadah Sholat Jumat yang diblokir oleh kebijakan operasional perusahaan [rule-jumatan]. Kami dapat menawarkan slot alternatif pada Jumat, 30 Oktober 2026 pukul 14:00 - 15:00 WIB.",
        proposed_slot: "Jumat, 30 Oktober 2026, 14:00 - 15:00 WIB",
        source_citation: "[rule-jumatan] & [cal-siti-03]",
      },
      {
        id: "msg-003-6",
        round_number: 3,
        sender_role: "CANDIDATE",
        sender_name: "Fajar Nugroho",
        channel: "whatsapp",
        sent_at: "2026-10-24T07:20:00Z",
        content:
          "Jumat siang jam 14 saya sudah perjalanan ke bandara untuk urusan keluarga. Lagipula saya ingin tanya, untuk posisi ini kisaran gajinya berapa ya dan apakah bisa WFH permanen?",
        is_rejection: true,
      },
    ],
  },
  {
    id: "th-004",
    candidate_id: "cand-003",
    candidate_name: "Jessica Tanuwijaya",
    candidate_channel: "email",
    candidate_position: "Product Operations Lead",
    candidate_email: "jessica.tan@example.com",
    interviewer_id: "int-001",
    interviewer_name: "Budi Santoso",
    interviewer_role: "VP of Engineering",
    interviewer_dept: "Engineering",
    interviewer_timezone: "WIB",
    current_round: 1,
    max_rounds: 3,
    status: "SCHEDULED",
    last_activity_at: "2026-10-23T11:45:00Z",
    last_message_preview: "Kandidat telah menyetujui slot: Kamis, 29 Oktober 2026 pukul 13:30 - 14:30 WIB.",
    deadline_at: "2026-10-29T13:30:00Z",
    agreed_slot: "Kamis, 29 Oktober 2026, 13:30 - 14:30 WIB",
    messages: [
      {
        id: "msg-004-1",
        round_number: 1,
        sender_role: "AI_ORCHESTRATOR",
        sender_name: "SmartHiring AI",
        channel: "email",
        sent_at: "2026-10-23T10:00:00Z",
        content:
          "Dear Jessica, kami mengundang Anda untuk sesi User Technical Interview bersama Pak Budi Santoso pada Kamis, 29 Oktober 2026 pukul 13:30 - 14:30 WIB.",
        proposed_slot: "Kamis, 29 Oktober 2026, 13:30 - 14:30 WIB",
        source_citation: "[cal-budi-03]",
      },
      {
        id: "msg-004-2",
        round_number: 1,
        sender_role: "CANDIDATE",
        sender_name: "Jessica Tanuwijaya",
        channel: "email",
        sent_at: "2026-10-23T11:45:00Z",
        content:
          "Selamat siang, terima kasih atas undangannya. Saya menyetujui jadwal pada Kamis, 29 Oktober 2026 pukul 13:30 WIB. Saya akan bergabung via Google Meet tepat waktu.",
      },
    ],
  },
  {
    id: "th-005",
    candidate_id: "cand-006",
    candidate_name: "Bambang Prakoso",
    candidate_channel: "whatsapp",
    candidate_position: "Senior DevOps Engineer",
    candidate_phone: "+6281765432100",
    interviewer_id: "int-006",
    interviewer_name: "I Made Sukadana",
    interviewer_role: "Regional Operations Director",
    interviewer_dept: "Operations",
    interviewer_timezone: "WITA",
    current_round: 2,
    max_rounds: 3,
    status: "EXPIRED",
    last_activity_at: "2026-10-22T08:00:00Z",
    last_message_preview: "Batas SLA 24 jam terlewati tanpa tanggapan kandidat. Status thread kedaluwarsa.",
    deadline_at: "2026-10-23T08:00:00Z",
    messages: [
      {
        id: "msg-005-1",
        round_number: 1,
        sender_role: "AI_ORCHESTRATOR",
        sender_name: "SmartHiring AI",
        channel: "whatsapp",
        sent_at: "2026-10-21T09:00:00Z",
        content:
          "Halo Bambang, undangan interview bersama I Made Sukadana pada Kamis, 22 Okt 11:00 WITA.",
        proposed_slot: "Kamis, 22 Oktober 2026, 11:00 - 12:00 WITA",
        source_citation: "[cal-made-01]",
      },
      {
        id: "msg-005-2",
        round_number: 1,
        sender_role: "CANDIDATE",
        sender_name: "Bambang Prakoso",
        channel: "whatsapp",
        sent_at: "2026-10-21T10:15:00Z",
        content: "Halo, saya sedang lembur perbaikan server. Bisakah hari Jumat?",
        is_rejection: true,
      },
      {
        id: "msg-005-3",
        round_number: 2,
        sender_role: "AI_ORCHESTRATOR",
        sender_name: "SmartHiring AI",
        channel: "whatsapp",
        sent_at: "2026-10-22T08:00:00Z",
        content:
          "Slot alternatif tersedia: Jumat, 23 Oktober 2026 pukul 14:00 - 15:00 WITA. Mohon konfirmasi sebelum 24 jam.",
        proposed_slot: "Jumat, 23 Oktober 2026, 14:00 - 15:00 WITA",
        source_citation: "[cal-made-02]",
      },
    ],
  },
];

/**
 * Calendar Matrix Events with strict Friday Prayer blocks & Work Hour Constraints
 * Base reference dates: Late October 2026 (Mon 26 Oct - Fri 30 Oct 2026)
 */
export const initialCalendarMatrixEvents: CalendarMatrixEvent[] = [
  // Recurring / Policy Block: Friday Prayer for WIB interviewers (Budi Santoso & Siti Rahmawati)
  {
    id: "cal-block-jumatan-budi",
    interviewer_id: "int-001",
    title: "Blocked: Sholat Jumat & Istirahat",
    start: "2026-10-30T11:30:00",
    end: "2026-10-30T13:00:00",
    event_type: "FRIDAY_PRAYER_BLOCK",
    rule_code: "[rule-jumatan]",
    description: "Kebijakan Operasional Wajib: Rapat / wawancara dilarang pada 11:30 - 13:00 WIB.",
  },
  {
    id: "cal-block-jumatan-siti",
    interviewer_id: "int-002",
    title: "Blocked: Sholat Jumat & Istirahat",
    start: "2026-10-30T11:30:00",
    end: "2026-10-30T13:00:00",
    event_type: "FRIDAY_PRAYER_BLOCK",
    rule_code: "[rule-jumatan]",
    description: "Kebijakan Operasional Wajib: Rapat / wawancara dilarang pada 11:30 - 13:00 WIB.",
  },
  // Friday Prayer for WITA interviewer (I Made Sukadana in Makassar / Bali: 12:30 - 14:00 WITA)
  {
    id: "cal-block-jumatan-made",
    interviewer_id: "int-006",
    title: "Blocked: Sholat Jumat & Istirahat (WITA)",
    start: "2026-10-30T12:30:00",
    end: "2026-10-30T14:00:00",
    event_type: "FRIDAY_PRAYER_BLOCK",
    rule_code: "[rule-jumatan]",
    description: "Kebijakan Operasional Wajib: Pemblokiran waktu ibadah lokal WITA.",
  },

  // Events for Budi Santoso (int-001)
  {
    id: "cal-budi-sync-1",
    interviewer_id: "int-001",
    title: "Engineering Leadership Sync",
    start: "2026-10-26T09:30:00",
    end: "2026-10-26T11:00:00",
    event_type: "TEAM_MEETING",
    description: "Rapat koordinasi mingguan VP Eng bersama para Engineering Leads.",
  },
  {
    id: "cal-budi-interview-ahmad",
    interviewer_id: "int-001",
    title: "User Interview: Ahmad Fauzi",
    start: "2026-10-28T14:30:00",
    end: "2026-10-28T15:30:00",
    event_type: "SCHEDULED_INTERVIEW",
    candidate_name: "Ahmad Fauzi",
    description: "AI-Negotiated Slot (Round 2 Reschedule confirmed).",
  },
  {
    id: "cal-budi-interview-jessica",
    interviewer_id: "int-001",
    title: "User Interview: Jessica Tanuwijaya",
    start: "2026-10-29T13:30:00",
    end: "2026-10-29T14:30:00",
    event_type: "SCHEDULED_INTERVIEW",
    candidate_name: "Jessica Tanuwijaya",
    description: "AI Scheduled Interview Slot (Round 1 Agreed).",
  },
  {
    id: "cal-budi-retro",
    interviewer_id: "int-001",
    title: "Sprint Retrospective & OKR Check",
    start: "2026-10-29T16:00:00",
    end: "2026-10-29T17:00:00",
    event_type: "TEAM_MEETING",
    description: "Evaluasi mingguan deliverables tech team.",
  },

  // Events for Siti Rahmawati (int-002)
  {
    id: "cal-siti-arch",
    interviewer_id: "int-002",
    title: "Core Architecture Review",
    start: "2026-10-27T14:00:00",
    end: "2026-10-27T15:30:00",
    event_type: "TEAM_MEETING",
    description: "Review RFC sistem caching terdistribusi.",
  },
  {
    id: "cal-siti-external",
    interviewer_id: "int-002",
    title: "Out of Office (Client On-Site)",
    start: "2026-10-28T10:00:00",
    end: "2026-10-28T12:00:00",
    event_type: "OUT_OF_OFFICE",
    description: "Kunjungan instalasi on-premise klien.",
  },

  // Events for I Made Sukadana (int-006)
  {
    id: "cal-made-ops",
    interviewer_id: "int-006",
    title: "Regional Ops Standup (WITA)",
    start: "2026-10-27T08:30:00",
    end: "2026-10-27T09:30:00",
    event_type: "TEAM_MEETING",
    description: "Sinkronisasi logistik regional timur.",
  },
];

/**
 * Helper to simulate rule checking for SlotConflictCheckerModal
 */
export function checkSlotAvailability(
  req: SlotConflictCheckRequest,
  events: CalendarMatrixEvent[]
): SlotConflictCheckResult {
  const { date, time, duration_minutes, interviewer_id } = req;
  const [startHour, startMin] = time.split(":").map(Number);
  const startDecimal = startHour + startMin / 60;
  const endDecimal = startDecimal + duration_minutes / 60;

  // 1. Check Working Hours (09:00 - 17:00)
  if (startDecimal < 9 || endDecimal > 17) {
    return {
      is_available: false,
      status: "OUTSIDE_WORKING_HOURS",
      rule_code: "[rule-jam-kerja]",
      message: `Waktu ${time} - ${Math.floor(endDecimal)}:${Math.round((endDecimal % 1) * 60).toString().padStart(2, "0")} berada di luar jam operasional resmi perusahaan (09:00 - 17:00).`,
      suggested_alternatives: ["10:00", "14:00", "15:30"],
    };
  }

  // 2. Check Friday Prayer (Friday between 11:30 and 13:00)
  const dayOfWeek = new Date(date).getDay(); // 5 = Friday
  if (dayOfWeek === 5) {
    const prayerStart = 11.5; // 11:30
    const prayerEnd = 13.0;   // 13:00
    // Check overlap
    if (startDecimal < prayerEnd && endDecimal > prayerStart) {
      return {
        is_available: false,
        status: "BLOCKED_FRIDAY_PRAYER",
        rule_code: "[rule-jumatan]",
        message: "Slot ini menabrak waktu ibadah Sholat Jumat (11:30 - 13:00 WIB). Kebijakan operasional melarang penjadwalan pada jendela waktu ini.",
        suggested_alternatives: ["13:30", "14:00", "15:00"],
      };
    }
  }

  // 3. Check Conflicting Existing Events for this Interviewer
  const proposedStart = new Date(`${date}T${time}:00`).getTime();
  const proposedEnd = proposedStart + duration_minutes * 60 * 1000;

  for (const evt of events) {
    if (evt.interviewer_id === interviewer_id && evt.event_type !== "FRIDAY_PRAYER_BLOCK") {
      const evtStart = new Date(evt.start).getTime();
      const evtEnd = new Date(evt.end).getTime();

      // Check direct collision
      if (proposedStart < evtEnd && proposedEnd > evtStart) {
        return {
          is_available: false,
          status: "CONFLICT_EXISTING_EVENT",
          conflicting_event: evt.title,
          rule_code: "[cal-conflict-01]",
          message: `Interviewer sudah memiliki agenda lain pada jam tersebut: '${evt.title}'.`,
          suggested_alternatives: ["10:00", "13:30", "15:30"],
        };
      }

      // 4. Check Buffer Rule (15 minutes buffer)
      const bufferMs = 15 * 60 * 1000;
      const isBufferViolated =
        (proposedStart >= evtEnd && proposedStart < evtEnd + bufferMs) ||
        (proposedEnd <= evtStart && proposedEnd > evtStart - bufferMs);

      if (isBufferViolated) {
        return {
          is_available: false,
          status: "INSUFFICIENT_BUFFER",
          rule_code: "[rule-buffer-15m]",
          message: `Slot terlalu mepet dengan agenda '${evt.title}'. Kebijakan mewajibkan jeda istirahat/persiapan minimal 15 menit antar-sesi.`,
          suggested_alternatives: ["10:15", "13:45", "16:00"],
        };
      }
    }
  }

  // All clear!
  return {
    is_available: true,
    status: "VALID",
    message: `Slot ${date} pukul ${time} (${duration_minutes} menit) tersedia dan 100% mematuhi seluruh aturan operasional & buffer rapat.`,
    rule_code: "[cal-verified-ok]",
  };
}
