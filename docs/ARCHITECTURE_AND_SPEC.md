# Heketon — HR & Office Ops AI Orchestrator
**Architecture, Orchestration & Accountability Specification (Tencent Cloud Hackathon Indonesia 2026)**

---

## 1. Product Positioning & Problem Statement

### 1.1 Background & Scope
Dalam pipeline rekrutmen perusahaan, tahap pengumpulan aplikasi awal dan screening CV biasanya sudah ditangani oleh ATS (*Applicant Tracking System*) atau form pendaftaran terpisah. Namun, **tahap pasca-seleksi awal (Post-Application Coordination)**—khususnya eskalasi kandidat ke **User Interview**—masih memakan waktu berjam-jam karena sifatnya yang sangat manual dan bolak-balik (*ping-pong*):
1. HR harus mengecek jadwal kosong *Hiring Manager (User)* dan mencocokkannya dengan zona waktu kandidat (**WIB / WITA / WIT**).
2. HR harus mengirim **Email formal** (beserta ringkasan CV) ke *User* dan menghubungi **Kandidat** melalui channel preferensinya (**WhatsApp** atau **Email**).
3. Ketika terjadi konflik jadwal (misal: *"User bisa tanggal 25, tapi kandidat membalas via WA tidak bisa tanggal 25"*), HR harus melakukan *triage* manual, mencari slot pengganti yang tidak menabrak jam kerja atau waktu **Sholat Jumat**, lalu mengirim ulang undangan ke kedua belah pihak.

### 1.2 Alignment dengan Hackathon Rulebook (`Challenge B — The Office Agent`)
Proyek ini dirancang sebagai **HR & Office Ops AI Orchestrator** yang menjawab **Challenge B (The Office Agent)**:
- **Hero Use Case**: Otomatisasi eskalasi kandidat ke *User Interview* & *Autonomous Schedule Triage* antara *Interviewer (Email)* dan *Kandidat (WhatsApp/Email)* melalui perintah *natural language*.
- **General Office Agent Compatibility**: Mesin orkestrasi LangGraph dirancang generik di atas entitas `Contact`, `CandidateApplication`, `CalendarEvent`, `Document/Note`, `Task`, dan `OperationalRule`. Dengan demikian, selain menangani use case rekrutmen, agen ini **100% siap mengeksekusi ~20 Test Cases resmi panitia** (seperti pengiriman notulen rapat, disambiguasi dua nama *"Pak Budi"*, penjadwalan lintas zona waktu, hingga deteksi *prompt injection* di dalam dokumen/pesan) serta **Live Surprise Test 90 detik** saat Demo Day.

---

## 2. Five Pillars of Agent Accountability (Compliance Matrix)

Sesuai halaman 2, 6, 7, dan 10 pada `docs/Rulebook.pdf`, setiap aksi agen tunduk pada 5 aturan akuntabilitas wajib berikut:

| Pilar Rulebook | Implementasi pada Sistem | Mekanisme Pencegahan Critical Failure |
| :--- | :--- | :--- |
| **1. SOURCES**<br>*(Shows its sources)* | Setiap rekomendasi slot jadwal, draf pesan, dan ringkasan kandidat wajib mencantumkan referensi ID sumber (`[cal-id]`, `[rule-id]`, `[doc-id]`, `[msg-id]`). | Output DTO dari `PlannerAgent` memiliki field wajib `sources_cited: list[SourceCitation]`. |
| **2. PERMISSIONS**<br>*(Stays within permissions & rules)* | Mematuhi aturan operasional Indonesia: konversi zona waktu **WIB/WITA/WIT**, jam kerja (09:00–17:00), blokir otomatis waktu **Sholat Jumat (11:30–13:00)**, dan hari libur nasional. Seluruh isi CV/chat/dokumen diperlakukan murni sebagai **data**, bukan instruksi (*Prompt Injection Guardrail*). | Node `GuardrailScanner` memindai *prompt injection* sebelum masuk ke Planner, dan `ValidatorAgent` memblokir jadwal yang melanggar aturan operasional. |
| **3. APPROVAL**<br>*(Asks before acting)* | **Hybrid Human-in-the-Loop (HITL)**: AI otomatis melakukan *triage* dan menyusun rencana aksi (*Who, What, When, Where, Channel, Content*), namun **wajib berhenti (`interrupt_before`)** di *Confirmation Card* sampai HR menekan tombol **Approve**. | Tool pengiriman Email/WA dan penulisan Kalender tidak dapat dipanggil langsung oleh LLM tanpa status `ActionPlan.status == APPROVED`. |
| **4. LIMITS**<br>*(Admits its limits)* | - **Disambiguasi**: Jika terdapat >1 kontak dengan nama yang sama (misal dua *"Pak Budi"*) atau informasi waktu tidak jelas, AI berhenti dan mengajukan pertanyaan klarifikasi singkat.<br>- **Max 3x Triage Loop**: Jika negosiasi jadwal User vs Kandidat ditolak >3 putaran atau kandidat membahas hal di luar wewenang jadwal (misal negosiasi gaji), AI menghentikan loop dan eskalasi ke HR. | State `negotiation_round` dibatasi maksimal `3`.Jika `ambiguity_detected == True` atau `round > 3`, graph beralih ke node `AskHumanClarification`. |
| **5. RECORD**<br>*(Keeps a record)* | Setiap input, sumber yang diperiksa, deteksi injeksi, hasil validasi *Secondary Agent*, persetujuan HR, hingga aksi yang dieksekusi (atau di-*undo*) dicatat secara *immutable* di tabel `audit_logs`. | Setiap transisi node LangGraph menulis jejak audit terstruktur ke PostgreSQL. |

### Bonus Capabilities (Rulebook Hal. 7) yang Diadopsi
1. **Secondary Validator Agent**: Agen kedua (`ValidatorAgent`) memverifikasi draf `ActionPlan` terhadap permintaan asli HR dan aturan operasional sebelum ditampilkan ke *Confirmation Screen*.
2. **High-Impact Action Confirmation**: Pengiriman pesan ke pihak eksternal (Kandidat) atau ke banyak penerima sekaligus memberi flag `is_high_impact = True` yang membutuhkan konfirmasi eksplisit di UI.
3. **60-Second Undo Buffer**: Setelah HR menekan **Approve & Send**, eksekusi masuk ke antrean *grace period* 60 detik (`APPROVED_PENDING_DISPATCH`) sehingga HR dapat menekan **Undo / Batalkan** sebelum pesan benar-benar dikirim.

---

## 3. Multi-Agent LangGraph Architecture

### 3.1 Alur Orkestrasi LangGraph
Berikut adalah topologi *StateGraph* di `backend/app/agent/`:

```mermaid
flowchart TD
    Start(["Input: Perintah Natural Language HR / Balasan Inbound WA & Email"]) --> Guardrail["1. Guardrail & Injection Scanner Node"]
    
    Guardrail -- "Prompt Injection Terdeteksi!" --> FlagSecurity["Blokir Instruksi Liar, Catat Audit Log & Beri Peringatan ke HR"]
    Guardrail -- "Aman" --> ContextRetriever["2. Context, Contact & Calendar Retriever Node"]
    
    ContextRetriever --> Planner["3. Planner & Triage Agent Node"]
    
    Planner -- "Ambigu (misal: 2 Pak Budi) / Out-of-Scope / Putaran > 3" --> Clarify(["Halt: Minta Klarifikasi / Eskalasi ke HR (LIMITS)"])
    Planner -- "Rencana Aksi Terbentuk" --> Validator["4. Secondary Validator Agent Node (BONUS)"]
    
    Validator -- "Melanggar Jam Kerja / Jumatan / Zona Waktu" --> Planner
    Validator -- "Valid & Sesuai Permintaan Asli" --> ApprovalGate{{"5. Human Approval Gate (LangGraph interrupt_before)"}}
    
    ApprovalGate -- "HR Klik Reject / Edit" --> Planner
    ApprovalGate -- "HR Klik Approve (+ High-Impact Check)" --> UndoBuffer["6. 60-Second Undo Buffer (BONUS)"]
    
    UndoBuffer -- "HR Klik Undo (< 60 dtk)" --> Cancelled(["Status: Undone & Dicatat di Audit Log"])
    UndoBuffer -- "Timer 60 dtk Selesai / Send Now" --> Executor["7. Channel & Calendar Executor Node"]
    
    Executor --> Audit["8. Immutable Audit Logger (RECORD)"]
    Audit --> End(["Selesai: Email Terkirim ke User, WA/Email ke Kandidat, Kalender Terupdate"])
```

### 3.2 Alur Triage & Rescheduling Otomatis (User vs Kandidat)
Ketika kandidat atau interviewer membalas bahwa jadwal tidak cocok (contoh: *"User bisa tgl 25, tapi kandidat gabisa"*):

```mermaid
sequenceDiagram
    autonumber
    actor HR as HR / Admin
    participant AI as LangGraph Orchestrator
    participant DB as Calendar & Rules DB
    actor User as Hiring Manager (Email)
    actor Cand as Kandidat (WhatsApp / Email)

    HR->>AI: "Eskalasi kandidat Rina ke User Interview sama Pak Budi minggu depan"
    AI->>DB: Cek kontak "Pak Budi", preferensi channel Rina (WA), Kalender Pak Budi, & Aturan (WIB/WITA/WIT, Jumatan)
    alt Terdapat >1 "Pak Budi"
        AI-->>HR: "Ada 2 Pak Budi: Budi Santoso (Engineering, WIB) & Budi Raharjo (Finance, WITA). Pilih yang mana?"
        HR->>AI: "Budi Santoso (Engineering)"
    end
    AI-->>HR: Tampilkan Confirmation Card (Draf Email ke Pak Budi + Draf WA ke Rina untuk opsi Tgl 25 10:00 WIB) + Badge High-Impact
    HR->>AI: Klik "Approve & Send" (Lewati/Selesai 60s Undo Window)
    AI->>User: Kirim Email Undangan Interview (Tgl 25 Okt, 10:00 WIB)
    AI->>Cand: Kirim WhatsApp Undangan Interview (Tgl 25 Okt, 10:00 WIB / 11:00 WITA)

    Note over User,Cand: Balasan Asinkron Masuk (via Dual-Mode Simulator / Webhook)
    User->>AI: Reply Email: "Oke, saya bisa tanggal 25 jam 10 pagi."
    Cand->>AI: Reply WA: "Maaf kak, tanggal 25 saya ada jadwal sidang. Kalau tanggal 26 atau Jumat siang bisa?"

    AI->>DB: Triage Otomatis (Putaran 1/3):<br/>1. Tandai Tgl 25 konflik.<br/>2. Tolak usulan "Jumat siang" (Bentrok aturan Sholat Jumat 11:30-13:00).<br/>3. Cek Kalender Pak Budi di Tgl 26 -> Kosong jam 14:00 WIB.
    AI-->>HR: Tampilkan Confirmation Card Revisi:<br/>- Alasan Triage & Sitasi Sumber<br/>- Draf Email Reschedule ke Pak Budi (26 Okt 14:00 WIB)<br/>- Draf WA Konfirmasi ke Rina (26 Okt 14:00 WIB)
    HR->>AI: Klik "Approve & Send"
    AI->>User: Kirim Email Update Jadwal (26 Okt 14:00 WIB)
    AI->>Cand: Kirim WA Update Jadwal (26 Okt 14:00 WIB)
```

---

## 4. Database Schema Design (`backend/app/model/`)

Semua model mewarisi [`BaseModel`](file:///D:/Project/Heketon/backend/app/model/base.py) (`id: UUID`, `created_at`, `updated_at`):

```mermaid
erDiagram
    CONTACT ||--o{ CALENDAR_EVENT : "has schedule"
    CONTACT ||--o{ CANDIDATE_APPLICATION : "interviews"
    CANDIDATE_APPLICATION ||--o{ NEGOTIATION_THREAD : "tracks scheduling"
    NEGOTIATION_THREAD ||--o{ ACTION_PLAN : "generates"
    ACTION_PLAN ||--|{ ACTION_ITEM : "decomposes into"
    NEGOTIATION_THREAD ||--o{ MESSAGE_LOG : "records WA/Email"
    ACTION_PLAN ||--o{ AUDIT_LOG : "audits"

    CONTACT {
        uuid id PK
        string full_name
        string role
        string department
        string email
        string phone_wa
        string timezone "WIB | WITA | WIT"
        boolean is_external
    }

    CANDIDATE_APPLICATION {
        uuid id PK
        string external_ats_id
        string full_name
        string email
        string phone_wa
        string preferred_channel "whatsapp | email"
        string timezone "WIB | WITA | WIT"
        string applied_position
        string stage "qualified | pending_schedule | negotiating | scheduled | escalated_to_hr"
        uuid interviewer_id FK
        text cv_summary
    }

    CALENDAR_EVENT {
        uuid id PK
        uuid contact_id FK
        string title
        datetime start_time_utc
        datetime end_time_utc
        string status "busy | tentative | cancelled"
    }

    OPERATIONAL_RULE {
        uuid id PK
        string rule_code "e.g. RULE-JUMATAN, RULE-OFFICE-HOURS"
        string category "working_hours | prayer_time | holiday | security"
        string description
        jsonb rule_config
    }

    NEGOTIATION_THREAD {
        uuid id PK
        uuid candidate_id FK
        uuid interviewer_id FK
        int current_round "Max 3 rounds before HR escalation"
        string status "awaiting_clarification | pending_approval | waiting_replies | confirmed | deadlock_escalated"
        datetime proposed_slot_utc
    }

    ACTION_PLAN {
        uuid id PK
        uuid thread_id FK
        text raw_request
        string status "clarification_needed | pending_approval | undo_window | executed | undone | rejected"
        boolean is_high_impact "True if external WA/Email or multi-recipient"
        boolean injection_detected
        jsonb sources_cited
        jsonb validator_report
        datetime undo_expires_at
        string approved_by
    }

    ACTION_ITEM {
        uuid id PK
        uuid action_plan_id FK
        string action_type "send_email | send_whatsapp | book_calendar | create_task"
        string recipient_name
        string recipient_contact
        string channel "email | whatsapp | calendar"
        datetime scheduled_for_utc
        text content_body
        string execution_status "pending | sent | cancelled"
    }

    MESSAGE_LOG {
        uuid id PK
        uuid thread_id FK
        string direction "outbound | inbound"
        string sender_role "hr_agent | interviewer | candidate"
        string channel "email | whatsapp"
        text body
    }

    AUDIT_LOG {
        uuid id PK
        uuid action_plan_id FK
        string event_type "request_received | guardrail_triggered | plan_validated | human_approved | action_undone | action_executed"
        jsonb what_agent_saw
        jsonb what_agent_decided
        jsonb what_agent_did
        string actor
    }
```

---

## 5. Pemetaan ke Struktur Folder MVC + Agent (`backend/app/`)

Sesuai konvensi layer singular yang sudah di-scaffold di `backend/app/`:

1. **`app/model/`**
   - `contact.py` (`Contact`)
   - `candidate.py` (`CandidateApplication`)
   - `calendar.py` (`CalendarEvent`, `OperationalRule`)
   - `orchestration.py` (`NegotiationThread`, `ActionPlan`, `ActionItem`, `MessageLog`)
   - `audit.py` (`AuditLog`)
2. **`app/dto/`**
   - `orchestration_dto.py` (Request natural language command, `ActionPlanResponseDTO`, `ClarificationQuestionDTO`, `ConfirmationCardDTO`, `InboundReplyWebhookDTO`)
   - `candidate_dto.py`, `contact_dto.py`, `audit_dto.py`
3. **`app/repository/`**
   - `contact_repository.py` (termasuk pencarian fuzzy nama untuk mendeteksi nama kembar/ambigu seperti *"Pak Budi"*)
   - `candidate_repository.py`
   - `calendar_repository.py` (query ketersediaan slot & pengecekan konflik jam kerja/Sholat Jumat lintas WIB/WITA/WIT)
   - `orchestration_repository.py` & `audit_repository.py`
4. **`app/agent/` (LangChain & LangGraph)**
   - `state.py` — Definisi `OrchestratorState` (`TypedDict`).
   - `nodes/guardrail.py` — Deteksi *prompt injection* pada input teks, catatan rapat, CV kandidat, dan balasan WA/Email.
   - `nodes/retriever.py` — Mengambil data kandidat, kontak, kalender, dan aturan operasional beserta ID sumbernya (`SOURCES`).
   - `nodes/planner.py` — Dekomposisi tugas (*who, what, when, where*) + logika *Triage Rescheduling* (maksimal 3 putaran).
   - `nodes/validator.py` — *Secondary Validator Agent* untuk mengecek kesesuaian rencana terhadap permintaan awal, zona waktu, dan aturan Sholat Jumat.
   - `tools/channel_adapter.py` — *Dual-Mode Adapter*: menulis ke *In-App Simulator Inbox* (untuk demo cepat 90 detik) + pengiriman ke SMTP/Resend & WhatsApp Gateway jika diaktifkan.
   - `graph.py` — Kompilasi `StateGraph` dengan `interrupt_before=["execute_actions"]` dan Postgres checkpointer.
5. **`app/service/`**
   - `orchestration_service.py` — Menjembatani controller dengan LangGraph (`invoke_command`, `clarify_ambiguity`, `approve_action_plan`, `undo_action_plan`, `handle_inbound_reply`).
   - `candidate_service.py`, `audit_service.py`
6. **`app/controller/`**
   - `orchestrator_controller.py` (`POST /api/v1/orchestrator/command`, `POST /api/v1/orchestrator/plans/{id}/approve`, `POST /api/v1/orchestrator/plans/{id}/undo`, `POST /api/v1/orchestrator/inbound-reply`)
   - `candidate_controller.py`, `simulator_controller.py`, `audit_controller.py`

---

## 6. Accountability Sheet Draft (Syarat Wajib Submission — Hal. 11 Rulebook)

Dokumen ini juga menjadi dasar langsung untuk **Accountability Sheet (1 halaman)** yang wajib dikumpulkan saat submission:

- **What the Agent Can Access**:
  - Data kandidat pasca-seleksi awal (`candidate_applications`), direktori kontak internal beserta zona waktu (`contacts`), jadwal kalender (`calendar_events`), serta tabel aturan operasional perusahaan (`operational_rules`).
- **What the Agent Executes Autonomously (Read-Only & Drafting)**:
  - Memindai *prompt injection* pada pesan/dokumen masuk.
  - Mendeteksi ambiguitas penerima (misal >1 kontak bernama *"Pak Budi"*) dan mengajukan pertanyaan klarifikasi.
  - Mengecek irisan jadwal kosong antara *Interviewer* dan *Kandidat* dengan memperhitungkan konversi **WIB/WITA/WIT**, jam kerja, dan waktu **Sholat Jumat**.
  - Melakukan *triage* balasan penolakan jadwal (maksimal 3 putaran) dan menyusun draf email/pesan WhatsApp beserta sitasi sumber (`SOURCES`).
  - Memvalidasi draf rencana menggunakan *Secondary Validator Agent*.
- **What Requires Human Approval (`APPROVAL`)**:
  - Mengirim Email ke *Hiring Manager / Stakeholder*.
  - Mengirim pesan WhatsApp / Email ke *Kandidat* (ditandai sebagai *High-Impact External Action*).
  - Mem-booking atau mengubah jadwal di kalender.
  - Menindaklanjuti negosiasi yang sudah melebihi 3 putaran (*deadlock*) atau pertanyaan kandidat di luar topik penjadwalan (misal negosiasi gaji).
- **What the Agent Will Never Do**:
  - Tidak pernah mengirim pesan eksternal atau mengubah kalender tanpa persetujuan eksplisit manusia.
  - Tidak pernah mengeksekusi instruksi tersembunyi (*prompt injection*) di dalam CV, catatan rapat, atau balasan chat.
  - Tidak pernah menebak kontak yang ambigu atau menjadwalkan rapat di waktu terlarang (seperti waktu Sholat Jumat).
