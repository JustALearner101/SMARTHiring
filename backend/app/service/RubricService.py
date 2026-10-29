from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.RubricDTO import (
    CompetencyCreateDTO,
    CompetencyItemDTO,
    CompetencyUpdateDTO,
    RubricProfileCreateDTO,
    RubricProfileDTO,
)
from app.exception.CustomException import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.model.InterviewModel import Interview
from app.model.RubricModel import Competency, Profile
from app.model.SummaryModel import SummaryPoint
from app.model.UserModel import User
from app.repository.RubricRepository import RubricRepository
from app.service.AuditLogService import AuditLogService


class RubricService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.rubric_repo = RubricRepository(session)
        self.audit_service = AuditLogService(session)

    @staticmethod
    def _to_competency_dto(c: Competency) -> CompetencyItemDTO:
        return CompetencyItemDTO(
            id=str(c.nid),
            code=c.vcode,
            name=c.vname,
            description=c.vreference_question or f"Competency Assessment for {c.vname}",
            weight=25.0,
            target_score=4,
        )

    def _to_profile_dto(self, p: Profile) -> RubricProfileDTO:
        sorted_comps = sorted(p.competencies, key=lambda item: (item.nsort_order, item.nid))
        competencies = [self._to_competency_dto(c) for c in sorted_comps]
        custom_desc = (p.vsummary_format or {}).get("description") if isinstance(p.vsummary_format, dict) else None
        description = custom_desc or f"Standard Interview Round Questions for {p.vname} ({p.vversion_no})"
        return RubricProfileDTO(
            id=str(p.nid),
            code=p.vcode,
            round_name=p.vname,
            description=description,
            target_role="INTERVIEWER" if p.vtarget_role == "INTERVIEWER" else "HR",
            department=p.vdepartment,
            owner_user_id=str(p.nid_owner_user) if p.nid_owner_user else None,
            owner_name=p.owner.vname if getattr(p, "owner", None) else None,
            competencies=competencies,
        )

    @staticmethod
    def _assert_can_mutate_profile(profile: Profile, current_user: User) -> None:
        if current_user.vrole == "ADMIN":
            return
        if current_user.vrole == "INTERVIEWER":
            if profile.nid_owner_user != current_user.nid:
                raise ForbiddenException("Anda hanya diizinkan mengelola rubrik kompetensi milik Anda sendiri.")
            return
        if (
            current_user.vrole == "HR"
            and profile.nid_owner_user != current_user.nid
            and profile.vtarget_role != "HR"
        ):
            raise ForbiddenException("Peran HR hanya dapat mengubah rubrik penilaian milik HR.")

    async def list_rubric_profiles(
        self,
        current_user: User | None = None,
        for_interviewer_id: str | None = None,
    ) -> list[RubricProfileDTO]:
        target_interviewer_nid = (
            int(for_interviewer_id)
            if for_interviewer_id and for_interviewer_id.isdigit()
            else None
        )
        profiles = await self.rubric_repo.list_profiles_scoped(
            current_user=current_user,
            for_interviewer_id=target_interviewer_nid,
        )
        return [self._to_profile_dto(p) for p in profiles]

    async def create_rubric_profile(
        self,
        dto: RubricProfileCreateDTO,
        current_user: User,
    ) -> RubricProfileDTO:
        clean_code = dto.code.strip().upper()
        existing = await self.rubric_repo.get_profile_by_code(clean_code)
        if existing:
            raise ConflictException(f"Profil rubrik dengan kode '{clean_code}' sudah terdaftar.")

        if current_user.vrole == "INTERVIEWER":
            resolved_target_role = "INTERVIEWER"
            resolved_dept = dto.department or current_user.vdepartment or "Technical / Division"
        elif current_user.vrole == "HR":
            resolved_target_role = "HR"
            resolved_dept = dto.department or current_user.vdepartment or "Human Resources"
        else:
            resolved_target_role = dto.target_role or "HR"
            resolved_dept = dto.department or current_user.vdepartment or "General"

        profile = Profile(
            vcode=clean_code,
            vname=dto.round_name.strip(),
            vversion_no="v1.0",
            vtarget_role=resolved_target_role,
            vdepartment=resolved_dept,
            nid_owner_user=current_user.nid,
            vsummary_format={"description": dto.description.strip()} if dto.description else {"style": "evidence_matrix"},
            vcrea=current_user.vusername,
        )
        self.session.add(profile)
        await self.session.commit()

        await self.audit_service.log_event(
            event_type="RUBRIC_PROFILE_CREATED",
            actor=current_user.vname,
            actor_type="HUMAN",
            title=f"Rubric Profile Created: {clean_code}",
            description=f"Profil rubrik '{profile.vname}' ({clean_code}) dibuat oleh {current_user.vname} ({current_user.vrole}).",
            metadata={"profile_id": profile.nid, "code": clean_code, "target_role": resolved_target_role},
        )

        loaded = await self.rubric_repo.get_profile_with_competencies(profile.nid)
        return self._to_profile_dto(loaded or profile)

    async def delete_rubric_profile(
        self,
        profile_id: str,
        current_user: User,
    ) -> None:
        if not profile_id.isdigit():
            raise NotFoundException("Profil rubrik tidak ditemukan.")
        profile = await self.rubric_repo.get_profile_with_competencies(int(profile_id))
        if not profile:
            raise NotFoundException("Profil rubrik tidak ditemukan.")

        self._assert_can_mutate_profile(profile, current_user)

        linked_interviews = (
            await self.session.execute(
                select(func.count()).select_from(Interview).where(Interview.nid_profile == profile.nid)
            )
        ).scalar_one()
        if linked_interviews > 0:
            raise ConflictException(
                "Profil rubrik tidak dapat dihapus karena sudah tertaut dengan riwayat sesi wawancara."
            )

        code = profile.vcode
        name = profile.vname
        await self.session.delete(profile)
        await self.session.commit()

        await self.audit_service.log_event(
            event_type="RUBRIC_PROFILE_DELETED",
            actor=current_user.vname,
            actor_type="HUMAN",
            title=f"Rubric Profile Deleted: {code}",
            description=f"Profil rubrik '{name}' ({code}) dihapus oleh {current_user.vname}.",
            metadata={"profile_code": code},
        )

    async def add_competency(
        self,
        profile_id: str,
        dto: CompetencyCreateDTO,
        current_user: User,
    ) -> CompetencyItemDTO:
        if not profile_id.isdigit():
            raise NotFoundException("Profil rubrik tidak ditemukan.")
        profile = await self.rubric_repo.get_profile_with_competencies(int(profile_id))
        if not profile:
            raise NotFoundException("Profil rubrik tidak ditemukan.")

        self._assert_can_mutate_profile(profile, current_user)

        clean_code = dto.code.strip().upper()
        if any(c.vcode.upper() == clean_code for c in profile.competencies):
            raise ConflictException(f"Kode kompetensi '{clean_code}' sudah ada pada profil rubrik ini.")

        now = datetime.now(UTC)
        comp = Competency(
            nid_profile=profile.nid,
            vcode=clean_code,
            vname=dto.name.strip(),
            vreference_question=dto.description.strip(),
            vvisibility_class="HR_ONLY" if profile.vtarget_role == "HR" else "GENERAL",
            nsort_order=len(profile.competencies) + 1,
            vcrea=current_user.vusername,
        )
        profile.dmodi = now
        self.session.add(comp)
        self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(comp)
        return self._to_competency_dto(comp)

    async def update_competency(
        self,
        profile_id: str,
        competency_id: str,
        dto: CompetencyUpdateDTO,
        current_user: User,
    ) -> CompetencyItemDTO:
        if not profile_id.isdigit() or not competency_id.isdigit():
            raise NotFoundException("Indikator kompetensi tidak ditemukan.")
        profile = await self.rubric_repo.get_profile_with_competencies(int(profile_id))
        if not profile:
            raise NotFoundException("Profil rubrik tidak ditemukan.")

        self._assert_can_mutate_profile(profile, current_user)

        comp = await self.rubric_repo.get_competency(profile.nid, int(competency_id))
        if not comp:
            raise NotFoundException("Indikator kompetensi tidak ditemukan.")

        if dto.code is not None:
            clean_code = dto.code.strip().upper()
            if any(c.nid != comp.nid and c.vcode.upper() == clean_code for c in profile.competencies):
                raise ConflictException(f"Kode kompetensi '{clean_code}' sudah digunakan pada profil ini.")
            comp.vcode = clean_code
        if dto.name is not None:
            comp.vname = dto.name.strip()
        if dto.description is not None:
            comp.vreference_question = dto.description.strip()

        now = datetime.now(UTC)
        comp.dmodi = now
        comp.vmodi = current_user.vusername
        profile.dmodi = now
        self.session.add(comp)
        self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(comp)
        return self._to_competency_dto(comp)

    async def delete_competency(
        self,
        profile_id: str,
        competency_id: str,
        current_user: User,
    ) -> None:
        if not profile_id.isdigit() or not competency_id.isdigit():
            raise NotFoundException("Indikator kompetensi tidak ditemukan.")
        profile = await self.rubric_repo.get_profile_with_competencies(int(profile_id))
        if not profile:
            raise NotFoundException("Profil rubrik tidak ditemukan.")

        self._assert_can_mutate_profile(profile, current_user)

        comp = await self.rubric_repo.get_competency(profile.nid, int(competency_id))
        if not comp:
            raise NotFoundException("Indikator kompetensi tidak ditemukan.")

        used_count = (
            await self.session.execute(
                select(func.count()).select_from(SummaryPoint).where(SummaryPoint.nid_competency == comp.nid)
            )
        ).scalar_one()
        if used_count > 0:
            raise ConflictException(
                "Indikator kompetensi tidak dapat dihapus karena sudah memiliki bukti penilaian pada sesi wawancara historis."
            )

        profile.dmodi = datetime.now(UTC)
        self.session.add(profile)
        await self.session.delete(comp)
        await self.session.commit()
