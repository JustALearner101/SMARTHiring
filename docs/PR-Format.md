# Pull Request Format Guide

Panduan format penulisan Pull Request untuk monorepo **Heketon**. Gunakan format ini agar setiap PR dapat direview, diuji ulang, dan diaudit tanpa perlu bertanya ke author.

---

## 1. Template Wajib

```markdown
## Summary

<1 paragraf: apa yang berubah dan kenapa. Sebutkan domain/komponen yang tersentuh.>

## Changes

### 1. <Tema perubahan pertama>
- <butir konkret, sebutkan path/berkas>

### 2. <Tema perubahan kedua>
- ...

## Breaking Changes

- <perubahan yang memaksa client/import lain ikut berubah, atau tulis "None">

## How to Test

```bash
<perintah copy-paste yang benar-benar dijalankan author>
```

Expected: <hasil yang diharapkan, mis. "36 passed">

## Checklist

- [ ] `ruff check .` bersih
- [ ] `pytest` hijau (unit + integration)
- [ ] Migrasi Alembic dapat dijalankan dari database kosong
- [ ] Dokumentasi terkait diperbarui
- [ ] Tidak ada kredensial/secret di diff
```

---

## 2. Aturan Penulisan per Section

| Section | Wajib berisi | Hindari |
| --- | --- | --- |
| **Summary** | Dampak bisnis/teknis + cakupan perubahan | Daftar file mentah, "update some files" |
| **Changes** | Dikelompokkan per tema, angka pasti (jumlah controller/test), path nyata | Klaim tanpa verifikasi ("100% coverage") |
| **Breaking Changes** | Tabel/pasangan `lama → baru` untuk rename, path route, atau signature | Menyembunyikan rename |
| **How to Test** | Perintah lengkap dari direktori yang jelas + expected output | Perintah yang butuh langkah rahasia di luar repo |
| **Checklist** | Status nyata, bukan aspirasi | Centang semua tanpa menjalankan |

### Aturan angka & klaim
- Setiap angka (jumlah test, jumlah endpoint, jumlah model) **harus berasal dari eksekusi nyata**, bukan perkiraan:
  - Jumlah test: `uv run pytest --collect-only -q`
  - Jumlah route: `grep -rc "@router\." backend/app/controller/*.py`
- Jangan menulis "100% coverage" kecuali ada laporan coverage (mis. `pytest --cov`) yang mendukung. Sebutkan cakupan secara eksplisit: "N test, mencakup seluruh M domain".
- Jangan pernah menyisakan komentar `<!-- TODO -->` di PR final.

### Aturan How to Test
- Tulis dari root repo, lalu `cd` ke direktori yang relevan — jangan asumsikan working directory reviewer.
- Sertakan prasyarat eksternal (PostgreSQL + pgvector, Node 20, pnpm 9) bila perintah membutuhkannya.
- Sertakan expected output singkat agar reviewer bisa membandingkan.

---

## 3. Konvensi Judul

```
<type>(<scope>): <ringkasan imperatif, huruf kecil>
```

- `type`: `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`
- `scope`: `backend`, `frontend`, `db`, `docs`, `ci`
- Contoh: `feat(backend): unify CamelCase architecture, add technical docs, and setup dual CI/CD workflows`

---

## 4. Referensi Cepat Perintah Verifikasi

```bash
# Backend
cd backend
uv sync
uv run ruff check .                              # lint
uv run pytest --collect-only -q | tail -1        # jumlah test
uv run pytest -v                                 # butuh PostgreSQL + pgvector
uv run bandit -r app/ -ll -ii                    # SAST
uv run pip-audit                                 # dependency audit

# Frontend
cd frontend
pnpm install --frozen-lockfile
pnpm lint
pnpm build
```

Prasyarat database lokal: PostgreSQL 17 + ekstensi `pgvector`, lalu `uv run alembic upgrade head` dan `uv run python -m scripts.seed`.
