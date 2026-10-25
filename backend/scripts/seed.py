import asyncio
from datetime import time

from sqlalchemy import select

from app.db.DatabaseSession import AsyncSessionLocal
from app.model.CalendarModel import WorkCalendar
from app.model.CandidateModel import Candidate
from app.model.RubricModel import Competency, Profile
from app.model.UserModel import User


async def seed_data() -> None:
    """Entrypoint for seeding initial development data."""
    async with AsyncSessionLocal() as session:
        print("Seeding initial database records...")

        # 1. Seed WorkCalendar
        existing_cal = (await session.execute(select(WorkCalendar).limit(1))).scalar_one_or_none()
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
            print(" - WorkCalendar seeded.")

        # 2. Seed User (Interviewer)
        existing_user = (await session.execute(select(User).limit(1))).scalar_one_or_none()
        if not existing_user:
            user = User(
                vuserid="EMP-ENG-001",
                vname="Budi Santoso",
                vusername="budi.santoso",
                vemail="budi.santoso@company.com",
                vpassword_hash="argon2_hashed_password",
                vphone_number="+6281211112222",
                vposition="VP of Engineering",
                vdepartment="Engineering",
                vrole="USER_INTERVIEWER",
                vtimezone="WIB",
                vworking_hours="09:00 - 17:00",
                vstatus="ACTIVE",
            )
            session.add(user)
            print(" - User (Budi Santoso) seeded.")

        # 3. Seed Candidate
        existing_cand = (await session.execute(select(Candidate).limit(1))).scalar_one_or_none()
        if not existing_cand:
            cand = Candidate(
                vcandidate_code="CAND-2026-001",
                vname="Rina Kusuma",
                vemail="rina.kusuma@example.com",
                vphone_number="+6281234567890",
                vpreferred_channel="whatsapp",
                vjob_position="Senior Frontend Engineer",
                vstatus="SCREENING",
                vtimezone="WIB",
                vresume_url="https://storage.smarthiring.ai/resumes/rina.pdf",
                vnotes="Top talent candidate with strong React & Next.js background.",
            )
            session.add(cand)
            print(" - Candidate (Rina Kusuma) seeded.")

        # 4. Seed Profile & Competency
        existing_profile = (await session.execute(select(Profile).limit(1))).scalar_one_or_none()
        if not existing_profile:
            profile = Profile(
                vcode="PROFILE-TECH-R1",
                vname="User Technical Interview (Round 1)",
                vversion_no="v1.0",
                vsummary_format={"format": "COMPETENCY_EVIDENCE_MAP"},
            )
            session.add(profile)
            await session.flush()

            comp1 = Competency(
                nid_profile=profile.nid,
                vvisibility_class="GENERAL",
                vcode="C1",
                vname="System Architecture & Scalability",
                nsort_order=1,
                vreference_question="Ceritakan pengalaman merancang sistem skalabel.",
            )
            comp2 = Competency(
                nid_profile=profile.nid,
                vvisibility_class="GENERAL",
                vcode="C2",
                vname="Problem Solving & Data Structures",
                nsort_order=2,
                vreference_question="Bagaimana pendekatan Anda mengatasi bottleneck kinerja?",
            )
            session.add_all([comp1, comp2])
            print(" - Rubric Profile & Competencies seeded.")

        await session.commit()
        print("Initial database records seeded successfully.")


if __name__ == "__main__":
    asyncio.run(seed_data())
