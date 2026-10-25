# Backend Testing & Quality Assurance Guide

Dokumen ini memandu tata cara pengujian otomatis (automated testing) dan penegakan kualitas kode pada backend **Heketon**.

---

## 1. Arsitektur & Suite Pengujian

Suite pengujian backend menggunakan kombinasi **Pytest**, **pytest-asyncio**, **AnyIO**, dan **HTTPX** (`AsyncClient`). Seluruh 36 skenario pengujian telah diuji dan memiliki tingkat kelulusan **100%**.

### Struktur Direktori Pengujian:
```
backend/tests/
├── conftest.py                     # Setup fixture AsyncClient & disposal koneksi database
├── test_health.py                  # Pengujian endpoint root /health
├── unit/                           # Pengujian komponen terisolasi tanpa interaksi IO eksternal
│   ├── test_dtos.py                # Serialisasi DTO, casting tipe data, & camelCase mapping
│   ├── test_calendar_rules.py      # Validasi aturan jam kerja, cuti bersama, & Sholat Jumat
│   ├── test_exception_handlers.py  # Standarisasi format error JSON global
│   └── test_pagination.py          # Logika paginasi, offset, limit, & total_pages
└── integration/                    # Pengujian fungsional menyeluruh ke database & router
    └── test_api_endpoints.py       # Pengujian 14 skenario endpoint di 16 domain controller
```

---

## 2. Siklus Hidup Fixture Database Asynchronous (`conftest.py`)

Koneksi database asynchronous diuji secara realistis menggunakan database PostgreSQL. Untuk mencegah error `RuntimeError: Event loop is closed` saat pytest berpindah antar-task async, [`conftest.py`](file:///D:/Project/Heketon/backend/tests/conftest.py) mengimplementasikan fixture autouse `cleanup_db_engine`:

```python
@pytest.fixture(autouse=True)
async def cleanup_db_engine():
    yield
    await engine.dispose()
```

Fixture ini memastikan connection pool di-dispose secara bersih setiap kali suatu pengujian selesai, sehingga task berikutnya memperoleh koneksi baru dengan event loop yang masih aktif.

---

## 3. Best Practices Penulisan Test

### 3.1. Idempotensi Pengujian (Mencegah `UniqueViolationError`)
Ketika menulis integration test yang melakukan insert data ke database (seperti kandidat, contact/user, atau jadwal), hindari hardcode nilai unik seperti email atau NIK. Gunakan `uuid` dinamis agar pengujian dapat dijalankan berulang kali tanpa batas:

```python
suffix = uuid.uuid4().hex[:6]
payload = {
    "employee_id": f"EMP-ENG-{suffix}",
    "name": "Bambang Setiawan",
    "email": f"bambang.{suffix}@company.com",
    ...
}
```

### 3.2. Kesesuaian Check Constraint Database
Perhatikan nilai yang diizinkan pada check constraint model ORM:
- Status persetujuan: Gunakan `"AWAITING_APPROVAL"` untuk status pending approval di database.
- Status consent: Gunakan `"GRANTED"`, `"NOT_GRANTED"`, atau `"WITHDRAWN"`.
- Timezone: Gunakan `"WIB"`, `"WITA"`, atau `"WIT"`.

### 3.3. Pencegahan `MissingGreenlet` pada SQLAlchemy Async
Saat membaca relasi antar-entitas (misalnya `Interview -> SourceFile -> Job -> HrDecision`), pastikan repository memuat relasi tersebut secara eksplisit menggunakan `selectinload`:
```python
selectinload(Interview.source_files)
.selectinload(SourceFile.jobs)
.selectinload(Job.hr_decisions)
.selectinload(HrDecision.decided_by)
```
Di sisi service, gunakan `getattr(obj, "relation_name", None)` untuk keamanan bertingkat jika entitas dibuat di memori secara lokal.

---

## 4. Perintah Eksekusi Pengujian

Jalankan perintah pengujian dari direktori `backend/`:

```bash
# Menjalankan seluruh 36 test suite
uv run pytest

# Menjalankan pengujian dengan output detail (verbose)
uv run pytest -v

# Hanya menjalankan file integration test
uv run pytest tests/integration/test_api_endpoints.py

# Hanya menjalankan unit test DTO
uv run pytest tests/unit/test_dtos.py

# Menjalankan test berdasarkan kata kunci tertentu
uv run pytest -k "conflict"
uv run pytest -k "candidate"
```

---

## 5. Linter & Format Kode (Ruff)

Proyek ini menggunakan **Ruff** untuk memastikan format kode, pengurutan import, dan kebersihan sintaks.

### Konfigurasi Khusus CamelCase (`pyproject.toml`):
Agar Ruff tidak menganggap penamaan file CamelCase/PascalCase sebagai pelanggaran konvensi modul PEP 8, aturan `N999` diabaikan:

```toml
[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "C4"]
ignore = ["N999"]
```

### Perintah Linter:
```bash
# Memeriksa pelanggaran kode di seluruh backend
uv run ruff check .

# Memperbaiki pelanggaran yang dapat diotomatisasi secara otomatis (auto-fix)
uv run ruff check --fix .
```
Semua pengecekan linter saat ini berada dalam kondisi **0 error / All checks passed**.

---

## 6. Otomatisasi CI/CD (GitHub Actions)

Proyek ini menerapkan arsitektur dual-pipeline menggunakan GitHub Actions:

### 6.1. Pipeline Branch `backend-dev` (`.github/workflows/backend-ci.yml`)
Dioptimalkan untuk siklus umpan balik cepat (*fast feedback*):
- **Linting & Code Style**: `uv run ruff check .`
- **Security SAST Scanning**: Menjalankan Bandit untuk mendeteksi celah keamanan kode:
  ```bash
  uv run bandit -r app/ -ll -ii
  ```
- **Vulnerability Scanning**: Memeriksa kerentanan dependensi Python menggunakan pip-audit:
  ```bash
  uv run pip-audit --ignore-vuln CVE-2026-114603
  ```
- **Fast-Feedback Unit Tests**: Menjalankan seluruh pengujian unit tanpa dependensi database berat:
  ```bash
  uv run pytest tests/unit/ tests/test_health.py -v
  ```

### 6.2. Pipeline Branch `main` (`.github/workflows/main-ci.yml`)
Berfungsi sebagai *production release gate*:
- **PostgreSQL Service Container**: Menjalankan container `pgvector/pgvector:pg17` pada port 5432.
- **Validasi Migrasi Skema**: `uv run alembic upgrade head` memastikan migrasi skema berjalan sempurna.
- **Validasi Seeder**: `uv run python -m scripts.seed` memverifikasi data awal.
- **Full Test Suite**: `uv run pytest -v` (seluruh 36 pengujian unit & integrasi).
- **Frontend Lint & Build**: Menguji instalasi pnpm, ESLint (`pnpm lint`), dan build Next.js 16 (`pnpm build`).
- **Integration Gate**: Menandai commit/PR siap untuk deploy.

