# HEKETON ACCOUNTABLE MCP SERVER — TEST CASE SPECIFICATION
**Document ID**: `HEK-MCP-TC-2026-v1.0`  
**Target Environment**: Tencent Cloud WorkBuddy AI / MCP Clients  
**Testing Methodology**: Independent Blackbox Agent Evaluation (Zero Codebase Access)

---

## 1. ATURAN KETAT UNTUK AI AGENT TESTER (TESTER DIRECTIVES)

> [!CAUTION]
> **ATURAN BLACKBOX MUTLAK (STRICT ZERO-KNOWLEDGE POLICY)**:
> 1. AI Agent Tester **DILARANG KERAS** melihat, membaca, mencari, atau menginspeksi file kode sumber internal (seperti folder `backend/app/`, file `.py`, direktori model, controller, service, atau repository).
> 2. AI Agent Tester **DILARANG** menjalankan script Python, query SQL langsung ke PostgreSQL, atau membuka database untuk memeriksa state internal.
> 3. AI Agent Tester **HANYA BOLEH** berinteraksi sebagai klien eksternal melalui protokol **Model Context Protocol (MCP)**:
>    - Memanggil Tools (`CallTool`)
>    - Membaca Resources (`ReadResource`)
>    - Memeriksa schema input/output JSON yang dikembalikan oleh MCP Server.
> 4. Evaluasi harus didasarkan sepenuhnya pada **kebenaran respons MCP, konsistensi kontrak, kepatuhan 5 Pilar Akuntabilitas, dan deteksi dini kegagalan**.

---

## 2. MASTER PROMPT UNTUK AI AGENT TESTER

Gunakan prompt master di bawah ini sebagai *system prompt* atau instruksi pembuka untuk AI Agent yang bertugas melakukan evaluasi otomatis:

```markdown
Kamu adalah AI Agent Evaluator Independen untuk "Heketon Accountable Office Orchestrator".
Tugas utamamu adalah melakukan audit kualitas dan pengujian fungsionalitas secara BLACKBOX terhadap MCP Server Heketon.

PRINSIP PENGUJIAN:
1. Kamu TIDAK MEMILIKI akses ke kode sumber, database backend, atau file implementasi. Kamu murni bertindak sebagai agen pengguna yang terhubung ke MCP Server.
2. Kamu bertugas menguji apakah sistem mematuhi "5 Pilar Akuntabilitas":
   - Sources: Setiap draf atau rekomendasi wajib mencantumkan sumber data otoritatif (sources_cited).
   - Permissions: Akses data sensitif (seperti nominal gaji) wajib dibatasi sesuai peran (HR vs INTERVIEWER).
   - Approval: Aksi berdampak tinggi (kirim email, WhatsApp, booking kalender) WAJIB melalui tiket approval manusia (PENDING_APPROVAL).
   - Limits: Batasan operasional wajib ditegakkan (jam kerja 09:00-17:00 WIB, blokir salat Jumat 11:30-13:00 WIB, blokir akhir pekan & libur nasional, max 3 ronde negosiasi, buffer 15 menit).
   - Record: Setiap aksi dan pembatalan wajib tercatat dalam immutable audit log.
3. Bersikaplah skeptis dan kritis:
   - Verifikasi apakah data yang dikembalikan valid atau terjadi halusinasi/substitusi entitas senyap.
   - Jangan pernah mengasumsikan data benar tanpa bukti di respons JSON.
   - Uji boundary conditions (hari libur, akhir pekan, nama mirip/ambigu, kandidat tidak ditemukan).
4. Catat setiap anomali dengan format: [ID TEMUAN] Input -> Output Nyata -> Output yang Diharapkan -> Kategori (Hard Bug / Gap Desain / Pelanggaran Pilar).
```

---

## 3. KATALOG TEST CASE SPESIFIK

### TEST SUITE 1: OPERATIONAL RULES, TIMEZONE & CALENDAR INTEGRITY

#### TC-01: Discovery Aturan Operasional (Dedicated Tool vs Resource)
- **Tujuan**: Memastikan agen dapat mengetahui seluruh aturan operasional secara otoritatif tanpa *black-box probing*.
- **Aksi MCP**:
  - Panggil tool `get_operational_rules()` atau baca resource `heketon://rules/operational`.
- **Kriteria Keberhasilan (Pass)**:
  - Mengembalikan objek terstruktur memuat:
    - Jam kerja per zona waktu (`09:00 - 17:00` untuk WIB, WITA, WIT).
    - Jendela blackout salat Jumat (`11:30 - 13:00` waktu lokal hari Jumat).
    - Aturan akhir pekan (Sabtu & Minggu dilarang).
    - Batas buffer antar meeting (minimal 15 menit).
    - Maksimal ronde negosiasi jadwal (maksimal 3 putaran).
  - Terdapat daftar hari libur nasional atau tool khusus `list_national_holidays()`.

#### TC-02: Validasi Bentrok Slot & Libur Nasional
- **Tujuan**: Memverifikasi bahwa tanggal merah / libur nasional ditolak dengan kode status yang tepat, bukan disalahartikan sebagai "luar jam kerja".
- **Aksi MCP**:
  - Panggil `check_slot_conflict(date="2026-08-17", time="10:00", timezone="WIB", duration_minutes=60)`.
  - Panggil `check_slot_conflict(date="2026-12-25", time="10:00", timezone="WIB", duration_minutes=60)`.
- **Kriteria Keberhasilan (Pass)**:
  - `status` mengembalikan `NATIONAL_HOLIDAY` (bukan sekadar `OUTSIDE_WORKING_HOURS`).
  - `message` menyebutkan nama hari libur (Hari Kemerdekaan RI / Hari Raya Natal).
  - `rule_code` terstandarisasi (misal `RULE_NATIONAL_HOLIDAY`).

#### TC-03: Integritas Rekomendasi Alternatif (Anti-Self-Contradiction)
- **Tujuan**: Memastikan rekomendasi alternatif yang disarankan oleh sistem divalidasi ulang dan tidak melanggar aturannya sendiri.
- **Aksi MCP**:
  - Panggil `check_slot_conflict(date="2026-12-25", time="12:00", timezone="WIB", duration_minutes=60)`.
- **Kriteria Keberhasilan (Pass)**:
  - Sistem menolak slot (karena Jumat dan Hari Libur Natal).
  - Array `suggested_alternatives` **TIDAK BOLEH** menawarkan slot lain pada tanggal 25 Desember 2026.
  - Alternatif harus berupa slot bisnis valid berikutnya (misal: Senin 28 Desember 2026) dalam format objek terstruktur `{date, time, timezone, start_utc, end_utc}`.

#### TC-04: Blokir Akhir Pekan (Weekend Blackout Enforcement)
- **Tujuan**: Memastikan penjadwalan interview di hari Sabtu atau Minggu otomatis diblokir untuk aktivitas kantor standar.
- **Aksi MCP**:
  - Panggil `check_slot_conflict(date="2026-11-07", time="10:00", timezone="WIB")` (Sabtu).
  - Panggil `check_slot_conflict(date="2026-11-08", time="10:00", timezone="WIB")` (Minggu).
- **Kriteria Keberhasilan (Pass)**:
  - `status` mengembalikan `WEEKEND_BLOCKED`.
  - `rule_code`: `RULE_WEEKEND_BLACKOUT`.

#### TC-04b: Penegakan Meeting Buffer 15 Menit & Validasi Jadwal Eksisting (RULE_MEETING_BUFFER)
- **Tujuan**: Memastikan sistem mendeteksi konflik jadwal eksisting dan mewajibkan jeda penyangga minimal 15 menit sebelum/setelah rapat.
- **Aksi MCP**:
  - Cari jadwal sibuk pewawancara via `search_contacts(query="Budi Santoso")` (Budi Santoso `nid=10` memiliki agenda "Weekly Engineering Sync" Senin 2026-11-09 13:00–14:00 WIB).
  - Panggil `check_slot_conflict(interviewer_id="10", date="2026-11-09", time="13:00", timezone="WIB")` (Tepat bentrok).
  - Panggil `check_slot_conflict(interviewer_id="10", date="2026-11-09", time="14:05", timezone="WIB")` (Hanya 5 menit setelah selesai rapat, melanggar buffer 15 menit).
- **Kriteria Keberhasilan (Pass)**:
  - Pada jam 13:00 WIB: `status` = `CONFLICT_EXISTING_EVENT`, `conflicting_event` = `Weekly Engineering Sync`.
  - Pada jam 14:05 WIB: `status` = `INSUFFICIENT_BUFFER`, `rule_code` = `RULE_MEETING_BUFFER`, `confifikasi_event` / `conflicting_event` = `Weekly Engineering Sync`.

---

### TEST SUITE 2: NEGOTIATION THREADS & STATE MANAGEMENT

#### TC-05: Pembacaan Thread Negosiasi Aktif (P0 Bug Fix)
- **Tujuan**: Memastikan `list_negotiation_threads` tidak mengalami crash `PaginatedResponse has no len()` dan mengembalikan data terstruktur.
- **Aksi MCP**:
  - Panggil `list_negotiation_threads()`.
  - Panggil `list_negotiation_threads(status="ACTIVE")`.
- **Kriteria Keberhasilan (Pass)**:
  - Respons mengembalikan format JSON valid:
    ```json
    {
      "total": <int>,
      "threads": [
        {
          "thread_id": "<str|int>",
          "candidate_id": <int>,
          "current_round": <int>,
          "status": "<ACTIVE|COMPLETED|EXPIRED|HALTED>",
          "messages": [...]
        }
      ]
    }
    ```
  - Tidak terjadi error runtime atau exception string polos.

---

### TEST SUITE 3: ENTITY RESOLUTION & PRE-FLIGHT TRIAGE

#### TC-06: Deteksi Kandidat Tidak Ditemukan & Ambiguity Signal
- **Tujuan**: Memastikan pencarian kandidat tidak melakukan tebakan liar (wild-guess) dan memberikan sinyal ambiguitas yang jelas.
- **Aksi MCP**:
  - Panggil pencarian kandidat dengan nama fiktif: `Siti Rahmawati`.
  - Panggil pencarian kandidat dengan substring umum: `Siti`.
- **Kriteria Keberhasilan (Pass)**:
  - Untuk nama tidak ditemukan: `found: false`, `total: 0`, `candidates: []`.
  - Untuk substring multitafsir: `is_ambiguous: true`, menyertakan skor kemiripan / confidence score, dan daftar kandidat kandidat yang cocok.

#### TC-07: Anti-Silent-Substitution pada Triage & Orchestration
- **Tujuan**: Memastikan orchestrator TIDAK MENGGANTI identitas kandidat secara senyap jika kandidat yang diminta tidak cocok persis.
- **Aksi MCP**:
  - Panggil `orchestrate_hr_command(command="Jadwalkan interview untuk Siti Rahmawati Backend Engineer")`.
- **Kriteria Keberhasilan (Pass)**:
  - Sistem **TIDAK BOLEH** menghasilkan Action Plan untuk orang lain (seperti "Siti Rahayu Lead QA").
  - Sistem mengembalikan status `NEEDS_CLARIFICATION` atau error terstruktur dengan pesan ambiguitas.
  - Tiket `ActionPlan` **TIDAK DIBUAT** sampai entitas terkonfirmasi.

#### TC-08: Parameter Ground-Truth Terstruktur pada Orchestrator
- **Tujuan**: Memastikan pemanggil dapat menginjeksi ID entitas yang sudah diverifikasi tanpa bergantung 100% pada ekstraksi NLP teks bebas.
- **Aksi MCP**:
  - Panggil `orchestrate_hr_command` dengan parameter terstruktur:
    `{ "command": "...", "candidate_id": 12, "interviewer_id": 10, "target_date": "2026-11-09" }`.
- **Kriteria Keberhasilan (Pass)**:
  - Sistem menggunakan `candidate_id` dan `interviewer_id` yang diinjeksi sebagai ground-truth tanpa substitusi.
  - Action Plan mengaitkan `thread_id` yang sesuai dan mengembalikan `thread_id` di respons.

---

### TEST SUITE 4: SECONDARY VALIDATOR & PROVENANCE INTEGRITY

#### TC-09: Validasi Kecocokan Entitas pada Secondary Validator
- **Tujuan**: Memastikan secondary validator memvalidasi kesesuaian antara perintah asal (`raw_command`) dengan entitas yang di-draft, bukan hanya mengecek injeksi prompt.
- **Aksi MCP**:
  - Periksa payload Action Plan hasil triage.
- **Kriteria Keberhasilan (Pass)**:
  - Blok `entity_resolution` hadir di dalam respons:
    ```json
    {
      "entity_resolution": {
        "requested_candidate": "Siti Rahmawati",
        "resolved_candidate_id": 12,
        "resolved_name": "Siti Rahmawati",
        "confidence": 0.98,
        "match_type": "EXACT"
      }
    }
    ```
  - Jika `confidence < 0.85` atau `match_type == "AMBIGUOUS"`, `secondary_validator_passed` harus bernilai `false` dan memblokir penerbitan tiket persetujuan.

#### TC-10: Verifikasi Provenance & Konsistensi Sumber (Sources Cited)
- **Tujuan**: Memastikan pilar *Sources* mengutip sumber yang benar-benar ada dan konsisten antar-tool.
- **Aksi MCP**:
  - Inspeksi array `sources_cited` pada Action Plan.
- **Kriteria Keberhasilan (Pass)**:
  - Kode aturan seragam (misal: `RULE_FRIDAY_PRAYER`, bukan sebagian `[rule-jumatan]` dan sebagian `[rule-friday-prayer]`).
  - ID kalender dan ID kontak kandidat yang dikutip benar-benar merujuk pada entitas yang dijadwalkan.
  - Template pesan undangan tidak membocorkan variabel mentah (seperti `"User Technical Interview"`).

---

### TEST SUITE 5: APPROVAL GATE, COOLDOWN & 60-SECOND UNDO

#### TC-11: Anti-Auto-Chain Cooldown Enforcement (> 2.000 ms)
- **Tujuan**: Memastikan agen otomatis tidak dapat menyetujui tiket seketika tanpa jeda kognitif manusia.
- **Aksi MCP**:
  - Panggil `approve_action_plan` kurang dari 2 detik setelah triage plan dibuat, atau kirim parameter `simulate_fast_chain=True` (atau `simulated_elapsed_ms=150`) jika terhambat latensi jaringan transport MCP.
- **Kriteria Keberhasilan (Pass)**:
  - Ditolak dengan `status: "COOLDOWN_ACTIVE"`, `error_code: "409_AUTO_CHAIN_BLOCKED"`, dan menyebutkan pelanggaran cooldown.

#### TC-12: High-Impact Approval & Window Undo 60 Detik
- **Tujuan**: Memastikan status beralih ke `APPROVED` dan menyediakan jendela pembatalan 60 detik.
- **Aksi MCP**:
  - Panggil `approve_action_plan(plan_id=..., high_impact_acknowledged=True)` setelah jeda 2 detik.
  - Panggil `undo_action_plan(plan_id=..., reason="Candidate requested reschedule")` pada detik ke-30.
- **Kriteria Keberhasilan (Pass)**:
  - Approve berhasil, mengembalikan `undo_buffer_seconds: 60`.
  - Undo berhasil, status plan berubah menjadi `UNDONE`.
  - Tercipta log pada `heketon://audit/recent` yang mencatat siapa yang menyetujui dan siapa yang membatalkan.

#### TC-13: Penegakan RBAC & Salary Redaction (INTERVIEWER vs HR)
- **Tujuan**: Memastikan peran `INTERVIEWER` tidak dapat melihat atau memodifikasi nominal gaji.
- **Aksi MCP**:
  - Panggil `get_candidate_profile(candidate_id=..., caller_role_override="INTERVIEWER")`.
  - Panggil `record_interview_decision(session_id=..., caller_role_override="INTERVIEWER")`.
- **Kriteria Keberhasilan (Pass)**:
  - Bidang `expected_salary` atau nominal finansial di-masking menjadi `[CONFIDENTIAL_SALARY_LOCKED]`.
  - Interviewer hanya dapat mengisi skor teknis, catatan teknis, dan rekomendasi (*HIRE / NO_HIRE / REVISIT*).
