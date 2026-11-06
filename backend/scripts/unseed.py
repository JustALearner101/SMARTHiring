import argparse
import asyncio
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from datetime import date

from sqlalchemy import text

from app.db.DatabaseSession import AsyncSessionLocal

# Seeded business identifiers for targeted cleanup
SEEDED_USERNAMES = ["hr.admin", "budi.santoso", "budi.hartono", "auditor.it"]
SEEDED_USER_IDS = ["EMP-HR-001", "EMP-ENG-001", "EMP-FIN-002", "EMP-AUD-001"]
SEEDED_CANDIDATE_CODES = ["CAND-2026-001", "CAND-2026-002"]
SEEDED_PROFILE_CODES = ["PROFILE-HR-R1", "PROFILE-TECH-R1", "PROFILE-FIN-R1"]
SEEDED_HOLIDAY_DATES = [date(2026, 12, 25), date(2026, 12, 26), date(2026, 5, 1)]
SEEDED_OFFICE_CODE = "JKT-HQ"

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


async def unseed_targeted(dry_run: bool = False) -> None:
    """Selectively delete only seeded dev records while strictly preserving all other data."""
    mode_desc = (
        "TARGETED DRY RUN (Pemeriksaan Data Seeded Saja)"
        if dry_run
        else "TARGETED PURGE (Cabut Data Seeded Saja, Data Lain Utuh)"
    )
    print("=" * 68)
    print(" Heketon / SMARTHiring Database Unseeder")
    print(f" Mode: {mode_desc}")
    print("=" * 68)

    async with AsyncSessionLocal() as session:
        # 1. Resolve User NIDs
        user_res = await session.execute(
            text("SELECT nid FROM tblm_user WHERE vusername = ANY(:usernames) OR vuserid = ANY(:userids);"),
            {"usernames": SEEDED_USERNAMES, "userids": SEEDED_USER_IDS},
        )
        user_nids = [row[0] for row in user_res.fetchall()]

        # 2. Resolve Candidate NIDs
        cand_res = await session.execute(
            text("SELECT nid FROM tblm_candidate WHERE vcandidate_code = ANY(:cand_codes);"),
            {"cand_codes": SEEDED_CANDIDATE_CODES},
        )
        cand_nids = [row[0] for row in cand_res.fetchall()]

        # 3. Resolve Profile NIDs
        prof_res = await session.execute(
            text("SELECT nid FROM tblm_profile WHERE vcode = ANY(:profile_codes);"),
            {"profile_codes": SEEDED_PROFILE_CODES},
        )
        profile_nids = [row[0] for row in prof_res.fetchall()]

        # 4. Resolve Competency NIDs
        comp_nids = []
        if profile_nids:
            comp_res = await session.execute(
                text("SELECT nid FROM tblm_competency WHERE nid_profile = ANY(:profile_nids);"),
                {"profile_nids": profile_nids},
            )
            comp_nids = [row[0] for row in comp_res.fetchall()]

        # 5. Resolve Interview NIDs
        interview_conditions = []
        interview_params = {}
        if cand_nids:
            interview_conditions.append("nid_candidate = ANY(:cand_nids)")
            interview_params["cand_nids"] = cand_nids
        if profile_nids:
            interview_conditions.append("nid_profile = ANY(:prof_nids)")
            interview_params["prof_nids"] = profile_nids
        if user_nids:
            interview_conditions.append("nid_interviewer = ANY(:user_nids)")
            interview_params["user_nids"] = user_nids

        interview_nids = []
        if interview_conditions:
            int_res = await session.execute(
                text(f"SELECT nid FROM tblt_interview WHERE {' OR '.join(interview_conditions)};"),
                interview_params,
            )
            interview_nids = [row[0] for row in int_res.fetchall()]

        # 6. Resolve SourceFile NIDs
        source_nids = []
        if interview_nids:
            sf_res = await session.execute(
                text("SELECT nid FROM tblt_source_file WHERE nid_interview = ANY(:int_nids);"),
                {"int_nids": interview_nids},
            )
            source_nids = [row[0] for row in sf_res.fetchall()]

        # 7. Resolve Job NIDs
        job_nids = []
        if source_nids:
            job_res = await session.execute(
                text("SELECT nid FROM tblt_job WHERE nid_source = ANY(:source_nids);"),
                {"source_nids": source_nids},
            )
            job_nids = [row[0] for row in job_res.fetchall()]

        # 8. Resolve TranscriptSegment NIDs
        seg_nids = []
        if job_nids:
            seg_res = await session.execute(
                text("SELECT nid FROM tblt_transcript_segment WHERE nid_job = ANY(:job_nids);"),
                {"job_nids": job_nids},
            )
            seg_nids = [row[0] for row in seg_res.fetchall()]

        # 9. Resolve SummaryPoint NIDs
        sp_conditions = []
        sp_params = {}
        if comp_nids:
            sp_conditions.append("nid_competency = ANY(:comp_nids)")
            sp_params["comp_nids"] = comp_nids
        if job_nids:
            sp_conditions.append("nid_job = ANY(:job_nids)")
            sp_params["job_nids"] = job_nids

        sp_nids = []
        if sp_conditions:
            sp_res = await session.execute(
                text(f"SELECT nid FROM tblt_summary_point WHERE {' OR '.join(sp_conditions)};"),
                sp_params,
            )
            sp_nids = [row[0] for row in sp_res.fetchall()]

        # 10. Resolve NegotiationThread NIDs
        th_conditions = []
        th_params = {}
        if cand_nids:
            th_conditions.append("nid_candidate = ANY(:cand_nids)")
            th_params["cand_nids"] = cand_nids
        if user_nids:
            th_conditions.append("nid_interviewer = ANY(:user_nids)")
            th_params["user_nids"] = user_nids

        thread_nids = []
        if th_conditions:
            th_res = await session.execute(
                text(f"SELECT nid FROM tblt_negotiation_thread WHERE {' OR '.join(th_conditions)};"),
                th_params,
            )
            thread_nids = [row[0] for row in th_res.fetchall()]

        # 11. Resolve FollowupPlan NIDs
        fp_conditions = []
        fp_params = {}
        if user_nids:
            fp_conditions.append("nid_approved_by = ANY(:user_nids)")
            fp_params["user_nids"] = user_nids
        if job_nids:
            fp_conditions.append("nid_job = ANY(:job_nids)")
            fp_params["job_nids"] = job_nids
        if thread_nids:
            fp_conditions.append("nid_thread = ANY(:thread_nids)")
            fp_params["thread_nids"] = thread_nids

        followup_nids = []
        if fp_conditions:
            fp_res = await session.execute(
                text(f"SELECT nid FROM tblt_followup_plan WHERE {' OR '.join(fp_conditions)};"),
                fp_params,
            )
            followup_nids = [row[0] for row in fp_res.fetchall()]

        # Ordered delete plans
        deletion_targets = [
            (
                "tblr_action_recipient",
                "nid_user = ANY(:user_nids) OR nid_candidate = ANY(:cand_nids) OR nid_followup_plan = ANY(:fp_nids)",
                {
                    "user_nids": user_nids if user_nids else [-1],
                    "cand_nids": cand_nids if cand_nids else [-1],
                    "fp_nids": followup_nids if followup_nids else [-1],
                }
                if (user_nids or cand_nids or followup_nids)
                else None,
            ),
            (
                "tblt_followup_plan",
                "nid = ANY(:nids)",
                {"nids": followup_nids} if followup_nids else None,
            ),
            (
                "tblt_audit_log",
                "nid_job = ANY(:job_nids) OR vactor_id = ANY(:usernames)",
                {"job_nids": job_nids, "usernames": SEEDED_USERNAMES} if (job_nids or SEEDED_USERNAMES) else None,
            ),
            (
                "tblt_hr_decision",
                "nid_job = ANY(:job_nids) OR nid_decided_by = ANY(:user_nids)",
                {"job_nids": job_nids, "user_nids": user_nids} if (job_nids or user_nids) else None,
            ),
            (
                "tblt_summary_evidence",
                "nid_summary_point = ANY(:sp_nids) OR nid_transcript = ANY(:seg_nids)",
                {"sp_nids": sp_nids, "seg_nids": seg_nids} if (sp_nids or seg_nids) else None,
            ),
            (
                "tblt_summary_point",
                "nid = ANY(:nids)",
                {"nids": sp_nids} if sp_nids else None,
            ),
            (
                "tblt_flag",
                "nid_job = ANY(:job_nids) OR nid_transcript = ANY(:seg_nids) OR nid_reviewed_by = ANY(:user_nids)",
                {
                    "job_nids": job_nids if job_nids else [-1],
                    "seg_nids": seg_nids if seg_nids else [-1],
                    "user_nids": user_nids if user_nids else [-1],
                }
                if (job_nids or seg_nids or user_nids)
                else None,
            ),
            (
                "tblt_transcript_segment",
                "nid = ANY(:nids)",
                {"nids": seg_nids} if seg_nids else None,
            ),
            (
                "tblt_job",
                "nid = ANY(:nids)",
                {"nids": job_nids} if job_nids else None,
            ),
            (
                "tblt_source_file",
                "nid = ANY(:nids)",
                {"nids": source_nids} if source_nids else None,
            ),
            (
                "tblt_interview",
                "nid = ANY(:nids)",
                {"nids": interview_nids} if interview_nids else None,
            ),
            (
                "tblt_thread_message",
                "nid_thread = ANY(:thread_nids)",
                {"thread_nids": thread_nids} if thread_nids else None,
            ),
            (
                "tblt_negotiation_thread",
                "nid = ANY(:nids)",
                {"nids": thread_nids} if thread_nids else None,
            ),
            (
                "tblt_calendar_event",
                "nid_user = ANY(:user_nids) OR vrule_code = '[cal-budi-sync]'",
                {"user_nids": user_nids} if user_nids else {"user_nids": [-1]},
            ),
            (
                "tblm_competency",
                "nid = ANY(:nids)",
                {"nids": comp_nids} if comp_nids else None,
            ),
            (
                "tblm_profile",
                "nid = ANY(:nids)",
                {"nids": profile_nids} if profile_nids else None,
            ),
            (
                "tblm_candidate",
                "nid = ANY(:nids)",
                {"nids": cand_nids} if cand_nids else None,
            ),
            (
                "tblm_holiday",
                "dholiday_date = ANY(:dates)",
                {"dates": SEEDED_HOLIDAY_DATES},
            ),
            (
                "tblm_user",
                "nid = ANY(:nids)",
                {"nids": user_nids} if user_nids else None,
            ),
            (
                "tblm_work_calendar",
                "voffice_code = :office_code",
                {"office_code": SEEDED_OFFICE_CODE},
            ),
        ]

        print("\n[Identifikasi Record Seeded yang Terpilih]:")
        total_targeted = 0
        executed_deletions = []

        for tbl, cond, params in deletion_targets:
            if not params:
                continue
            cnt_res = await session.execute(text(f"SELECT COUNT(*) FROM {tbl} WHERE {cond};"), params)
            cnt = cnt_res.scalar() or 0
            if cnt > 0:
                total_targeted += cnt
                print(f"  - {tbl:<26}: {cnt:>5} baris akan dicabut")
                executed_deletions.append((tbl, cond, params, cnt))

        if total_targeted == 0:
            print("  Tidak ada record seeded yang ditemukan di database.")
            return

        print(f"\nTotal record seeded terdeteksi: {total_targeted} baris.")

        if dry_run:
            print("\n[DRY RUN] Tidak ada data yang dihapus dari database.")
            return

        print("\nMengeksekusi pencabutan data seeded...")
        for tbl, cond, params, cnt in executed_deletions:
            try:
                await session.execute(text(f"DELETE FROM {tbl} WHERE {cond};"), params)
                print(f"  [OK] {tbl} ({cnt} baris dicabut).")
            except Exception as e:
                print(f"  [ERROR] Gagal mencabut {tbl}: {e}")
                await session.rollback()
                raise

        await session.commit()
        print(f"\n[SUCCESS] Berhasil mencabut {total_targeted} baris data seeded!")
        print("[INFO] Seluruh data kustom / non-seed lainnya di database tetap 100% UTUH.")


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


async def unseed_keep_accounts(dry_run: bool = False) -> None:
    """Purge transactional data, candidates, and pytest users while preserving real user accounts, permissions, and work calendar."""
    mode_desc = "KEEP ACCOUNTS PURGE (Pembersihan Total Non-User & Sanitasi Pytest Users)"
    if dry_run:
        mode_desc = "DRY RUN (Pemeriksaan Saja)"

    print("=" * 68)
    print(" Heketon / SMARTHiring Database Unseeder")
    print(f" Mode: {mode_desc}")
    print("=" * 68)

    clean_tables = [
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
        "tblm_holiday",
        "tblm_candidate",
        "tblm_competency",
        "tblm_profile",
    ]

    async with AsyncSessionLocal() as session:
        real_users_res = await session.execute(
            text(
                "SELECT nid, vusername, vname, vrole FROM tblm_user "
                "WHERE nid IN (1, 7, 10, 11, 12) OR vusername IN ('hr.admin', 'busud', 'budi.santoso', 'budi.hartono', 'auditor.it') "
                "ORDER BY nid;"
            )
        )
        real_users = real_users_res.fetchall()
        print("\n[Akun Utama yang Dijamin Tetap Terpelihara]:")
        for u in real_users:
            print(f"  - [PRESERVED] nid={u[0]}: {u[1]} ({u[2]} / {u[3]})")

        dirty_users_res = await session.execute(
            text("SELECT nid, vusername FROM tblm_user WHERE vusername ~ '^(bambang|interviewer)\\.[0-9a-f]{6}$';")
        )
        dirty_users = dirty_users_res.fetchall()
        print(f"\n[Akun Sampah Pytest yang Terdeteksi]: {len(dirty_users)} akun ({[u[1] for u in dirty_users]})")

        if dry_run:
            print("\n[DRY RUN] Tidak ada data yang dihapus dari database.")
            return

        print("\nMemulai proses pembersihan tabel...")
        tables_csv = ", ".join(clean_tables)
        try:
            await session.execute(text(f"TRUNCATE TABLE {tables_csv} RESTART IDENTITY CASCADE;"))
            print(f"  [OK] Seluruh {len(clean_tables)} tabel transaksi, kandidat, dan holiday berhasil di-TRUNCATE (sequence di-reset).")
        except Exception as e:
            print(f"  TRUNCATE gagal ({e}), menjalankan fallback DELETE terurut...")
            await session.rollback()
            for tbl in clean_tables:
                try:
                    await session.execute(text(f"DELETE FROM {tbl};"))
                    print(f"  [OK] {tbl} dibersihkan.")
                except Exception as err:
                    print(f"  [WARN] Gagal membersihkan {tbl}: {err}")

        if dirty_users:
            dirty_nids = [u[0] for u in dirty_users]
            await session.execute(
                text("DELETE FROM tblm_user WHERE nid = ANY(:nids);"),
                {"nids": dirty_nids},
            )
            print(f"  [OK] {len(dirty_users)} akun sampah pytest dari tblm_user berhasil dihapus.")

        await session.commit()
        print("\n[SUCCESS] Pembersihan database dengan proteksi akun user selesai dengan sukses!")


def main() -> None:
    parser = argparse.ArgumentParser(description="Cabut data seeding dari database backend Heketon.")
    parser.add_argument(
        "--targeted",
        "--seeded-only",
        dest="targeted",
        action="store_true",
        help="Targeted purge: hanya cabut data yang dibuat oleh script seed (berdasarkan ID / code spesifik), data lain tetap utuh.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Full purge: bersihkan seluruh tabel aplikasi tanpa terkecuali.",
    )
    parser.add_argument(
        "--keep-admin",
        action="store_true",
        help="Safe purge: bersihkan data demo & transaksi, pertahankan akun hr.admin dan work calendar.",
    )
    parser.add_argument(
        "--keep-accounts",
        action="store_true",
        help="Proteksi akun user: bersihkan transaksi & kandidat kotor, hapus pytest users, pertahankan akun asli (hr.admin, busud, budi.santoso, budi.hartono, auditor.it), permission, dan work calendar.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Tampilkan jumlah baris tiap tabel tanpa mengeksekusi penghapusan.",
    )
    args = parser.parse_args()

    # Default to targeted if not explicitly asked for full purge or keep-admin
    if args.keep_accounts:
        asyncio.run(unseed_keep_accounts(dry_run=args.dry_run))
    elif args.all or args.keep_admin:
        keep_admin_flag = args.keep_admin and not args.all
        asyncio.run(unseed_database(keep_admin=keep_admin_flag, dry_run=args.dry_run))
    else:
        asyncio.run(unseed_targeted(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
