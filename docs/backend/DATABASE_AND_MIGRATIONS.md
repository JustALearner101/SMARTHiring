# Backend Database & Migrations Guide

Dokumen ini menjelaskan arsitektur persistensi data, struktur skema relasional, dan tata cara migrasi skema database menggunakan **Alembic** pada backend **Heketon**.

---

## 1. Spesifikasi Mesin Database

- **RDBMS**: PostgreSQL 17
- **Ekstensi**: `pgvector` (untuk pencarian kemiripan semantik pada job profile dan evaluasi kandidat).
- **Driver Asynchronous**: `asyncpg` (`postgresql+asyncpg://...`) digunakan oleh FastAPI untuk seluruh query data bisnis.
- **Driver Synchronous**: `psycopg 3` (`postgresql://...`) digunakan secara eksklusif oleh checkpointer status state-graph LangGraph (`LANGGRAPH_CHECKPOINT_DB_URI`).

---

## 2. Model Dasar & Konvensi Skema (`BaseModel.py`)

Seluruh entitas ORM di `backend/app/model/` mewarisi model dasar yang didefinisikan di [`BaseModel.py`](file:///D:/Project/Heketon/backend/app/model/BaseModel.py):

### 2.1. Naming Convention Metadata
Untuk menjamin konsistensi constraint database lintas database engine, `Base.metadata.naming_convention` dikonfigurasi sebagai berikut:
- `ix`: `ix_%(column_0_label)s` (Index)
- `uq`: `uq_%(table_name)s_%(column_0_name)s` (Unique Constraint)
- `ck`: `ck_%(table_name)s_%(constraint_name)s` (Check Constraint)
- `fk`: `fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s` (Foreign Key)
- `pk`: `pk_%(table_name)s` (Primary Key)

### 2.2. Hirarki Kelas Model:
1. **`TableBaseModel`**:
   - Primary key integer auto-increment: `nid: Mapped[int]`
   - Timestamp penciptaan: `dcrea: Mapped[datetime]` (server default: `func.now()`)
   - Timestamp pembaruan: `dmod: Mapped[datetime]` (auto-update on modify)
   - Digunakan oleh tabel operasional (`tblm_user`, `tblm_candidate`, `tblm_work_calendar`, dll.).
2. **`AppendOnlyBaseModel`**:
   - Primary key integer: `nid: Mapped[int]`
   - Timestamp penciptaan: `dcrea: Mapped[datetime]`
   - **Tanpa kolom `dmod`** untuk memastikan integritas data append-only (audit logs, ledger riwayat pesan).
3. **`BaseModel`**:
   - Primary key UUID: `id: Mapped[uuid.UUID]`
   - Kolom timestamp: `created_at` dan `updated_at`.

---

## 3. Ringkasan Entitas & Relasi Domain

| Berkas Model | Nama Tabel Database | Fungsi & Integritas Data |
| :--- | :--- | :--- |
| [`UserModel.py`](file:///D:/Project/Heketon/backend/app/model/UserModel.py) | `tblm_user`, `tblm_permission` | Data user internal (HR, Interviewer), hashing password Argon2, dan role ACL. |
| [`CandidateModel.py`](file:///D:/Project/Heketon/backend/app/model/CandidateModel.py) | `tblm_candidate` | Profil pelamar dengan kode ATS unik (`vcandidate_code`), status lamaran, dan preferensi channel (whatsapp/email). |
| [`CalendarModel.py`](file:///D:/Project/Heketon/backend/app/model/CalendarModel.py) | `tblm_work_calendar`, `tblm_holiday` | Jam kerja default, waktu blackout sholat Jumat, dan kalender libur nasional / cuti bersama. |
| [`OrchestrationModel.py`](file:///D:/Project/Heketon/backend/app/model/OrchestrationModel.py) | `tblt_calendar_event`, `tblt_negotiation_thread`, `tblt_thread_message` | Sinkronisasi event kalender Google/Outlook, riwayat negosiasi jadwal kandidat, dan log percakapan. |
| [`FollowupModel.py`](file:///D:/Project/Heketon/backend/app/model/FollowupModel.py) | `tblt_followup_plan`, `tblt_action_recipient` | Rencana aksi interview yang dihasilkan AI dengan status approval dan token undo. |
| [`InterviewModel.py`](file:///D:/Project/Heketon/backend/app/model/InterviewModel.py) | `tblt_interview`, `tblt_source_file` | Sesi wawancara, persetujuan consent GDPR/PDP kandidat, dan URL rekaman audio. |
| [`JobModel.py`](file:///D:/Project/Heketon/backend/app/model/JobModel.py) | `tblt_job`, `tblt_transcript_segment` | Pipeline ASR / Speech-to-Text dan segmen transkripsi dengan confidence score. |
| [`RubricModel.py`](file:///D:/Project/Heketon/backend/app/model/RubricModel.py) | `tblm_profile`, `tblm_competency` | Profil evaluasi rubrik berbasis per kandidat (`nid_candidate` FK to `tblm_candidate.nid`) dan indikator kompetensi. |
| [`SummaryModel.py`](file:///D:/Project/Heketon/backend/app/model/SummaryModel.py) | `tblt_summary_point`, `tblt_summary_evidence`, `tblt_hr_decision`, `tblt_flag` | Poin ringkasan kompetensi dengan kutipan verbatim bukti transkrip dan keputusan mutlak HR. |
| [`AuditModel.py`](file:///D:/Project/Heketon/backend/app/model/AuditModel.py) | `tblt_audit_log`, `tblt_system_log` | Jejak audit SHA-256 hash-chained yang bersifat tamper-evident. |

---

## 4. Panduan Migrasi Database dengan Alembic

Alembic dikonfigurasi di `backend/alembic/` dan menggunakan koneksi asyncpg melalui helper `async_engine_from_config`.

### 4.1. Deteksi Model Otomatis
Agar Alembic dapat mendeteksi perubahan deklaratif model secara otomatis saat membuat migrasi, seluruh file model diimpor di [`backend/app/model/__init__.py`](file:///D:/Project/Heketon/backend/app/model/__init__.py) sebelum Alembic mengevaluasi `target_metadata = Base.metadata`.

### 4.2. Perintah Eksekusi Migrasi
Jalankan perintah ini dari direktori `backend/`:

```bash
# 1. Menghasilkan file migrasi baru berdasarkan perubahan model
uv run alembic revision --autogenerate -m "nama_deskripsi_migrasi"

# 2. Menerapkan seluruh migrasi yang belum terpasang ke database
uv run alembic upgrade head

# 3. Melihat riwayat migrasi saat ini
uv run alembic current

# 4. Melakukan rollback satu versi migrasi ke belakang jika diperlukan
uv run alembic downgrade -1
```

> [!NOTE]
> Versi migrasi skema saat ini adalah `00676c75559c` (`00676c75559c_add_candidate_to_profile.py`), yang menambahkan relasi per kandidat `nid_candidate` ke tabel `tblm_profile`.

---

## 5. Script Utilitas & Seeding Data

### 5.1. Verifikasi Database (`scripts/check_db.py`)
Memeriksa apakah instance PostgreSQL lokal aktif dan ekstensi `pgvector` telah terpasang dengan benar:
```bash
cd backend
uv run python -m scripts.check_db
```

### 5.2. Seeding Data Development (`scripts/seed.py`)
Mengisi data awal untuk kebutuhan demo dan pengujian lokal (interviewer Budi Santoso, kandidat Rina Kusuma, WorkCalendar 09:00 - 17:00, dan rubrik kompetensi):
```bash
cd backend
uv run python -m scripts.seed
```

### 5.3. Pencabutan & Pembersihan Data (`scripts/unseed.py`)
Mencabut / membersihkan seluruh data development dan transaksi dari database PostgreSQL:
```bash
cd backend
# 1. Full Purge: Bersihkan seluruh tabel aplikasi
uv run python -m scripts.unseed

# 2. Safe Purge: Bersihkan data demo transaksi, pertahankan akun hr.admin dan work calendar
uv run python -m scripts.unseed --keep-admin

# 3. Dry Run: Tampilkan jumlah baris tiap tabel tanpa menghapus
uv run python -m scripts.unseed --dry-run
```
