import asyncio
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import select

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
                "vuserid": "EMP-FIN-002",
                "vname": "Budi Hartono",
                "vusername": "budi.hartono",
                "vemail": "budi.hartono@company.com",
                "vpassword_hash": default_password_hash,
                "vphone_number": "+6281299998888",
                "vposition": "VP of Finance",
                "vdepartment": "Finance",
                "vrole": "USER_INTERVIEWER",
                "vtimezone": "WITA",
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
            ).scalars().first()

            if not existing:
                session.add(User(**u))
                print(f"  [User] {u['vname']} ({u['vrole']}) berhasil didaftarkan.")
            else:
                existing.vpassword_hash = default_password_hash
                existing.vname = u["vname"]
                existing.vposition = u["vposition"]
                existing.vdepartment = u["vdepartment"]
                existing.vtimezone = u["vtimezone"]
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

            # USER_INTERVIEWER: Terbatas umum, blokir gaji & sensitif
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
        # 4. Seed Candidates (Rina Kusuma & Ahmad Fauzi)
        # -------------------------------------------------------------
        candidates_to_seed = [
            {
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
                "vcandidate_code": "CAND-2026-002",
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
        # 5. Seed Rubric Profiles & Competencies
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
            ).scalars().first()

            if not existing_p:
                existing_p = Profile(
                    vcode=p_data["vcode"],
                    vname=p_data["vname"],
                    vversion_no=p_data["vversion_no"],
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
            {"dholiday_date": date(2026, 12, 25), "vname": "Hari Raya Natal", "vtype": "NATIONAL_HOLIDAY"},
            {"dholiday_date": date(2026, 12, 26), "vname": "Cuti Bersama Natal", "vtype": "COLLECTIVE_LEAVE"},
            {"dholiday_date": date(2026, 5, 1), "vname": "Hari Buruh Internasional", "vtype": "NATIONAL_HOLIDAY"},
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
            # Seed Calendar Event for Budi
            now = datetime.now(UTC)
            ev_start = now.replace(minute=0, second=0, microsecond=0) + timedelta(days=1, hours=1)
            ev_end = ev_start + timedelta(hours=1)
            existing_ev = (
                await session.execute(
                    select(CalendarEvent).where(
                        CalendarEvent.nid_user == budi_user.nid,
                        CalendarEvent.vtitle == "Weekly Engineering Sync",
                    )
                )
            ).scalars().first()
            if not existing_ev:
                session.add(
                    CalendarEvent(
                        nid_user=budi_user.nid,
                        vtitle="Weekly Engineering Sync",
                        dscheduled_start_utc=ev_start,
                        dscheduled_end_utc=ev_end,
                        vevent_type="TEAM_MEETING",
                        vrule_code="[cal-budi-sync]",
                    )
                )
                print("  [CalendarEvent] Weekly Engineering Sync untuk Budi Santoso dibuat.")

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
                        vsource_citation="[cal-budi-01]",
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

        # Simpan seluruh transaksi ke database
        await session.commit()
        print("\nDatabase berhasil diselaraskan dan siap untuk integrasi Multi-Role & Agentic Workflow!")


if __name__ == "__main__":
    asyncio.run(seed_data())
