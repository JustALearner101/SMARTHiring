import asyncio
from datetime import time

from sqlalchemy import select

from app.core.AppSecurity import get_password_hash
from app.db.DatabaseSession import AsyncSessionLocal
from app.model.CalendarModel import WorkCalendar
from app.model.CandidateModel import Candidate
from app.model.RubricModel import Competency, Profile
from app.model.UserModel import Permission, User


async def seed_data() -> None:
    """Entrypoint for seeding comprehensive development data including Multi-Role & Permissions."""
    async with AsyncSessionLocal() as session:
        print("Memulai proses seeding database Heketon / SMARTHiring...")

        # -------------------------------------------------------------
        # 1. Seed WorkCalendar (Office Working Hours & Friday Blackout)
        # -------------------------------------------------------------
        existing_cal = (
            await session.execute(
                select(WorkCalendar).where(WorkCalendar.voffice_code == "JKT-HQ")
            )
        ).scalar_one_or_none()

        if not existing_cal:
            cal = WorkCalendar(
                voffice_code="JKT-HQ",
                vtimezone="WIB",
                twork_start=time(9, 0),
                twork_end=time(17, 0),
                tfriday_prayer_start=time(11, 30),
                tfriday_prayer_end=time(13, 0),
                nmax_negotiation_rounds=3,
                nbuffer_minutes=15,
                binjection_guardrail_enabled=True,
            )
            session.add(cal)
            print("  [WorkCalendar] Kebijakan operasional kantor JKT-HQ dibuat.")
        else:
            print("  [WorkCalendar] JKT-HQ sudah ada, melewati.")

        # -------------------------------------------------------------
        # 2. Seed Users (HR, Hiring Manager, dan Auditor)
        # -------------------------------------------------------------
        # Password default untuk demo lokal: "password123"
        default_password_hash = get_password_hash("password123")

        users_to_seed = [
            {
                "vuserid": "EMP-HR-001",
                "vname": "Siti Rahma (HR Lead)",
                "vusername": "hr.admin",
                "vemail": "siti.rahma@company.com",
                "vpassword_hash": default_password_hash,
                "vphone_number": "+628111222333",
                "vposition": "Talent Acquisition Manager",
                "vdepartment": "Human Resources",
                "vrole": "HR",
                "vtimezone": "WIB",
                "vworking_hours": "09:00 - 17:00",
                "vstatus": "ACTIVE",
            },
            {
                "vuserid": "EMP-ENG-001",
                "vname": "Budi Santoso",
                "vusername": "budi.santoso",
                "vemail": "budi.santoso@company.com",
                "vpassword_hash": default_password_hash,
                "vphone_number": "+6281211112222",
                "vposition": "VP of Engineering",
                "vdepartment": "Engineering",
                "vrole": "USER_INTERVIEWER",
                "vtimezone": "WIB",
                "vworking_hours": "09:00 - 17:00",
                "vstatus": "ACTIVE",
            },
            {
                "vuserid": "EMP-AUD-001",
                "vname": "Hendra Wijaya (Lead Auditor)",
                "vusername": "auditor.it",
                "vemail": "hendra.wijaya@company.com",
                "vpassword_hash": default_password_hash,
                "vphone_number": "+6281333334444",
                "vposition": "IT & AI Governance Auditor",
                "vdepartment": "Internal Audit",
                "vrole": "AUDITOR",
                "vtimezone": "WIB",
                "vworking_hours": "09:00 - 17:00",
                "vstatus": "ACTIVE",
            },
        ]

        for u in users_to_seed:
            existing = (
                await session.execute(
                    select(User).where(User.vusername == u["vusername"])
                )
            ).scalar_one_or_none()

            if not existing:
                session.add(User(**u))
                print(f"  [User] {u['vname']} ({u['vrole']}) berhasil didaftarkan.")
            else:
                existing.vpassword_hash = default_password_hash
                existing.vname = u["vname"]
                print(f"  [User] {u['vname']} sudah ada, kredensial disinkronkan.")

        # -------------------------------------------------------------
        # 3. Seed Permissions (Matriks Hak Akses per Kelas Data)
        # -------------------------------------------------------------
        permissions_matrix = [
            # HR: Akses penuh
            ("HR", "GENERAL", "WRITE"),
            ("HR", "HR_ONLY", "WRITE"),
            ("HR", "SALARY", "READ"),
            ("HR", "SENSITIVE_FLAG", "READ"),
            ("HR", "AUDIT_LOG", "READ"),

            # USER_INTERVIEWER (Hiring Manager): Terbatas umum, blokir gaji & sensitif
            ("USER_INTERVIEWER", "GENERAL", "READ"),
            ("USER_INTERVIEWER", "HR_ONLY", "NONE"),
            ("USER_INTERVIEWER", "SALARY", "NONE"),
            ("USER_INTERVIEWER", "SENSITIVE_FLAG", "NONE"),
            ("USER_INTERVIEWER", "AUDIT_LOG", "NONE"),

            # TECH_INTERVIEWER: Terbatas umum
            ("TECH_INTERVIEWER", "GENERAL", "READ"),
            ("TECH_INTERVIEWER", "HR_ONLY", "NONE"),
            ("TECH_INTERVIEWER", "SALARY", "NONE"),
            ("TECH_INTERVIEWER", "SENSITIVE_FLAG", "NONE"),
            ("TECH_INTERVIEWER", "AUDIT_LOG", "NONE"),

            # AUDITOR: Khusus inspeksi log dan evaluasi
            ("AUDITOR", "AUDIT_LOG", "READ"),
            ("AUDITOR", "GENERAL", "READ"),
            ("AUDITOR", "SENSITIVE_FLAG", "READ"),
            ("AUDITOR", "SALARY", "NONE"),
            ("AUDITOR", "HR_ONLY", "NONE"),
        ]

        for role, vis_class, level in permissions_matrix:
            perm_exists = (
                await session.execute(
                    select(Permission).where(
                        Permission.vrole == role,
                        Permission.vvisibility_class == vis_class,
                    )
                )
            ).scalar_one_or_none()

            if not perm_exists:
                session.add(
                    Permission(
                        vrole=role,
                        vvisibility_class=vis_class,
                        vaccess_level=level,
                    )
                )
            else:
                perm_exists.vaccess_level = level

        print("  [Permissions] Matriks hak akses (Role x Visibility Class) berhasil diselaraskan.")

        # -------------------------------------------------------------
        # 4. Seed Candidate (dengan Data Gaji Aktual & Ekspektasi)
        # -------------------------------------------------------------
        cand_code = "CAND-2026-001"
        existing_cand = (
            await session.execute(
                select(Candidate).where(Candidate.vcandidate_code == cand_code)
            )
        ).scalar_one_or_none()

        if not existing_cand:
            cand = Candidate(
                vcandidate_code=cand_code,
                vname="Rina Kusuma",
                vemail="rina.kusuma@example.com",
                vphone_number="+6281234567890",
                vpreferred_channel="whatsapp",
                vjob_position="Senior Frontend Engineer",
                vstatus="SCREENING",
                vtimezone="WIB",
                vresume_url="https://storage.smarthiring.ai/resumes/rina.pdf",
                vnotes="Top talent candidate with strong React & Next.js background.",
                ncurrent_salary=22_000_000,
                nexpected_salary=28_000_000,
            )
            session.add(cand)
            print("  [Candidate] Rina Kusuma dibuat lengkap dengan data ekspektasi gaji.")
        else:
            existing_cand.ncurrent_salary = 22_000_000
            existing_cand.nexpected_salary = 28_000_000
            print("  [Candidate] Rina Kusuma sudah ada, data gaji disinkronkan.")

        # -------------------------------------------------------------
        # 5. Seed Rubric Profiles & Competencies (HR & Technical Rounds)
        # -------------------------------------------------------------
        profiles_to_seed = [
            {
                "vcode": "PROFILE-HR-R1",
                "vname": "HR Screening & Culture Fit (Round 1)",
                "vversion_no": "v1.0",
                "vsummary_format": {"format": "COMPETENCY_EVIDENCE_MAP"},
                "competencies": [
                    {
                        "vvisibility_class": "GENERAL",
                        "vcode": "H1",
                        "vname": "Culture & Core Values Alignment",
                        "nsort_order": 1,
                        "vreference_question": "Bagaimana Anda menyikapi nilai transparansi dan kepemilikan (ownership) di lingkungan kerja sebelumnya?",
                    },
                    {
                        "vvisibility_class": "GENERAL",
                        "vcode": "H2",
                        "vname": "Career Motivation & Trajectory",
                        "nsort_order": 2,
                        "vreference_question": "Apa motivasi terbesar Anda melamar di posisi ini dan apa target profesional Anda dalam 2 tahun ke depan?",
                    },
                    {
                        "vvisibility_class": "GENERAL",
                        "vcode": "H3",
                        "vname": "Communication & Interpersonal Dynamics",
                        "nsort_order": 3,
                        "vreference_question": "Ceritakan situasi saat Anda harus bekerja sama dengan rekan tim yang memiliki gaya komunikasi bertolak belakang.",
                    },
                    {
                        "vvisibility_class": "SALARY",
                        "vcode": "H4",
                        "vname": "Compensation, Benefits & Notice Period",
                        "nsort_order": 4,
                        "vreference_question": "Berapa ekspektasi kompensasi total (take-home pay) dan berapa lama notice period yang diperlukan di kantor lama?",
                    },
                ],
            },
            {
                "vcode": "PROFILE-TECH-R1",
                "vname": "User Technical Interview (Round 1)",
                "vversion_no": "v1.0",
                "vsummary_format": {"format": "COMPETENCY_EVIDENCE_MAP"},
                "competencies": [
                    {
                        "vvisibility_class": "GENERAL",
                        "vcode": "C1",
                        "vname": "System Architecture & Scalability",
                        "nsort_order": 1,
                        "vreference_question": "Ceritakan pengalaman Anda merancang arsitektur sistem skala besar.",
                    },
                    {
                        "vvisibility_class": "GENERAL",
                        "vcode": "C2",
                        "vname": "Problem Solving & Data Structures",
                        "nsort_order": 2,
                        "vreference_question": "Bagaimana pendekatan Anda dalam mengatasi bottleneck kinerja aplikasi?",
                    },
                    {
                        "vvisibility_class": "GENERAL",
                        "vcode": "C3",
                        "vname": "Communication & Team Collaboration",
                        "nsort_order": 3,
                        "vreference_question": "Bagaimana Anda mengelola perbedaan pandangan teknis dengan anggota tim?",
                    },
                    {
                        "vvisibility_class": "SALARY",
                        "vcode": "C4",
                        "vname": "Salary & Compensation Expectations",
                        "nsort_order": 4,
                        "vreference_question": "Berapa ekspektasi kompensasi total dan berapa lama periode pemberitahuan (notice period)?",
                    },
                ],
            },
        ]

        for p_data in profiles_to_seed:
            existing_p = (
                await session.execute(
                    select(Profile).where(Profile.vcode == p_data["vcode"])
                )
            ).scalar_one_or_none()

            if not existing_p:
                existing_p = Profile(
                    vcode=p_data["vcode"],
                    vname=p_data["vname"],
                    vversion_no=p_data["version_no"] if "version_no" in p_data else p_data["vversion_no"],
                    vsummary_format=p_data["vsummary_format"],
                )
                session.add(existing_p)
                await session.flush()
                print(f"  [Rubric Profile] Profil {p_data['vcode']} dibuat.")
            else:
                existing_p.vname = p_data["vname"]
                print(f"  [Rubric Profile] Profil {p_data['vcode']} sudah ada.")

            for c_data in p_data["competencies"]:
                existing_comp = (
                    await session.execute(
                        select(Competency).where(
                            Competency.nid_profile == existing_p.nid,
                            Competency.vcode == c_data["vcode"],
                        )
                    )
                ).scalar_one_or_none()

                if not existing_comp:
                    session.add(
                        Competency(
                            nid_profile=existing_p.nid,
                            vvisibility_class=str(c_data["vvisibility_class"]),
                            vcode=str(c_data["vcode"]),
                            vname=str(c_data["vname"]),
                            nsort_order=int(c_data["nsort_order"]),
                            vreference_question=str(c_data["vreference_question"]),
                        )
                    )
                    print(f"  [Competency] {c_data['vcode']} - {c_data['vname']} ({c_data['vvisibility_class']}) ditambahkan.")
                else:
                    existing_comp.vvisibility_class = str(c_data["vvisibility_class"])
                    existing_comp.vname = str(c_data["vname"])
                    existing_comp.vreference_question = str(c_data["vreference_question"])

        # Simpan seluruh transaksi ke database
        await session.commit()
        print("\n Database berhasil diselaraskan dan siap untuk integrasi Multi-Role!")


if __name__ == "__main__":
    asyncio.run(seed_data())

