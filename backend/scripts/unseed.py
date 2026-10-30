import argparse
import asyncio
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from sqlalchemy import text

from app.db.DatabaseSession import AsyncSessionLocal

# Reverse topological order (leaf tables first, parent tables last)
TRANSACTIONAL_TABLES = [
    "tblr_action_recipient",
    "tblt_followup_plan",
    "tblt_hr_decision",
    "tblt_flag",
    "tblt_summary_evidence",
    "tblt_summary_point",
    "tblt_transcript_segment",
    "tblt_job",
    "tblt_source_file",
    "tblt_interview",
    "tblt_thread_message",
    "tblt_negotiation_thread",
    "tblt_calendar_event",
    "tblt_audit_log",
    "tbl_log_system",
]

MASTER_TABLES = [
    "tblm_holiday",
    "tblm_candidate",
    "tblm_competency",
    "tblm_profile",
    "tblm_permission",
    "tblm_user",
    "tblm_work_calendar",
]

ALL_TABLES = TRANSACTIONAL_TABLES + MASTER_TABLES


async def get_table_counts(tables: list[str]) -> dict[str, int]:
    """Inspect current row counts for the specified tables."""
    counts: dict[str, int] = {}
    async with AsyncSessionLocal() as session:
        for tbl in tables:
            try:
                res = await session.execute(text(f"SELECT COUNT(*) FROM {tbl};"))
                counts[tbl] = res.scalar() or 0
            except Exception:
                counts[tbl] = 0
    return counts


async def unseed_database(keep_admin: bool = False, dry_run: bool = False) -> None:
    """Purge seeded development and transactional records from the PostgreSQL database."""
    mode_desc = (
        "DRY RUN (Pemeriksaan Saja)"
        if dry_run
        else ("SAFE PURGE (Mempertahankan Akun Admin)" if keep_admin else "FULL PURGE (Cabut Seluruh Data)")
    )
    print("=" * 68)
    print(" Heketon / SMARTHiring Database Unseeder")
    print(f" Mode: {mode_desc}")
    print("=" * 68)

    counts_before = await get_table_counts(ALL_TABLES)

    print("\n[Status Database Sebelum Pencabutan]:")
    total_rows = 0
    for tbl in ALL_TABLES:
        cnt = counts_before.get(tbl, 0)
        total_rows += cnt
        marker = " [ADA DATA]" if cnt > 0 else ""
        print(f"  - {tbl:<26}: {cnt:>5} baris{marker}")

    print(f"\nTotal record terdeteksi di database: {total_rows} baris.")

    if dry_run:
        print("\n[DRY RUN] Tidak ada data yang dihapus dari database.")
        return

    if total_rows == 0:
        print("\nDatabase sudah bersih / kosong (0 baris). Tidak ada data yang perlu dicabut.")
        return

    print("\nMemulai proses pembersihan tabel...")

    async with AsyncSessionLocal() as session:
        if not keep_admin:
            # Full purge: use PostgreSQL TRUNCATE ... RESTART IDENTITY CASCADE for atomic & instant wipe
            all_tables_csv = ", ".join(ALL_TABLES)
            try:
                await session.execute(text(f"TRUNCATE TABLE {all_tables_csv} RESTART IDENTITY CASCADE;"))
                await session.commit()
                print("  [OK] Seluruh 22 tabel berhasil di-TRUNCATE dan sequence di-reset ke 1.")
            except Exception as e:
                # Fallback to ordered DELETE
                print(f"  TRUNCATE gagal ({e}), menjalankan fallback DELETE terurut...")
                await session.rollback()
                for tbl in ALL_TABLES:
                    try:
                        await session.execute(text(f"DELETE FROM {tbl};"))
                        print(f"  [OK] {tbl} dibersihkan.")
                    except Exception as err:
                        print(f"  [WARN] Gagal membersihkan {tbl}: {err}")
                await session.commit()
        else:
            # Safe purge: clean transactional & demo entities, keep hr.admin and work calendar
            safe_truncate = TRANSACTIONAL_TABLES + [
                "tblm_holiday",
                "tblm_candidate",
                "tblm_competency",
                "tblm_profile",
            ]
            safe_tables_csv = ", ".join(safe_truncate)
            try:
                await session.execute(text(f"TRUNCATE TABLE {safe_tables_csv} RESTART IDENTITY CASCADE;"))
                # Delete non-admin demo users, keep hr.admin
                await session.execute(text("DELETE FROM tblm_user WHERE vusername != 'hr.admin';"))
                await session.commit()
                print("  [OK] Data transaksi dan demo berhasil dibersihkan.")
                print("  [OK] Akun 'hr.admin' dan kebijakan 'WorkCalendar' tetap dipertahankan.")
            except Exception as e:
                print(f"  [WARN] Error saat safe purge: {e}")
                await session.rollback()

    # Re-verify counts after cleanup
    counts_after = await get_table_counts(ALL_TABLES)
    remaining_rows = sum(counts_after.values())
    print(f"\n[Verifikasi Akhir]: Sisa record di database: {remaining_rows} baris.")
    if remaining_rows == 0 or (keep_admin and remaining_rows <= 20):
        print("[SUCCESS] Seeding data di backend berhasil dicabut dengan bersih!")
    else:
        print("[NOTICE] Masih terdapat beberapa baris di tabel database.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Cabut data seeding dari database backend Heketon.")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Full purge: bersihkan seluruh tabel aplikasi tanpa terkecuali (default).",
    )
    parser.add_argument(
        "--keep-admin",
        action="store_true",
        help="Safe purge: bersihkan data demo & transaksi, pertahankan akun hr.admin dan work calendar.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Tampilkan jumlah baris tiap tabel tanpa mengeksekusi penghapusan.",
    )
    args = parser.parse_args()

    keep_admin_flag = args.keep_admin and not args.all

    asyncio.run(unseed_database(keep_admin=keep_admin_flag, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
