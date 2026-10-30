# Backend API Contracts & OpenAPI Specification

Dokumen ini mendefinisikan spesifikasi kontrak REST API untuk backend **Heketon**. Seluruh endpoint dipasang di bawah prefix `settings.API_V1_STR` (`/api/v1`) dan didokumentasikan secara otomatis melalui Swagger UI di `http://localhost:8000/docs` dan OpenAPI JSON di `/api/v1/openapi.json`.

---

## 1. Standar Response Envelope

Seluruh response dari endpoint backend dibungkus menggunakan generic envelope [`ApiResponse[T]`](file:///D:/Project/Heketon/backend/app/dto/BaseDTO.py#L15-L25):

```json
{
  "success": true,
  "message": "Deskripsi status operasi yang informatif",
  "data": { ... }
}
```

- `success` (`bool`): Menandakan keberhasilan operasi (`true` untuk status 2xx, `false` untuk 4xx/5xx).
- `message` (`str`): Pesan deskriptif dalam Bahasa Indonesia yang siap ditampilkan ke UI.
- `data` (`T | None`): Objek atau array payload data utama. Bernilai `null` jika response tidak memiliki data atau terjadi error.

---

## 2. Standar Paginasi & Query Parameters

Endpoint yang mendukung pembacaan data massal menggunakan model [`PaginationParams`](file:///D:/Project/Heketon/backend/app/dto/BaseDTO.py#L36-L55) dan mengembalikan [`PaginatedResponse[T]`](file:///D:/Project/Heketon/backend/app/dto/BaseDTO.py#L26-L35):

### Request Query Parameters:
- `page` (`int`, default: `1`): Nomor halaman (1-based index).
- `page_size` (`int`, default: `20`, max: `100`): Jumlah data per halaman.

### Response Schema (`PaginatedResponse[T]`):
```json
{
  "items": [ ... ],
  "total": 45,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

---

## 3. Format Error Handling

Jika terjadi error pada request, sistem mengembalikan response HTTP sesuai status code dengan format envelope seragam:

```json
{
  "success": false,
  "message": "Pesan error spesifik mengenai kegagalan operasi",
  "data": null
}
```

### Pemetaan HTTP Status Codes:
- `200 OK`: Permintaan berhasil diproses.
- `201 Created`: Entitas baru berhasil dibuat.
- `400 Bad Request`: Payload data tidak valid secara logika bisnis.
- `401 Unauthorized`: Autentikasi diperlukan atau token kedaluwarsa.
- `403 Forbidden`: Akses tidak diizinkan untuk peran pengguna saat ini.
- `404 Not Found`: Entitas atau resource yang diminta tidak ditemukan di database.
- `409 Conflict`: Terjadi tabrakan data (misalnya duplikasi unique identifier atau tanggal).
- `422 Unprocessable Entity`: Validasi schema field Pydantic gagal (misalnya format email atau enum tidak sesuai).
- `500 Internal Server Error`: Terjadi kesalahan yang tidak terduga di server.

---

## 4. Katalog Kontrak 16 Domain API

### 4.1. Candidate Management (`CandidateController`)
- **Tag**: `CandidateManagement`
- **Base Route**: `/api/v1/candidates`

| Method | Endpoint | Request Body | Response Data Model | Deskripsi |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/candidates` | None (Query: `query`, `status`, pagination) | `PaginatedResponse[CandidateDTO]` | Mengambil daftar kandidat dengan filter dan paginasi. |
| `POST` | `/api/v1/candidates` | `CandidateCreateDTO` | `CandidateDTO` | Mendaftarkan profil pelamar baru (auto-generate ATS code). |
| `GET` | `/api/v1/candidates/{candidate_id}` | None | `CandidateDTO` | Mengambil detail kandidat berdasarkan ID. |
| `PATCH` | `/api/v1/candidates/{candidate_id}` | `CandidateUpdateDTO` | `CandidateDTO` | Memperbarui sebagian status atau profil kandidat. |

#### Contoh Payload Create Candidate:
```json
{
  "name": "Rina Kusuma",
  "email": "rina.kusuma@example.com",
  "phone": "+6281234567890",
  "preferred_channel": "whatsapp",
  "applied_position": "Senior Backend Engineer",
  "status": "SCREENING",
  "timezone": "WIB",
  "resume_url": "https://storage.smarthiring.ai/resumes/rina.pdf",
  "notes": "Pengalaman 5 tahun di FastAPI & microservices"
}
```

---

### 4.2. Contacts Directory (`ContactController`)
- **Tag**: `ContactsDirectory`
- **Base Route**: `/api/v1/contacts`

| Method | Endpoint | Request Body | Response Data Model | Deskripsi |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/contacts` | None (Query: `department`, `search`) | `list[InterviewerContactDTO]` | Mengambil direktori interviewer internal. |
| `POST` | `/api/v1/contacts` | `InterviewerCreateDTO` | `InterviewerContactDTO` | Menambahkan interviewer atau user baru. |
| `PATCH` | `/api/v1/contacts/{user_id}` | `InterviewerUpdateDTO` | `InterviewerContactDTO` | Memperbarui profil/jam kerja interviewer. |

---

### 4.3. National Holidays (`HolidayController`)
- **Tag**: `NationalHolidays`
- **Base Route**: `/api/v1/holidays`

| Method | Endpoint | Request Body | Response Data Model | Deskripsi |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/holidays` | None (Query: `year`) | `list[NationalHolidayDTO]` | Mengambil daftar libur nasional & cuti bersama. |
| `POST` | `/api/v1/holidays` | `NationalHolidayCreateDTO` | `NationalHolidayDTO` | Mendaftarkan hari libur atau cuti bersama baru. |

---

### 4.4. Operational Policies (`OperationalPolicyController`)
- **Tag**: `OperationalPolicies`
- **Base Route**: `/api/v1/operationalRules`

| Method | Endpoint | Request Body | Response Data Model | Deskripsi |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/operationalRules` | None | `OperationalPolicyDTO` | Mengambil aturan jam kerja aktif & threshold negosiasi. |
| `PUT` | `/api/v1/operationalRules` | `OperationalPolicyDTO` | `OperationalPolicyDTO` | Memperbarui kebijakan operasional dan buffer rapat. |

---

### 4.5. Assessment Rubrics (`RubricController`)
- **Tag**: `AssessmentRubrics`
- **Base Route**: `/api/v1/rubrics`

| Method | Endpoint | Request Body | Response Data Model | Deskripsi |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/rubrics` | None (Query: `for_interviewer_id`, `candidate_id`) | `list[RubricProfileDTO]` | Mengambil profil evaluasi rubrik berbasis per kandidat atau interviewer. |
| `POST` | `/api/v1/rubrics` | `RubricProfileCreateDTO` | `RubricProfileDTO` | Membuat profil rubrik penilaian kandidat baru. |
| `DELETE` | `/api/v1/rubrics/{profile_id}` | None | `dict[str, str]` | Menghapus profil rubrik penilaian. |
| `POST` | `/api/v1/rubrics/{profile_id}/re-evaluate` | None | `RubricProfileDTO` | Memicu AI LangGraph untuk mengevaluasi ulang penilaian kandidat langsung dari transkrip wawancara. |
| `POST` | `/api/v1/rubrics/{profile_id}/competencies` | `CompetencyCreateDTO` | `CompetencyItemDTO` | Menambahkan indikator kompetensi pada profil rubrik. |
| `PATCH` | `/api/v1/rubrics/{profile_id}/competencies/{competency_id}` | `CompetencyUpdateDTO` | `CompetencyItemDTO` | Memperbarui nama/bobot indikator kompetensi. |
| `DELETE` | `/api/v1/rubrics/{profile_id}/competencies/{competency_id}` | None | `dict[str, str]` | Menghapus indikator kompetensi. |

---

### 4.6. Orchestrator Commands (`OrchestratorCommandController`)
- **Tag**: `OrchestratorCommands`
- **Base Route**: `/api/v1/orchestrator`

| Method | Endpoint | Request Body | Response Data Model | Deskripsi |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/orchestrator/scenarios` | None | `list[PresetScenarioDTO]` | Mengambil daftar skenario demo interaktif. |
| `POST` | `/api/v1/orchestrator/command` | `CommandRequestDTO` | `ActionPlanDTO` | Menjalankan perintah bahasa alami untuk triase jadwal. |

#### Contoh Payload Command:
```json
{
  "command": "Jadwalkan technical interview untuk Rina Kusuma hari Rabu depan dengan Budi Santoso."
}
```

---

### 4.7. Action Plans & Approval (`ActionPlanController`)
- **Tag**: `ActionPlans`
- **Base Route**: `/api/v1/actionPlans`

| Method | Endpoint | Request Body | Response Data Model | Deskripsi |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/actionPlans/current` | None | `ActionPlanDTO` | Mengambil rencana aksi aktif yang menunggu approval. |
| `POST` | `/api/v1/actionPlans/{plan_id}/approve` | `PlanApprovalRequestDTO` | `ActionPlanDTO` | Human Approval Gate (memulai jendela undo 60 detik). |
| `POST` | `/api/v1/actionPlans/{plan_id}/undo` | `PlanUndoRequestDTO` | `ActionPlanDTO` | Membatalkan eksekusi jadwal dalam jendela undo. |

---

### 4.8. Negotiation Threads (`NegotiationThreadController`)
- **Tag**: `NegotiationThreads`
- **Base Route**: `/api/v1/negotiationThreads`

| Method | Endpoint | Request Body | Response Data Model | Deskripsi |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/negotiationThreads` | None (Query pagination) | `PaginatedResponse[NegotiationThreadDTO]` | Mengambil thread negosiasi jadwal lintas platform. |
| `GET` | `/api/v1/negotiationThreads/{thread_id}` | None | `NegotiationThreadDTO` | Mengambil log riwayat pesan lengkap pada suatu thread. |

---

### 4.9. Simulator Webmail (`SimulatorEmailController`)
- **Tag**: `SimulatorEmail`
- **Base Route**: `/api/v1/simulator/email`

| Method | Endpoint | Request Body | Response Data Model | Deskripsi |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/simulator/email/inbox` | None | `list[SimulatorEmailItemDTO]` | Mengambil inbox simulasi email interviewer. |

---

### 4.10. Simulator WhatsApp (`SimulatorWhatsAppController`)
- **Tag**: `SimulatorWhatsApp`
- **Base Route**: `/api/v1/simulator/whatsapp`

| Method | Endpoint | Request Body | Response Data Model | Deskripsi |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/simulator/whatsapp/messages` | None (Query: `thread_id`) | `list[SimulatorWhatsAppMessageDTO]` | Mengambil log chat WhatsApp kandidat. |
| `POST` | `/api/v1/simulator/whatsapp/send` | Query parameters (`thread_id`, `text`, `sender`) | `SimulatorWhatsAppMessageDTO` | Mengirim pesan simulasi balasan kandidat. |
| `GET` | `/api/v1/simulator/whatsapp/quickPresets` | None | `list[QuickPresetDTO]` | Mengambil template balasan cepat kandidat. |
| `GET` | `/api/v1/simulator/whatsapp/notifications` | None | `list[SimulatorWhatsAppNotificationDTO]` | Mengambil notifikasi status pesan WhatsApp. |

---

### 4.11. Interview Sessions (`InterviewSessionController`)
- **Tag**: `InterviewSessions`
- **Base Route**: `/api/v1/interviews/sessions`

| Method | Endpoint | Request Body | Response Data Model | Deskripsi |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/interviews/sessions` | None (Query: `candidate_code`, pagination) | `PaginatedResponse[InterviewSessionDTO]` | Mengambil sesi rekaman & pemrosesan interview. |
| `POST` | `/api/v1/interviews/sessions/upload` | `InterviewUploadRequestDTO` | `InterviewSessionDTO` | Mengunggah rekaman interview dengan status persetujuan. |
| `GET` | `/api/v1/interviews/sessions/{interview_id}` | None | `InterviewSessionDTO` | Mengambil detail hasil evaluasi sesi interview. |

---

### 4.12. Interview Transcripts (`InterviewTranscriptController`)
- **Tag**: `InterviewTranscripts`
- **Base Route**: `/api/v1/interviews/transcripts`

| Method | Endpoint | Request Body | Response Data Model | Deskripsi |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/interviews/transcripts/{interview_id}` | None | `list[TranscriptSegmentDTO]` | Mengambil segmen transkripsi dengan label pembicara. |

---

### 4.13. Interview Decisions (`InterviewDecisionController`)
- **Tag**: `InterviewDecisions`
- **Base Route**: `/api/v1/interviews/decisions`

| Method | Endpoint | Request Body | Response Data Model | Deskripsi |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/interviews/decisions/{interview_id}` | `HrDecisionRequestDTO` | `HrDecisionDTO` | Mencatat keputusan akhir HR (ADVANCE / HOLD / REJECT). |

---

### 4.14. Calendar Matrix (`CalendarMatrixController`)
- **Tag**: `CalendarMatrix`
- **Base Route**: `/api/v1/calendarMatrix`

| Method | Endpoint | Request Body | Response Data Model | Deskripsi |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/calendarMatrix/events` | None (Query: `start_date`, `end_date`) | `list[CalendarMatrixEventDTO]` | Mengambil jadwal kesibukan seluruh interviewer. |

---

### 4.15. Slot Conflict Checker (`SlotConflictCheckerController`)
- **Tag**: `SlotConflictChecker`
- **Base Route**: `/api/v1/slotConflictChecker`

| Method | Endpoint | Request Body | Response Data Model | Deskripsi |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/slotConflictChecker/check` | `SlotConflictCheckRequestDTO` | `SlotConflictCheckResponseDTO` | Pre-flight slot conflict detection & Friday prayer check. |

#### Contoh Response Slot Conflict Checker (Blocked Friday Prayer):
```json
{
  "success": true,
  "message": "Pengecekan konflik slot selesai",
  "data": {
    "is_available": false,
    "status": "BLOCKED_FRIDAY_PRAYER",
    "conflict_reason": "Waktu wawancara bentrok dengan periode Sholat Jumat (11:30 - 13:00 WIB)"
  }
}
```

---

### 4.16. Immutable Audit Logs (`AuditLogController`)
- **Tag**: `AuditLogs`
- **Base Route**: `/api/v1/auditLogs`

| Method | Endpoint | Request Body | Response Data Model | Deskripsi |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/auditLogs` | None (Query pagination) | `PaginatedResponse[AuditEventDTO]` | Mengambil log jejak audit immutable dengan chain hash SHA-256. |
