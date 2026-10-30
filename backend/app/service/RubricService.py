from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agent.InterviewAnalyzerGraph import run_interview_analyzer_pipeline
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
from app.model.CandidateModel import Candidate
from app.model.InterviewModel import Interview, SourceFile
from app.model.JobModel import Job
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

        cand = getattr(p, "candidate", None)
        return RubricProfileDTO(
            id=str(p.nid),
            code=p.vcode,
            round_name=p.vname,
            description=description,
            target_role="INTERVIEWER" if p.vtarget_role == "INTERVIEWER" else "HR",
            department=p.vdepartment,
            owner_user_id=str(p.nid_owner_user) if p.nid_owner_user else None,
            owner_name=p.owner.vname if getattr(p, "owner", None) else None,
            candidate_id=str(p.nid_candidate) if p.nid_candidate else None,
            candidate_name=cand.vname if cand else None,
            candidate_code=cand.vcandidate_code if cand else None,
            applied_position=cand.vjob_position if cand else None,
            competencies=competencies,
        )

    @staticmethod
    def _assert_can_mutate_profile(profile: Profile, current_user: User) -> None:
        if current_user.vrole == "ADMIN":
            return
        if current_user.vrole == "INTERVIEWER":
            if profile.nid_owner_user and profile.nid_owner_user != current_user.nid:
                raise ForbiddenException("Anda hanya diizinkan mengelola rubrik kompetensi milik Anda sendiri.")
            return
        if (
            current_user.vrole == "HR"
            and profile.nid_owner_user
            and profile.nid_owner_user != current_user.nid
            and profile.vtarget_role != "HR"
        ):
            raise ForbiddenException("Peran HR hanya dapat mengubah rubrik penilaian milik HR.")

    async def list_rubric_profiles(
        self,
        current_user: User | None = None,
        for_interviewer_id: str | None = None,
        candidate_id: str | None = None,
    ) -> list[RubricProfileDTO]:
        target_interviewer_nid = (
            int(for_interviewer_id)
            if for_interviewer_id and for_interviewer_id.isdigit()
            else None
        )
        target_candidate_nid = (
            int(candidate_id)
            if candidate_id and candidate_id.isdigit()
            else None
        )
        profiles = await self.rubric_repo.list_profiles_scoped(
            current_user=current_user,
            for_interviewer_id=target_interviewer_nid,
            candidate_id=target_candidate_nid,
        )
        return [self._to_profile_dto(p) for p in profiles]

    async def create_rubric_profile(
        self,
        dto: RubricProfileCreateDTO,
        current_user: User,
    ) -> RubricProfileDTO:
        cand_id = int(dto.candidate_id) if dto.candidate_id and dto.candidate_id.isdigit() else None
        cand: Candidate | None = None
        if cand_id:
            cand = (
                await self.session.execute(select(Candidate).where(Candidate.nid == cand_id))
            ).scalar_one_or_none()

        clean_code: str
        if dto.code and dto.code.strip():
            clean_code = dto.code.strip().upper()
        elif cand:
            clean_code = f"RUBRIC-{cand.vcandidate_code.replace(' ', '_').upper()}"
        else:
            clean_code = f"RUBRIC-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"

        existing = await self.rubric_repo.get_profile_by_code(clean_code)
        if existing:
            # If for the same candidate, return existing
            if cand_id and existing.nid_candidate == cand_id:
                return self._to_profile_dto(existing)
            raise ConflictException(f"Profil rubrik dengan kode '{clean_code}' sudah terdaftar.")

        if current_user.vrole == "INTERVIEWER":
            resolved_target_role = "INTERVIEWER"
            resolved_dept = dto.department or (cand.vjob_position if cand else current_user.vdepartment) or "Technical / Division"
        elif current_user.vrole == "HR":
            resolved_target_role = "HR"
            resolved_dept = dto.department or (cand.vjob_position if cand else current_user.vdepartment) or "Human Resources"
        else:
            resolved_target_role = dto.target_role or "HR"
            resolved_dept = dto.department or (cand.vjob_position if cand else current_user.vdepartment) or "General"

        round_title = (
            dto.round_name.strip()
            if dto.round_name and dto.round_name.strip()
            else (f"Interview Rubric - {cand.vname}" if cand else f"Assessment Rubric ({clean_code})")
        )

        profile = Profile(
            vcode=clean_code,
            vname=round_title,
            vversion_no="v1.0",
            vtarget_role=resolved_target_role,
            vdepartment=resolved_dept,
            nid_owner_user=current_user.nid,
            nid_candidate=cand_id,
            vsummary_format=(
                {"description": dto.description.strip()}
                if dto.description
                else {
                    "description": f"Rubrik penilaian spesifik untuk kandidat {cand.vname if cand else clean_code}",
                    "style": "evidence_matrix",
                }
            ),
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
            metadata={
                "profile_id": profile.nid,
                "code": clean_code,
                "target_role": resolved_target_role,
                "candidate_id": cand_id,
            },
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

    async def re_evaluate_rubric(
        self,
        profile_id: str,
        current_user: User,
    ) -> RubricProfileDTO:
        if not profile_id.isdigit():
            raise NotFoundException("Profil rubrik tidak ditemukan.")
        profile = await self.rubric_repo.get_profile_with_competencies(int(profile_id))
        if not profile:
            raise NotFoundException("Profil rubrik tidak ditemukan.")

        self._assert_can_mutate_profile(profile, current_user)

        # Look up interview session linked to this profile or candidate
        int_stmt = (
            select(Interview)
            .options(
                selectinload(Interview.source_files).selectinload(SourceFile.jobs),
                selectinload(Interview.candidate),
            )
            .where(
                or_(
                    Interview.nid_profile == profile.nid,
                    Interview.nid_candidate == profile.nid_candidate if profile.nid_candidate else False,
                )
            )
            .order_by(Interview.dcrea.desc())
        )
        interview = (await self.session.execute(int_stmt)).scalars().first()
        if not interview:
            raise NotFoundException(
                "Belum ada rekaman atau sesi wawancara untuk kandidat ini yang dapat dinilai ulang."
            )

        # Find latest Job with transcribed audio
        latest_job: Job | None = None
        source_file: SourceFile | None = None
        for sf in (interview.source_files or []):
            for j in (sf.jobs or []):
                if j.nstatus in (3, 4, 10):
                    latest_job = j
                    source_file = sf
                    break
            if latest_job:
                break

        if not latest_job:
            # Check any job
            for sf in (interview.source_files or []):
                if sf.jobs:
                    latest_job = sf.jobs[-1]
                    source_file = sf
                    break

        if not latest_job:
            raise NotFoundException(
                "Sesi wawancara belum memiliki transkrip hasil proses rekaman audio."
            )

        # Execute re-evaluation with analyzer pipeline
        await run_interview_analyzer_pipeline(
            session=self.session,
            interview_id=interview.nid,
            candidate_id=interview.nid_candidate,
            profile_id=profile.nid,
            consent_status=interview.vconsent_status,
            notes=f"Re-evaluated by {current_user.vname} ({current_user.vrole})",
            audio_url=source_file.vurl if source_file else None,
            audio_duration=source_file.vduration if source_file else None,
            job_id=latest_job.nid,
        )

        await self.audit_service.log_event(
            event_type="RUBRIC_RE_EVALUATED",
            actor=current_user.vname,
            actor_type="HUMAN",
            title=f"Rubric Re-Evaluated: {profile.vcode}",
            description=f"Rubrik penilaian '{profile.vname}' ({profile.vcode}) dinilai ulang dari transkrip wawancara oleh {current_user.vname}.",
            metadata={"profile_id": profile.nid, "interview_id": interview.nid, "job_id": latest_job.nid},
        )

        loaded = await self.rubric_repo.get_profile_with_competencies(profile.nid)
        return self._to_profile_dto(loaded or profile)

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
