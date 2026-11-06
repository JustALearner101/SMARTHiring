import asyncio
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import select, text

from app.core.AppSecurity import get_password_hash
from app.db.DatabaseSession import AsyncSessionLocal
from app.model.CalendarModel import Holiday, WorkCalendar
from app.model.CandidateModel import Candidate
from app.model.InterviewModel import Interview, SourceFile
from app.model.JobModel import Job, TranscriptSegment
from app.model.OrchestrationModel import CalendarEvent, NegotiationThread, ThreadMessage
from app.model.RubricModel import Competency, Profile
from app.model.SummaryModel import HrDecision, SummaryEvidence, SummaryPoint
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
        ).scalars().first()

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
        # 2. Seed Users (HR, Hiring Managers including 2 Budis, and Auditor)
        # -------------------------------------------------------------
        default_password_hash = get_password_hash("password123")

        users_to_seed = [
            {
                "nid": 1,
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
                "nid": 10,
                "vuserid": "EMP-ENG-001",
                "vname": "Budi Santoso",
                "vusername": "budi.santoso",
                "vemail": "budi.santoso@company.com",
                "vpassword_hash": default_password_hash,
                "vphone_number": "+6281211112222",
                "vposition": "VP of Engineering",
                "vdepartment": "Engineering",
                "vrole": "INTERVIEWER",
                "vtimezone": "WIB",
                "vworking_hours": "09:00 - 17:00",
                "vstatus": "ACTIVE",
            },
            {
                "nid": 11,
                "vuserid": "EMP-FIN-002",
                "vname": "Budi Hartono",
                "vusername": "budi.hartono",
                "vemail": "budi.hartono@company.com",
                "vpassword_hash": default_password_hash,
                "vphone_number": "+6281299998888",
                "vposition": "VP of Finance",
                "vdepartment": "Finance",
                "vrole": "INTERVIEWER",
                "vtimezone": "WITA",
                "vworking_hours": "09:00 - 17:00",
                "vstatus": "ACTIVE",
            },
            {
                "nid": 4,
                "vuserid": "EMP-AUD-001",
                "vname": "Hendra Wijaya (System Admin)",
                "vusername": "auditor.it",
                "vemail": "hendra.wijaya@company.com",
                "vpassword_hash": default_password_hash,
                "vphone_number": "+6281333334444",
                "vposition": "IT & AI Governance Administrator",
                "vdepartment": "Internal Audit",
                "vrole": "ADMIN",
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
            ).scalars().first()

            if not existing:
                session.add(User(**u))
                print(f"  [User] {u['vname']} ({u['vrole']}) berhasil didaftarkan.")
            else:
                existing.vpassword_hash = default_password_hash
                existing.vname = u["vname"]
                existing.vrole = u["vrole"]
                existing.vposition = u["vposition"]
                existing.vdepartment = u["vdepartment"]
                existing.vtimezone = u["vtimezone"]
                print(f"  [User] {u['vname']} sudah ada, kredensial disinkronkan.")

        await session.flush()

        # -------------------------------------------------------------
        # 3. Seed Permissions (Matriks Hak Akses per Kelas Data)
        # -------------------------------------------------------------
        permissions_matrix = [
            # HR: Akses penuh operasional rekrutmen
            ("HR", "GENERAL", "WRITE"),
            ("HR", "HR_ONLY", "WRITE"),
            ("HR", "SALARY", "READ"),
            ("HR", "SENSITIVE_FLAG", "READ"),
            ("HR", "AUDIT_LOG", "NONE"),

            # INTERVIEWER: Terbatas umum, blokir gaji & sensitif
            ("INTERVIEWER", "GENERAL", "READ"),
            ("INTERVIEWER", "HR_ONLY", "NONE"),
            ("INTERVIEWER", "SALARY", "NONE"),
            ("INTERVIEWER", "SENSITIVE_FLAG", "NONE"),
            ("INTERVIEWER", "AUDIT_LOG", "NONE"),

            # ADMIN: Akses penuh seluruh modul & inspeksi audit log
            ("ADMIN", "AUDIT_LOG", "READ"),
            ("ADMIN", "GENERAL", "WRITE"),
            ("ADMIN", "HR_ONLY", "WRITE"),
            ("ADMIN", "SALARY", "READ"),
            ("ADMIN", "SENSITIVE_FLAG", "READ"),
        ]

        for role, vis_class, level in permissions_matrix:
            perm_exists = (
                await session.execute(
                    select(Permission).where(
                        Permission.vrole == role,
                        Permission.vvisibility_class == vis_class,
                    )
                )
            ).scalars().first()

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
        # 4. Seed Candidates (Deterministic ATS Profiles 1..12)
        # -------------------------------------------------------------
        candidates_to_seed = [
            {
                "nid": 1,
                "vcandidate_code": "CAND-2026-001",
                "vname": "Rina Kusuma",
                "vemail": "rina.kusuma@example.com",
                "vphone_number": "+6281234567890",
                "vpreferred_channel": "whatsapp",
                "vjob_position": "Senior Frontend Engineer",
                "vstatus": "SCREENING",
                "vtimezone": "WIB",
                "vresume_url": "https://storage.smarthiring.ai/resumes/rina.pdf",
                "vnotes": "Top talent candidate with strong React & Next.js background.",
                "ncurrent_salary": 22_000_000,
                "nexpected_salary": 28_000_000,
            },
            {
                "nid": 2,
                "vcandidate_code": "CAND-2026-002",
                "vname": "Siti Rahayu",
                "vemail": "siti.rahayu@example.com",
                "vphone_number": "+6281234567891",
                "vpreferred_channel": "whatsapp",
                "vjob_position": "Lead QA Engineer",
                "vstatus": "SCREENING",
                "vtimezone": "WIB",
                "vresume_url": "https://storage.smarthiring.ai/resumes/siti-rahayu.pdf",
                "vnotes": "QA Automation lead with Cypress, Playwright, and Pytest experience.",
                "ncurrent_salary": 20_000_000,
                "nexpected_salary": 26_000_000,
            },
            {
                "nid": 3,
                "vcandidate_code": "CAND-2026-003",
                "vname": "Siti Aminah",
                "vemail": "siti.aminah@example.com",
                "vphone_number": "+6281234567892",
                "vpreferred_channel": "email",
                "vjob_position": "Frontend Developer",
                "vstatus": "SCREENING",
                "vtimezone": "WIB",
                "vresume_url": "https://storage.smarthiring.ai/resumes/siti-aminah.pdf",
                "vnotes": "Vue.js & Tailwind CSS specialist with 3 years experience.",
                "ncurrent_salary": 14_000_000,
                "nexpected_salary": 18_000_000,
            },
            {
                "nid": 4,
                "vcandidate_code": "CAND-2026-004",
                "vname": "Budi Pratama",
                "vemail": "budi.pratama@example.com",
                "vphone_number": "+6281234567893",
                "vpreferred_channel": "whatsapp",
                "vjob_position": "DevOps Engineer",
                "vstatus": "SCREENING",
                "vtimezone": "WIB",
                "vresume_url": "https://storage.smarthiring.ai/resumes/budi-pratama.pdf",
                "vnotes": "Kubernetes, Terraform, and Tencent Cloud infrastructure engineer.",
                "ncurrent_salary": 24_000_000,
                "nexpected_salary": 30_000_000,
            },
            {
                "nid": 5,
                "vcandidate_code": "CAND-2026-005",
                "vname": "Dewi Lestari",
                "vemail": "dewi.lestari@example.com",
                "vphone_number": "+6281234567894",
                "vpreferred_channel": "email",
                "vjob_position": "Product Designer",
                "vstatus": "SCREENING",
                "vtimezone": "WITA",
                "vresume_url": "https://storage.smarthiring.ai/resumes/dewi.pdf",
                "vnotes": "UI/UX lead specializing in design systems and accessibility.",
                "ncurrent_salary": 19_000_000,
                "nexpected_salary": 25_000_000,
            },
            {
                "nid": 6,
                "vcandidate_code": "CAND-2026-006",
                "vname": "Fajar Nugraha",
                "vemail": "fajar.nugraha@example.com",
                "vphone_number": "+6281234567895",
                "vpreferred_channel": "whatsapp",
                "vjob_position": "Data Engineer",
                "vstatus": "SCREENING",
                "vtimezone": "WIT",
                "vresume_url": "https://storage.smarthiring.ai/resumes/fajar.pdf",
                "vnotes": "Big Data pipelines using Spark, Airflow, and PostgreSQL.",
                "ncurrent_salary": 21_000_000,
                "nexpected_salary": 27_000_000,
            },
            {
                "nid": 7,
                "vcandidate_code": "CAND-2026-007",
                "vname": "Maya Putri",
                "vemail": "maya.putri@example.com",
                "vphone_number": "+6281234567896",
                "vpreferred_channel": "whatsapp",
                "vjob_position": "Mobile Developer",
                "vstatus": "SCREENING",
                "vtimezone": "WIB",
                "vresume_url": "https://storage.smarthiring.ai/resumes/maya.pdf",
                "vnotes": "React Native and Flutter cross-platform developer.",
                "ncurrent_salary": 16_000_000,
                "nexpected_salary": 20_000_000,
            },
            {
                "nid": 8,
                "vcandidate_code": "CAND-2026-008",
                "vname": "Rizky Pratama",
                "vemail": "rizky.pratama@example.com",
                "vphone_number": "+6281234567897",
                "vpreferred_channel": "email",
                "vjob_position": "Security Analyst",
                "vstatus": "SCREENING",
                "vtimezone": "WIB",
                "vresume_url": "https://storage.smarthiring.ai/resumes/rizky.pdf",
                "vnotes": "AppSec and SOC analyst with CEH & CompTIA Security+.",
                "ncurrent_salary": 23_000_000,
                "nexpected_salary": 29_000_000,
            },
            {
                "nid": 9,
                "vcandidate_code": "CAND-2026-009",
                "vname": "Nadia Safitri",
                "vemail": "nadia.safitri@example.com",
                "vphone_number": "+6281234567898",
                "vpreferred_channel": "whatsapp",
                "vjob_position": "Scrum Master",
                "vstatus": "SCREENING",
                "vtimezone": "WIB",
                "vresume_url": "https://storage.smarthiring.ai/resumes/nadia.pdf",
                "vnotes": "Agile coach and certified Scrum Master (PSM II).",
                "ncurrent_salary": 20_000_000,
                "nexpected_salary": 25_000_000,
            },
            {
                "nid": 10,
                "vcandidate_code": "CAND-2026-010",
                "vname": "Bayu Setiawan",
                "vemail": "bayu.setiawan@example.com",
                "vphone_number": "+6281234567899",
                "vpreferred_channel": "email",
                "vjob_position": "Cloud Architect",
                "vstatus": "SCREENING",
                "vtimezone": "WITA",
                "vresume_url": "https://storage.smarthiring.ai/resumes/bayu.pdf",
                "vnotes": "Multi-cloud architecture specialist with FinOps focus.",
                "ncurrent_salary": 32_000_000,
                "nexpected_salary": 40_000_000,
            },
            {
                "nid": 11,
                "vcandidate_code": "CAND-2026-011",
                "vname": "Eko Prasetyo",
                "vemail": "eko.prasetyo@example.com",
                "vphone_number": "+6281234567800",
                "vpreferred_channel": "whatsapp",
                "vjob_position": "Site Reliability Engineer",
                "vstatus": "SCREENING",
                "vtimezone": "WIB",
                "vresume_url": "https://storage.smarthiring.ai/resumes/eko.pdf",
                "vnotes": "Observability and high-availability systems engineer.",
                "ncurrent_salary": 25_000_000,
                "nexpected_salary": 31_000_000,
            },
            {
                "nid": 12,
                "vcandidate_code": "CAND-2026-012",
                "vname": "Ahmad Fauzi",
                "vemail": "ahmad.fauzi@example.com",
                "vphone_number": "+6281987654321",
                "vpreferred_channel": "whatsapp",
                "vjob_position": "Backend Engineer",
                "vstatus": "SCREENING",
                "vtimezone": "WITA",
                "vresume_url": "https://storage.smarthiring.ai/resumes/ahmad.pdf",
                "vnotes": "Solid Python and FastAPI engineer with PostgreSQL experience.",
                "ncurrent_salary": 18_000_000,
                "nexpected_salary": 24_000_000,
            },
        ]

        for cand_dict in candidates_to_seed:
            existing_cand = (
                await session.execute(
                    select(Candidate).where(Candidate.vcandidate_code == cand_dict["vcandidate_code"])
                )
            ).scalars().first()

            if not existing_cand:
                session.add(Candidate(**cand_dict))
                print(f"  [Candidate] {cand_dict['vname']} ({cand_dict['vcandidate_code']}) dibuat.")
            else:
                existing_cand.vname = cand_dict["vname"]
                existing_cand.vemail = cand_dict["vemail"]
                existing_cand.vphone_number = cand_dict["vphone_number"]
                existing_cand.vjob_position = cand_dict["vjob_position"]
                existing_cand.vstatus = cand_dict["vstatus"]
                existing_cand.ncurrent_salary = cand_dict["ncurrent_salary"]
                existing_cand.nexpected_salary = cand_dict["nexpected_salary"]
                print(f"  [Candidate] {cand_dict['vname']} ({cand_dict['vcandidate_code']}) data disinkronkan.")

        # -------------------------------------------------------------
        # 5. Seed Rubric Profiles & Competencies (Scoped per User/Division)
        # -------------------------------------------------------------
        hr_owner = (await session.execute(select(User).where(User.vusername == "hr.admin"))).scalars().first()
        eng_owner = (await session.execute(select(User).where(User.vusername == "budi.santoso"))).scalars().first()
        fin_owner = (await session.execute(select(User).where(User.vusername == "budi.hartono"))).scalars().first()

        profiles_to_seed = [
            {
                "vcode": "PROFILE-HR-R1",
                "vname": "HR Screening & Culture Fit (Round 1)",
                "vversion_no": "v1.0",
                "vtarget_role": "HR",
                "vdepartment": "Human Resources",
                "nid_owner_user": hr_owner.nid if hr_owner else None,
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
                "vname": "Engineering Technical Interview (Round 1)",
                "vversion_no": "v1.0",
                "vtarget_role": "INTERVIEWER",
                "vdepartment": "Engineering",
                "nid_owner_user": eng_owner.nid if eng_owner else None,
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
                ],
            },
            {
                "vcode": "PROFILE-FIN-R1",
                "vname": "Finance & Corporate Governance Interview",
                "vversion_no": "v1.0",
                "vtarget_role": "INTERVIEWER",
                "vdepartment": "Finance",
                "nid_owner_user": fin_owner.nid if fin_owner else None,
                "vsummary_format": {"format": "COMPETENCY_EVIDENCE_MAP"},
                "competencies": [
                    {
                        "vvisibility_class": "GENERAL",
                        "vcode": "F1",
                        "vname": "Financial Modeling & Forecasting Accuracy",
                        "nsort_order": 1,
                        "vreference_question": "Bagaimana metode Anda memvalidasi asumsi proyeksi arus kas kuartalan saat volatilitas pasar tinggi?",
                    },
                    {
                        "vvisibility_class": "GENERAL",
                        "vcode": "F2",
                        "vname": "Internal Control & Audit Compliance (PSAK/IFRS)",
                        "nsort_order": 2,
                        "vreference_question": "Ceritakan pengalaman Anda menemukan dan menutup celah rekonsiliasi keuangan sebelum audit eksternal.",
                    },
                ],
            },
        ]

        for p_data in profiles_to_seed:
            existing_p = (
                await session.execute(
                    select(Profile).where(Profile.vcode == p_data["vcode"])
                )
            ).scalars().first()

            if not existing_p:
                existing_p = Profile(
                    vcode=p_data["vcode"],
                    vname=p_data["vname"],
                    vversion_no=p_data["vversion_no"],
                    vtarget_role=p_data["vtarget_role"],
                    vdepartment=p_data["vdepartment"],
                    nid_owner_user=p_data["nid_owner_user"],
                    vsummary_format=p_data["vsummary_format"],
                )
                session.add(existing_p)
                await session.flush()
                print(f"  [Rubric Profile] Profil {p_data['vcode']} dibuat.")
            else:
                existing_p.vname = p_data["vname"]
                existing_p.vtarget_role = p_data["vtarget_role"]
                existing_p.vdepartment = p_data["vdepartment"]
                existing_p.nid_owner_user = p_data["nid_owner_user"]
                print(f"  [Rubric Profile] Profil {p_data['vcode']} sudah ada.")

            for c_data in p_data["competencies"]:
                existing_comp = (
                    await session.execute(
                        select(Competency).where(
                            Competency.nid_profile == existing_p.nid,
                            Competency.vcode == c_data["vcode"],
                        )
                    )
                ).scalars().first()

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

        # -------------------------------------------------------------
        # 6. Seed Holidays
        # -------------------------------------------------------------
        holidays_to_seed = [
            {"dholiday_date": date(2026, 1, 1), "vname": "Tahun Baru 2026 Masehi", "vtype": "NATIONAL_HOLIDAY"},
            {"dholiday_date": date(2026, 1, 16), "vname": "Isra Mikraj Nabi Muhammad SAW", "vtype": "NATIONAL_HOLIDAY"},
            {"dholiday_date": date(2026, 2, 16), "vname": "Cuti Bersama Tahun Baru Imlek", "vtype": "COLLECTIVE_LEAVE"},
            {"dholiday_date": date(2026, 2, 17), "vname": "Tahun Baru Imlek 2577 Kongzili", "vtype": "NATIONAL_HOLIDAY"},
            {"dholiday_date": date(2026, 3, 20), "vname": "Cuti Bersama Hari Suci Nyepi", "vtype": "COLLECTIVE_LEAVE"},
            {"dholiday_date": date(2026, 3, 21), "vname": "Hari Suci Nyepi Tahun Baru Saka 1948", "vtype": "NATIONAL_HOLIDAY"},
            {"dholiday_date": date(2026, 3, 22), "vname": "Hari Raya Idul Fitri 1447 H", "vtype": "NATIONAL_HOLIDAY"},
            {"dholiday_date": date(2026, 3, 23), "vname": "Hari Raya Idul Fitri 1447 H", "vtype": "NATIONAL_HOLIDAY"},
            {"dholiday_date": date(2026, 3, 24), "vname": "Cuti Bersama Hari Raya Idul Fitri", "vtype": "COLLECTIVE_LEAVE"},
            {"dholiday_date": date(2026, 4, 3), "vname": "Wafat Yesus Kristus", "vtype": "NATIONAL_HOLIDAY"},
            {"dholiday_date": date(2026, 4, 5), "vname": "Hari Kebangkitan Yesus Kristus (Paskah)", "vtype": "NATIONAL_HOLIDAY"},
            {"dholiday_date": date(2026, 5, 1), "vname": "Hari Buruh Internasional", "vtype": "NATIONAL_HOLIDAY"},
            {"dholiday_date": date(2026, 5, 14), "vname": "Kenaikan Yesus Kristus", "vtype": "NATIONAL_HOLIDAY"},
            {"dholiday_date": date(2026, 5, 15), "vname": "Cuti Bersama Kenaikan Yesus Kristus", "vtype": "COLLECTIVE_LEAVE"},
            {"dholiday_date": date(2026, 5, 27), "vname": "Hari Raya Idul Adha 1447 H", "vtype": "NATIONAL_HOLIDAY"},
            {"dholiday_date": date(2026, 5, 28), "vname": "Cuti Bersama Hari Raya Idul Adha", "vtype": "COLLECTIVE_LEAVE"},
            {"dholiday_date": date(2026, 5, 31), "vname": "Hari Raya Waisak 2570 BE", "vtype": "NATIONAL_HOLIDAY"},
            {"dholiday_date": date(2026, 6, 1), "vname": "Hari Lahir Pancasila", "vtype": "NATIONAL_HOLIDAY"},
            {"dholiday_date": date(2026, 6, 16), "vname": "Tahun Baru Islam 1448 H", "vtype": "NATIONAL_HOLIDAY"},
            {"dholiday_date": date(2026, 8, 17), "vname": "Hari Kemerdekaan RI", "vtype": "NATIONAL_HOLIDAY"},
            {"dholiday_date": date(2026, 8, 25), "vname": "Maulid Nabi Muhammad SAW", "vtype": "NATIONAL_HOLIDAY"},
            {"dholiday_date": date(2026, 12, 24), "vname": "Cuti Bersama Hari Raya Natal", "vtype": "COLLECTIVE_LEAVE"},
            {"dholiday_date": date(2026, 12, 25), "vname": "Hari Raya Natal", "vtype": "NATIONAL_HOLIDAY"},
            {"dholiday_date": date(2026, 12, 26), "vname": "Cuti Bersama Natal", "vtype": "COLLECTIVE_LEAVE"},
        ]
        for h in holidays_to_seed:
            existing_h = (
                await session.execute(
                    select(Holiday).where(Holiday.dholiday_date == h["dholiday_date"])
                )
            ).scalars().first()
            if not existing_h:
                session.add(Holiday(**h))
                print(f"  [Holiday] {h['vname']} ({h['dholiday_date']}) ditambahkan.")

        # -------------------------------------------------------------
        # 7. Seed Initial CalendarEvent & NegotiationThread (for Budi Santoso & Rina)
        # -------------------------------------------------------------
        budi_user = (
            await session.execute(select(User).where(User.vusername == "budi.santoso"))
        ).scalars().first()
        rina_cand = (
            await session.execute(select(Candidate).where(Candidate.vcandidate_code == "CAND-2026-001"))
        ).scalars().first()

        if budi_user and rina_cand:
            # Seed deterministic weekday Calendar Events for Budi Santoso
            now = datetime.now(UTC)
            weekday_events = [
                (
                    "Weekly Engineering Sync",
                    datetime(2026, 11, 9, 6, 0, tzinfo=UTC),  # Monday 13:00 WIB
                    datetime(2026, 11, 9, 7, 0, tzinfo=UTC),  # Monday 14:00 WIB
                ),
                (
                    "Architecture Design Review",
                    datetime(2026, 11, 11, 3, 0, tzinfo=UTC),  # Wednesday 10:00 WIB
                    datetime(2026, 11, 11, 4, 0, tzinfo=UTC),  # Wednesday 11:00 WIB
                ),
            ]
            for ev_title, ev_start, ev_end in weekday_events:
                existing_ev = (
                    await session.execute(
                        select(CalendarEvent).where(
                            CalendarEvent.nid_user == budi_user.nid,
                            CalendarEvent.vtitle == ev_title,
                        )
                    )
                ).scalars().first()
                if not existing_ev:
                    session.add(
                        CalendarEvent(
                            nid_user=budi_user.nid,
                            vtitle=ev_title,
                            dscheduled_start_utc=ev_start,
                            dscheduled_end_utc=ev_end,
                            vevent_type="TEAM_MEETING",
                            vrule_code="[cal-budi-santoso:EMP-ENG-001:HQ-JKT]",
                        )
                    )
                    print(f"  [CalendarEvent] {ev_title} untuk Budi Santoso dibuat.")

            # Seed Negotiation Thread
            existing_thread = (
                await session.execute(
                    select(NegotiationThread).where(
                        NegotiationThread.nid_candidate == rina_cand.nid,
                        NegotiationThread.nid_interviewer == budi_user.nid,
                    )
                )
            ).scalars().first()

            if not existing_thread:
                th = NegotiationThread(
                    nid_candidate=rina_cand.nid,
                    nid_interviewer=budi_user.nid,
                    ncurrent_round=1,
                    nmax_rounds=3,
                    vstatus="NEGOTIATING",
                    ddeadline_at=now + timedelta(days=3),
                    dlast_activity_at=now,
                )
                session.add(th)
                await session.flush()

                # Add initial messages
                session.add(
                    ThreadMessage(
                        nid_thread=th.nid,
                        nround_number=1,
                        vsender_role="AI_ORCHESTRATOR",
                        vsender_name="SmartHiring AI Orchestrator",
                        vchannel="whatsapp",
                        vcontent="Halo Kak Rina Kusuma! Selamat, Anda lolos seleksi awal. Kami mengundang sesi interview teknis bersama Pak Budi Santoso via Google Meet. Apakah jadwal Rabu 10:00 WIB sesuai?",
                        vproposed_slot="Rabu, 10:00 WIB",
                        vsource_citation="[cal-budi-santoso:EMP-ENG-001:HQ-JKT]",
                    )
                )
                session.add(
                    ThreadMessage(
                        nid_thread=th.nid,
                        nround_number=1,
                        vsender_role="CANDIDATE",
                        vsender_name="Rina Kusuma",
                        vchannel="whatsapp",
                        vcontent="Halo kak! Maaf hari Rabu saya berhalangan karena ada presentasi. Kalau hari Kamis jam 14:00 WIB apakah memungkinkan?",
                        vproposed_slot="Kamis, 14:00 WIB",
                        bis_rejection=True,
                    )
                )
                print("  [NegotiationThread] Thread negosiasi awal Rina x Budi dibuat.")

            siti_cand = (
                await session.execute(select(Candidate).where(Candidate.vcandidate_code == "CAND-2026-002"))
            ).scalars().first()
            if budi_user and siti_cand:
                existing_th2 = (
                    await session.execute(
                        select(NegotiationThread).where(
                            NegotiationThread.nid_candidate == siti_cand.nid,
                            NegotiationThread.nid_interviewer == budi_user.nid,
                        )
                    )
                ).scalars().first()
                if not existing_th2:
                    th2 = NegotiationThread(
                        nid_candidate=siti_cand.nid,
                        nid_interviewer=budi_user.nid,
                        ncurrent_round=1,
                        nmax_rounds=3,
                        vstatus="NEGOTIATING",
                        ddeadline_at=now + timedelta(days=3),
                        dlast_activity_at=now,
                    )
                    session.add(th2)
                    await session.flush()
                    session.add(
                        ThreadMessage(
                            nid_thread=th2.nid,
                            nround_number=1,
                            vsender_role="AI_ORCHESTRATOR",
                            vsender_name="SmartHiring AI Orchestrator",
                            vchannel="whatsapp",
                            vcontent="Halo Kak Siti Rahayu! Kami mengundang Anda untuk sesi interview teknis QA Lead. Apakah jadwal Senin 10:00 WIB sesuai?",
                            vproposed_slot="Senin, 10:00 WIB",
                            vsource_citation="[cal-budi-santoso:EMP-ENG-001:HQ-JKT]",
                        )
                    )
                    print("  [NegotiationThread] Thread negosiasi Siti Rahayu x Budi Santoso dibuat.")

            budi_hartono = (
                await session.execute(select(User).where(User.vusername == "budi.hartono"))
            ).scalars().first()
            dewi_cand = (
                await session.execute(select(Candidate).where(Candidate.vcandidate_code == "CAND-2026-005"))
            ).scalars().first()
            if budi_hartono and dewi_cand:
                existing_th3 = (
                    await session.execute(
                        select(NegotiationThread).where(
                            NegotiationThread.nid_candidate == dewi_cand.nid,
                            NegotiationThread.nid_interviewer == budi_hartono.nid,
                        )
                    )
                ).scalars().first()
                if not existing_th3:
                    th3 = NegotiationThread(
                        nid_candidate=dewi_cand.nid,
                        nid_interviewer=budi_hartono.nid,
                        ncurrent_round=2,
                        nmax_rounds=3,
                        vstatus="NEGOTIATING",
                        ddeadline_at=now + timedelta(days=2),
                        dlast_activity_at=now,
                    )
                    session.add(th3)
                    await session.flush()
                    session.add(
                        ThreadMessage(
                            nid_thread=th3.nid,
                            nround_number=1,
                            vsender_role="AI_ORCHESTRATOR",
                            vsender_name="SmartHiring AI Orchestrator",
                            vchannel="email",
                            vcontent="Dear Dewi Lestari, we invite you to an interview with VP of Finance Budi Hartono on Tuesday at 11:00 WITA.",
                            vproposed_slot="Selasa, 11:00 WITA",
                            vsource_citation="[cal-budi-hartono:EMP-FIN-002:HQ-JKT]",
                        )
                    )
                    session.add(
                        ThreadMessage(
                            nid_thread=th3.nid,
                            nround_number=2,
                            vsender_role="CANDIDATE",
                            vsender_name="Dewi Lestari",
                            vchannel="email",
                            vcontent="Dear team, Tuesday 11:00 WITA works perfectly for me. Thank you!",
                            vproposed_slot="Selasa, 11:00 WITA",
                            bis_rejection=False,
                        )
                    )
                    print("  [NegotiationThread] Thread negosiasi Dewi Lestari x Budi Hartono dibuat.")

        # -------------------------------------------------------------
        # 8. Seed Sample Interview Session with Transcripts & Rubric Points
        # -------------------------------------------------------------
        tech_profile = (
            await session.execute(select(Profile).where(Profile.vcode == "PROFILE-TECH-R1"))
        ).scalars().first()

        if rina_cand and tech_profile:
            existing_interview = (
                await session.execute(
                    select(Interview).where(
                        Interview.nid_candidate == rina_cand.nid,
                        Interview.nid_profile == tech_profile.nid,
                    )
                )
            ).scalars().first()

            if not existing_interview:
                interview = Interview(
                    nid_candidate=rina_cand.nid,
                    nid_profile=tech_profile.nid,
                    nid_interviewer=budi_user.nid if budi_user else None,
                    vconsent_status="GRANTED",
                    dconsent_at=datetime.now(UTC),
                    vconsent_notice_version="v2.1",
                )
                session.add(interview)
                await session.flush()

                sf = SourceFile(
                    nid_interview=interview.nid,
                    vtype="AUDIO",
                    vurl="https://storage.smarthiring.ai/interviews/rec-rina-tech.mp3",
                    vduration="42:15",
                )
                session.add(sf)
                await session.flush()

                job = Job(
                    nid_source=sf.nid,
                    nstatus=10,  # COMPLETED
                )
                session.add(job)
                await session.flush()

                # Add transcript segments
                seg1 = TranscriptSegment(
                    nid_job=job.nid,
                    nsegment_no=1,
                    nstart_ms=12000,
                    nend_ms=28000,
                    vspeaker_label="INTERVIEWER",
                    vspeaker_type="INTERVIEWER",
                    vtext="Bisa ceritakan pengalaman Anda merancang microservices di skala jutaan pengguna aktif harian?",
                    fconfidence=0.98,
                )
                seg2 = TranscriptSegment(
                    nid_job=job.nid,
                    nsegment_no=2,
                    nstart_ms=30000,
                    nend_ms=75000,
                    vspeaker_label="CANDIDATE",
                    vspeaker_type="CANDIDATE",
                    vtext="Di perusahaan sebelumnya kami migrasi dari monolitik ke microservices menggunakan FastAPI dan Kafka. Kami memisahkan database per service dan mengoptimalkan caching dengan Redis sehingga latensi p99 turun drastis ke bawah 120ms.",
                    fconfidence=0.96,
                )
                session.add_all([seg1, seg2])
                await session.flush()

                # Link competency points
                c1 = (
                    await session.execute(
                        select(Competency).where(Competency.nid_profile == tech_profile.nid, Competency.vcode == "C1")
                    )
                ).scalars().first()
                if c1:
                    sp1 = SummaryPoint(
                        nid_competency=c1.nid,
                        nid_job=job.nid,
                        vcoverage_status="COVERED",
                        vverification_status="VERIFIED",
                        vcontent="Kandidat memiliki rekam jejak terbukti merancang arsitektur microservices berbasis event-driven (FastAPI + Kafka) dengan optimasi p99 latency di bawah 120ms.",
                    )
                    session.add(sp1)
                    await session.flush()

                    session.add(
                        SummaryEvidence(
                            nid_summary_point=sp1.nid,
                            nid_transcript=seg2.nid,
                            vquote="Di perusahaan sebelumnya kami migrasi dari monolitik ke microservices menggunakan FastAPI dan Kafka. Kami memisahkan database per service dan mengoptimalkan caching dengan Redis.",
                        )
                    )

                c2 = (
                    await session.execute(
                        select(Competency).where(Competency.nid_profile == tech_profile.nid, Competency.vcode == "C2")
                    )
                ).scalars().first()
                if c2:
                    sp2 = SummaryPoint(
                        nid_competency=c2.nid,
                        nid_job=job.nid,
                        vcoverage_status="COVERED",
                        vverification_status="VERIFIED",
                        vcontent="Kandidat mahir dalam database profiling, indexing PostgreSQL, serta caching Redis berkinerja tinggi.",
                    )
                    session.add(sp2)
                    await session.flush()

                    session.add(
                        SummaryEvidence(
                            nid_summary_point=sp2.nid,
                            nid_transcript=seg2.nid,
                            vquote="Kami memisahkan database per service dan mengoptimalkan caching dengan Redis sehingga latensi p99 turun drastis ke bawah 120ms.",
                        )
                    )

                c3 = (
                    await session.execute(
                        select(Competency).where(Competency.nid_profile == tech_profile.nid, Competency.vcode == "C3")
                    )
                ).scalars().first()
                if c3:
                    sp3 = SummaryPoint(
                        nid_competency=c3.nid,
                        nid_job=job.nid,
                        vcoverage_status="COVERED",
                        vverification_status="VERIFIED",
                        vcontent="Kandidat menunjukkan komunikasi yang jelas dan kemampuan artikulasi teknis yang lugas.",
                    )
                    session.add(sp3)
                    await session.flush()

                    session.add(
                        SummaryEvidence(
                            nid_summary_point=sp3.nid,
                            nid_transcript=seg2.nid,
                            vquote="Kami memisahkan database per service dan mengoptimalkan caching dengan Redis.",
                        )
                    )

                hr_user = (
                    await session.execute(select(User).where(User.vusername == "hr.admin"))
                ).scalars().first()
                if hr_user:
                    session.add(
                        HrDecision(
                            nid_job=job.nid,
                            vdecision="PROCEED",
                            vnote="Kandidat sangat menguasai arsitektur backend skala besar. Direkomendasikan untuk offering.",
                            nid_decided_by=hr_user.nid,
                            ddecided_at=datetime.now(UTC),
                        )
                    )
                print("  [Interview] Sesi wawancara komprehensif Rina Kusuma berhasil dibuat.")

        # -------------------------------------------------------------
        # 9. Seed 25 Hash-Chained Audit Logs (Pillar 5 RECORD)
        # -------------------------------------------------------------
        from app.service.AuditLogService import AuditLogService
        audit_svc = AuditLogService(session)
        audit_events = [
            ("POLICY_UPDATE", "SYSTEM", "ORCHESTRATOR", "Operational Rules Configured", "Working hours 09:00-17:00, Friday prayer blackout 11:30-13:00 WIB initialized."),
            ("HOLIDAY_SYNC", "SYSTEM", "ORCHESTRATOR", "National Holidays Synchronized", "24 Indonesian national holidays & cuti bersama loaded from SKB 3 Menteri."),
            ("SECURITY_INITIALIZATION", "ADMIN", "HUMAN", "RBAC Matrix Verified", "Permissions configured: HR (full recruitment), INTERVIEWER (salary-blind), ADMIN (audit-read)."),
            ("GUARDRAIL_SCAN", "AI_ORCHESTRATOR", "AGENT", "Prompt Injection Scanner Active", "Guardrail ruleset loaded: prompt injection scan enabled for all inputs."),
            ("CANDIDATE_ATS_SYNC", "HR_ADMIN", "HUMAN", "ATS Pipeline Synchronized", "12 candidate profiles registered into ATS database."),
            ("CALENDAR_SYNC", "SYSTEM", "ORCHESTRATOR", "Calendar Availability Cached", "Work calendars synced for Jakarta HQ and Regional branches."),
            ("TRIAGE_INITIATED", "AI_ORCHESTRATOR", "AGENT", "Scheduling Triage Started", "Candidate Rina Kusuma interview negotiation round 1 initialized."),
            ("SLOT_VERIFICATION", "AI_ORCHESTRATOR", "AGENT", "Slot Availability Verified", "Checked Wednesday 10:00 WIB against Budi Santoso schedule: no conflict."),
            ("SOURCE_CITED", "AI_ORCHESTRATOR", "AGENT", "Sources Provenance Verified", "Cited sources: [cal-budi-sync], [RULE_WORKING_HOURS], [RULE_FRIDAY_PRAYER]."),
            ("MESSAGE_DISPATCHED", "AI_ORCHESTRATOR", "AGENT", "Invitation Sent via WhatsApp", "Initial slot offer sent to candidate Rina Kusuma."),
            ("CANDIDATE_RESPONSE", "CANDIDATE", "HUMAN", "Reschedule Request Received", "Candidate requested move from Wednesday to Thursday 14:00 WIB."),
            ("CONFLICT_DETECTED", "AI_ORCHESTRATOR", "AGENT", "Blackout Verification", "Thursday 14:00 WIB checked: compliant with working hours."),
            ("TRIAGE_ROUND_2", "AI_ORCHESTRATOR", "AGENT", "Round 2 Proposal Prepared", "Updated draft plan generated for Thursday 14:00 WIB."),
            ("SECONDARY_VALIDATION", "SECONDARY_VALIDATOR", "AGENT", "Dual-Control Validation Passed", "Validated by secondary model: no rule violations."),
            ("APPROVAL_REQUESTED", "AI_ORCHESTRATOR", "AGENT", "Human Approval Gate Opened", "ActionPlan #1 submitted for HR approval (Two-Turn Gate)."),
            ("HIGH_IMPACT_FLAGGED", "AI_ORCHESTRATOR", "AGENT", "High Impact Confirmed", "External WhatsApp message flagged for mandatory human authorization."),
            ("APPROVAL_GRANTED", "HR_ADMIN", "HUMAN", "Action Plan Approved", "HR Lead Siti Rahma approved interview booking."),
            ("UNDO_BUFFER_OPENED", "AI_ORCHESTRATOR", "AGENT", "60-Second Undo Buffer Active", "Execution delayed by 60-second safety window."),
            ("UNDO_WINDOW_EXPIRED", "SYSTEM", "ORCHESTRATOR", "Undo Window Concluded", "60 seconds elapsed without user revocation."),
            ("CALENDAR_BOOKED", "AI_ORCHESTRATOR", "AGENT", "Calendar Event Finalized", "Interview booked in Budi Santoso official calendar."),
            ("EMAIL_DISPATCHED", "EMAIL_DISPATCHER", "ORCHESTRATOR", "Confirmation Email Sent", "ICS calendar invite delivered to interviewer and candidate."),
            ("WHATSAPP_DISPATCHED", "WHATSAPP_DISPATCHER", "ORCHESTRATOR", "WhatsApp Confirmation Delivered", "Final schedule confirmed to candidate via WhatsApp."),
            ("RUBRIC_EVALUATION", "INTERVIEWER", "HUMAN", "Interview Rubric Scored", "Budi Santoso scored technical competencies C1-C4."),
            ("HR_DECISION_RECORDED", "HR_ADMIN", "HUMAN", "Selection Decision Finalized", "HR decision PROCEED recorded for candidate Rina Kusuma."),
            ("AUDIT_CHAIN_VERIFIED", "AUDITOR", "HUMAN", "Chain of Custody Audit Completed", "Audit log hash-chain integrity verified with zero tampering detected."),
        ]
        for ev_type, actor, actor_type, title, desc in audit_events:
            await audit_svc.log_event(
                event_type=ev_type,
                actor=actor,
                actor_type=actor_type,
                title=title,
                description=desc,
                metadata={"seeded": True, "compliance_pillar": "Pillar 5 (RECORD)"},
            )
        print("  [AuditLog] 25 cryptographic hash-chained audit events seeded.")

        # Synchronize PostgreSQL identity / serial sequences to prevent unique constraint collisions
        sync_tables = [
            "tblm_candidate",
            "tblm_user",
            "tblt_negotiation_thread",
            "tblt_thread_message",
            "tblm_holiday",
            "tblt_audit_log",
            "tblm_profile",
            "tblm_competency",
            "tblt_calendar_event",
            "tblt_interview",
            "tblt_job",
            "tblt_source_file",
        ]
        for tbl in sync_tables:
            try:
                await session.execute(
                    text(
                        f"SELECT setval(pg_get_serial_sequence('{tbl}', 'nid'), COALESCE((SELECT MAX(nid) FROM {tbl}), 1));"
                    )
                )
            except Exception:
                pass
        print("  [Sequence] Serial sequence values synchronized with MAX(nid).")

        # Simpan seluruh transaksi ke database
        await session.commit()
        print("\nDatabase berhasil diselaraskan dan siap untuk integrasi Multi-Role & Agentic Workflow!")


if __name__ == "__main__":
    asyncio.run(seed_data())
