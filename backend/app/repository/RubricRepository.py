from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.model.CandidateModel import Candidate
from app.model.RubricModel import Competency, Profile
from app.model.UserModel import User
from app.repository.BaseRepository import BaseRepository


class RubricRepository(BaseRepository[Profile]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Profile, session)

    def _base_profile_query(self):
        return (
            select(Profile)
            .options(
                selectinload(Profile.competencies),
                selectinload(Profile.owner),
                selectinload(Profile.candidate),
            )
            .order_by(
                func.coalesce(Profile.dmodi, Profile.dcrea).desc(),
                Profile.nid.asc(),
            )
        )

    async def list_profiles_with_competencies(self) -> Sequence[Profile]:
        result = await self.session.execute(self._base_profile_query())
        return result.scalars().all()

    async def list_profiles_scoped(
        self,
        current_user: User | None = None,
        for_interviewer_id: int | None = None,
        candidate_id: int | None = None,
    ) -> Sequence[Profile]:
        stmt = self._base_profile_query()

        if candidate_id is not None:
            stmt = stmt.where(Profile.nid_candidate == candidate_id)

        if for_interviewer_id is not None:
            owned_stmt = stmt.where(Profile.nid_owner_user == for_interviewer_id)
            owned_items = (await self.session.execute(owned_stmt)).scalars().all()
            if owned_items:
                return owned_items

            target_user = (
                await self.session.execute(select(User).where(User.nid == for_interviewer_id))
            ).scalar_one_or_none()
            fallback_role = "HR" if (target_user and target_user.vrole == "HR") else "INTERVIEWER"
            fallback_stmt = stmt.where(Profile.vtarget_role == fallback_role)
            return (await self.session.execute(fallback_stmt)).scalars().all()

        if current_user is not None:
            if current_user.vrole == "INTERVIEWER":
                stmt = stmt.where(Profile.nid_owner_user == current_user.nid)
            elif current_user.vrole == "HR":
                stmt = stmt.where(
                    or_(
                        Profile.nid_owner_user == current_user.nid,
                        Profile.vtarget_role == "HR",
                        Profile.nid_candidate.is_not(None),
                    )
                )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_or_create_candidate_profile(
        self,
        candidate_id: int,
        owner_user_id: int | None = None,
        target_role: str = "HR",
        department: str | None = None,
        round_name: str | None = None,
    ) -> Profile:
        stmt = (
            select(Profile)
            .options(
                selectinload(Profile.competencies),
                selectinload(Profile.owner),
                selectinload(Profile.candidate),
            )
            .where(Profile.nid_candidate == candidate_id)
        )
        if owner_user_id is not None:
            stmt = stmt.where(Profile.nid_owner_user == owner_user_id)

        existing = (await self.session.execute(stmt)).scalars().first()
        if existing:
            return existing

        cand = (
            await self.session.execute(select(Candidate).where(Candidate.nid == candidate_id))
        ).scalar_one_or_none()

        cand_name = cand.vname if cand else f"Candidate #{candidate_id}"
        cand_code = cand.vcandidate_code if cand else f"CAND-{candidate_id}"
        cand_dept = department or (cand.vjob_position if cand else "Human Resources")

        base_code = f"RUBRIC-{cand_code.replace(' ', '_').upper()}"
        code = base_code
        suffix = 1
        while await self.get_profile_by_code(code):
            code = f"{base_code}-{suffix}"
            suffix += 1

        profile = Profile(
            vcode=code,
            vname=round_name or f"Interview Evaluation - {cand_name}",
            vversion_no="v1.0",
            vtarget_role=target_role,
            vdepartment=cand_dept,
            nid_owner_user=owner_user_id,
            nid_candidate=candidate_id,
            vsummary_format={
                "description": f"Rubrik penilaian otomatis untuk kandidat {cand_name} ({cand_code})",
                "candidate_name": cand_name,
                "candidate_code": cand_code,
            },
            vcrea="SYSTEM",
        )
        self.session.add(profile)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile

    async def get_profile_with_competencies(self, profile_id: int) -> Profile | None:
        stmt = (
            select(Profile)
            .options(
                selectinload(Profile.competencies),
                selectinload(Profile.owner),
                selectinload(Profile.candidate),
            )
            .where(Profile.nid == profile_id)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_profile_by_code(self, code: str) -> Profile | None:
        stmt = (
            select(Profile)
            .options(
                selectinload(Profile.competencies),
                selectinload(Profile.owner),
                selectinload(Profile.candidate),
            )
            .where(Profile.vcode == code)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_competency(self, profile_id: int, competency_id: int) -> Competency | None:
        stmt = select(Competency).where(
            Competency.nid == competency_id,
            Competency.nid_profile == profile_id,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()
