# Implementation Plan: UI Redesign (Who & Channels, Dynamic Dispatch Banner, Compact Live Audit Log)

## Ringkasan Masalah & Sasaran

Berdasarkan pengamatan pada dua tangkapan layar dan feedback pengguna, terdapat 3 permasalahan UI utama:

1. **Bagian WHO & CHANNELS Terlalu Sempit & Berantakan ("jelek banget kyk gitu")**:
   - Saat ini `WHO & CHANNELS` dipaksakan masuk ke dalam kolom 1 dari 4 di grid kartu informasi (`lg:grid-cols-4`).
   - Akibatnya, dua sub-kartu (Candidate dan Interviewer) sangat sempit (~170px), tombol toggle email/whatsapp terlipat (*crammed*), ikon email tampak terdistorsi/aneh, dan alamat email/nomor telepon terpotong (*truncated*).
   - **Solusi**: Memisahkan kartu `WHO & NOTIFICATION CHANNELS` menjadi area tersendiri dengan tata letak 2 kolom elegan (*Side-by-Side Recipient Cards*), avatar inisial profesional, badge status/peran yang jelas, dan *segmented pill toggle* yang luas dan responsif. Kartu meeting details (**WHAT**, **WHEN**, **WHERE**) ditata rapi dalam 3 kolom seimbang di atasnya.

2. **Teks Banner "DISPATCH_COMPLETE" Masih Hardcoded WhatsApp**:
   - Di [`page.tsx`](file:///D:/Project/Heketon/frontend/src/app/[locale]/(admin)/orchestration/scheduling/page.tsx), teks ringkasan setelah eksekusi masih hardcoded:
     `• WhatsApp sent to {activePlan?.candidate_name}`
     meskipun pengguna memilih mengirim via **Email (Corpo Default)**.
   - Audit trail title di frontend juga sempat hardcoded `"Email & WhatsApp Sent"`.
   - **Solusi**: Merender draf pengiriman secara dinamis berdasarkan properti `item.channel` aktual pada `activePlan.items`. Jika channel adalah `email`, tampilkan `• Email sent to ... (alamat@email) via Sumopod SMTP (SSL 465)`. Jika `whatsapp`, tampilkan `• WhatsApp sent to ... (+62...) via WhatsApp Gateway`. Tombol simulator juga diposisikan secara kontekstual sesuai channel aktif.

3. **Live Audit Log Terlalu Panjang Memanjang ke Bawah Tanpa Batas**:
   - Komponen [`AuditTimeline.tsx`](file:///D:/Project/Heketon/frontend/src/components/orchestration/AuditTimeline.tsx) saat ini tidak memiliki batasan tinggi (`max-height`). Dengan 50+ event audit, halaman meregang hingga lebih dari 5.000 piksel ke bawah.
   - **Solusi**: Menerapkan prinsip `/frontend-design`:
     - Membatasi container dengan ketinggian viewport yang proporsional (`max-h-[640px] xl:max-h-[720px]`) dengan scrollbar internal yang halus (*custom thin scrollbar*).
     - Menambahkan *sticky header* dengan *event count* dan **Quick Category Filter** (`All`, `Approvals`, `Dispatches`, `Guardrails`).
     - Tipografi dan *spacing* timeline yang lebih ringkas dan modern (*compact executive density*).
     - Tombol tautan di footer menuju halaman ledger lengkap (`/audit/logs`).

---

## Proposed Changes

### 1. Frontend: Redesign `ConfirmationCard.tsx`
**Path**: `frontend/src/components/orchestration/ConfirmationCard.tsx`

- **Restrukturisasi Grid**:
  - **Baris 1**: **Meeting Agenda & Logistics** (3 kolom seimbang: `WHAT (Session Agenda)`, `WHEN (Cross Timezone)`, `WHERE (Meeting Platform)`). Memberikan ruang bernapas yang lega untuk meeting link dan jam lintas WIB/WITA.
  - **Baris 2**: **Dedicated Notification & Channel Routing Section**:
    - Header: `Notification Channels & Participant Routing` dengan label status `Corporate Default: Email`.
    - Grid 2 Kolom Lebar (`grid grid-cols-1 md:grid-cols-2 gap-4`):
      - **Candidate Card**:
        - Avatar inisial dengan badge warna aksen.
        - Nama lengkap, role badge `Candidate`, dan posisi yang dilamar.
        - Segmented switch pill yang lebar dan nyaman diklik:
          `[ ✉️ Email (Corpo Default) ]  [ 💬 WhatsApp ]`
        - Preview handle kontak yang jelas:
          - Email: ikon amplop SVG bersih, alamat email asli (`belial110104@gmail.com`), badge `Sumopod SMTP (SSL 465)`.
          - WhatsApp: ikon chat, nomor telepon asli (`+628345678907`), badge `WhatsApp Gateway`.
      - **Interviewer Card**:
        - Avatar inisial pewawancara.
        - Nama lengkap, role badge `Interviewer / Host`, divisi `Engineering · VP of Engineering`.
        - Segmented switch pill yang lebar dan nyaman diklik:
          `[ ✉️ Email (Corpo Default) ]  [ 💬 WhatsApp ]`
        - Preview handle kontak yang jelas (`budi.santoso@company.com`).
- **Tab Preview Pesan**:
  - Tetap sinkron secara real-time dengan pilihan channel di kartu routing.

---

### 2. Frontend: Dynamic Dispatch Banner di `page.tsx`
**Path**: `frontend/src/app/[locale]/(admin)/orchestration/scheduling/page.tsx`

- Mengganti teks statis pada blok `STATUS === "EXECUTED"` (`DISPATCH_COMPLETE`):
  ```tsx
  {/* SEBELUMNYA (Hardcoded) */}
  • <strong>Email</strong> sent to {activePlan?.interviewer_name} ({activePlan?.items[0]?.recipient_contact})
  • <strong>WhatsApp</strong> sent to {activePlan?.candidate_name} ({activePlan?.items[1]?.recipient_contact})

  {/* SESUDAHNYA (Dinamis sesuai activePlan.items) */}
  {activePlan?.items?.filter(i => i.channel !== "calendar").map((item) => {
    const isEmail = item.channel === "email";
    return (
      <div key={item.id} className="flex items-center gap-2 mt-1">
        <span className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[11px] font-semibold ${
          isEmail ? "bg-brand-100 text-brand-800 dark:bg-brand-900/30 dark:text-brand-300" : "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300"
        }`}>
          {isEmail ? "✉️ Email" : "💬 WhatsApp"}
        </span>
        <span className="text-xs text-gray-700 dark:text-gray-300">
          sent to <strong>{item.recipient_name}</strong> ({item.recipient_contact}) via {isEmail ? "Sumopod SMTP (SSL 465)" : "WhatsApp Gateway"}
        </span>
      </div>
    );
  })}
  ```
- Memperbarui event log `ACTION_DISPATCHED` agar deskripsi teks audit mencerminkan channel aktual yang digunakan.
- Tombol simulator disesuaikan urutannya: jika candidate atau interviewer dikirim via Email, tombol *View in Email Simulator* ditonjolkan pertama.

---

### 3. Frontend: Redesign `AuditTimeline.tsx` (Prinsip `/frontend-design`)
**Path**: `frontend/src/components/orchestration/AuditTimeline.tsx`

- **Tinggi Terkendali (*Constrained Height*)**:
  - Membatasi tinggi container: `max-h-[640px] xl:max-h-[720px] flex flex-col`.
  - Area list event menggunakan `overflow-y-auto` dengan `scrollbar-thin` agar halaman utama tidak terdorong memanjang ke bawah.
- **Header Interaktif & Filter Cepat**:
  - Header tetap sticky di atas (`sticky top-0 z-10 bg-white/95 dark:bg-gray-900/95 backdrop-blur-xs`).
  - Dilengkapi filter tabs mini:
    `[ All (50) ]  [ Approvals ]  [ Dispatches ]  [ Guardrails ]`
    memudahkan navigasi HR untuk memeriksa peristiwa spesifik tanpa harus menelusuri puluhan log.
- **Card Micro-Design**:
  - Ikon status dengan warna yang lebih kontras dan semantik:
    - Hijau untuk `HUMAN_APPROVED`, `ACTION_DISPATCHED`, `ACTION_EXECUTED`.
    - Amber/Orange untuk `UNDO_BUFFER_STARTED`, `DISAMBIGUATION_TRIGGERED`.
    - Biru/Indigo untuk `PLAN_GENERATED`, `SOURCES_RETRIEVED`.
    - Merah untuk `ACTION_UNDONE`, `DEADLOCK_ESCALATED`.
  - Peringkasan hash / payload dan actor badge agar informasi padat namun mudah dibaca.
- **Footer**:
  - Tombol pintas `"View Full Hash Chain Ledger →"` menuju `/audit/logs`.

---

## Verification Plan

### Automated Tests
1. **Frontend Type Check**:
   ```powershell
   cd frontend
   pnpm tsc --noEmit
   ```
2. **Frontend Linter**:
   ```powershell
   cd frontend
   pnpm lint
   ```
3. **Backend Tests & Linters** (memastikan tidak ada regresi):
   ```powershell
   cd backend
   uv run ruff check .
   uv run pytest tests/unit/
   ```

### Manual / Browser Verification (via Playwright)
1. **Verifikasi Visual WHO & CHANNELS**:
   - Membuka `http://localhost:3000/orchestration/scheduling`.
   - Menjalankan perintah penjadwalan.
   - Memverifikasi tata letak 2 kolom kartu Candidate dan Interviewer: tidak ada teks terpotong, tombol toggle lapang dan responsif, alamat email/telepon tampil jelas.
2. **Verifikasi Dynamic Dispatch Banner (Email vs WhatsApp)**:
   - Memilih channel **Email (Corpo Default)** untuk kedua pihak.
   - Menyetujui plan dan menekan *Send Now*.
   - Memverifikasi banner `DISPATCH_COMPLETE` menampilkan label **Email** untuk Candidate dan Interviewer (bukan lagi hardcoded WhatsApp).
   - Mengulangi dengan salah satu pihak disetel ke **WhatsApp**, lalu memastikan banner menampilkan **WhatsApp** untuk pihak tersebut.
3. **Verifikasi Live Audit Log**:
   - Memverifikasi tinggi kolom kanan terkunci rapi (tidak lagi membuat halaman memanjang ke bawah).
   - Menguji filter kategori (*All*, *Approvals*, *Dispatches*, *Guardrails*).
   - Menguji scrollbar internal yang mulus.
