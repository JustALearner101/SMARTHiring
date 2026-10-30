from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.BaseDTO import PaginatedResponse, PaginationParams
from app.dto.CandidateDTO import (
    CandidateCreateDTO,
    CandidateDTO,
    CandidateReapplyDTO,
    CandidateUpdateDTO,
)
from app.exception.CustomException import (
    BusinessRuleException,
    ConflictException,
    NotFoundException,
)
from app.model.CandidateModel import Candidate
from app.model.FollowupModel import ActionRecipient
from app.model.InterviewModel import Interview
from app.model.OrchestrationModel import NegotiationThread
from app.model.UserModel import User
from app.repository.CandidateRepository import CandidateRepository
from app.service.AuditLogService import AuditLogService


class CandidateService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.candidate_repo = CandidateRepository(session)
        self.audit_service = AuditLogService(session)

    @staticmethod
    def _to_candidate_dto(candidate: Candidate, current_user: User | None = None) -> CandidateDTO:
        can_view_salary = current_user is not None and current_user.vrole in ("HR", "ADMIN")
        prev_id = getattr(candidate, "nid_previous_application", None)
        return CandidateDTO(
            id=str(candidate.nid),
            candidate_code=candidate.vcandidate_code,
            name=candidate.vname,
            email=candidate.vemail,
            phone=candidate.vphone_number,
            preferred_channel=candidate.vpreferred_channel,  # type: ignore[arg-type]
            applied_position=candidate.vjob_position,
            status=candidate.vstatus,  # type: ignore[arg-type]
            timezone=candidate.vtimezone,  # type: ignore[arg-type]
            resume_url=candidate.vresume_url,
            notes=candidate.vnotes,
            current_salary=candidate.ncurrent_salary if can_view_salary else None,
            expected_salary=candidate.nexpected_salary if can_view_salary else None,
            application_cycle=getattr(candidate, "napplication_cycle", 1) or 1,
            previous_application_id=str(prev_id) if prev_id else None,
            created_at=candidate.dcrea.isoformat() if candidate.dcrea else datetime.now(UTC).isoformat(),
        )

    async def _generate_unique_code(self) -> str:
        seq = await self.candidate_repo.get_next_sequence_number()
        while True:
            code = f"CAND-2026-{seq:03d}"
            if not await self.candidate_repo.get_by_code(code):
                return code
            seq += 1

    async def list_candidates(
        self,
        query: str | None = None,
        status: str | None = None,
        params: PaginationParams | None = None,
        current_user: User | None = None,
    ) -> PaginatedResponse[CandidateDTO]:
        p = params or PaginationParams()
        items, total = await self.candidate_repo.search(
            query=query, status=status, offset=p.offset, limit=p.limit
        )
        return PaginatedResponse.create(
            items=[self._to_candidate_dto(c, current_user=current_user) for c in items],
            total=total,
            page=p.page,
            page_size=p.page_size,
        )

    async def get_candidate_by_id(
        self, candidate_id: str, current_user: User | None = None
    ) -> CandidateDTO | None:
        candidate = await self.candidate_repo.get_by_id(candidate_id)
        return self._to_candidate_dto(candidate, current_user=current_user) if candidate else None

    async def create_candidate(
        self, dto: CandidateCreateDTO, current_user: User | None = None
    ) -> CandidateDTO:
        prior_apps = await self.candidate_repo.list_by_email(dto.email)
        target_pos_norm = dto.applied_position.strip().lower()

        active_same_pos = next(
            (
                c
                for c in prior_apps
                if c.vjob_position.strip().lower() == target_pos_norm
                and c.vstatus not in ("REJECTED", "OFFERED")
            ),
            None,
        )
        if active_same_pos:
            raise ConflictException(
                f"Kandidat {dto.email} masih memiliki lamaran aktif ({active_same_pos.vcandidate_code} - "
                f"status {active_same_pos.vstatus}) untuk posisi {active_same_pos.vjob_position}."
            )

        latest_prior = prior_apps[0] if prior_apps else None
        next_cycle = (
            max((getattr(c, "napplication_cycle", 1) or 1) for c in prior_apps) + 1
            if prior_apps
            else 1
        )
        code = await self._generate_unique_code()

        candidate_data = {
            "vcandidate_code": code,
            "vname": dto.name,
            "vemail": dto.email,
            "vphone_number": dto.phone,
            "vpreferred_channel": dto.preferred_channel,
            "vjob_position": dto.applied_position,
            "vstatus": "SCREENING",
            "vtimezone": dto.timezone,
            "vresume_url": dto.resume_url,
            "vnotes": dto.notes,
            "ncurrent_salary": dto.current_salary,
            "nexpected_salary": dto.expected_salary,
            "napplication_cycle": next_cycle,
            "nid_previous_application": latest_prior.nid if latest_prior else None,
        }
        candidate = await self.candidate_repo.create(candidate_data)
        return self._to_candidate_dto(candidate, current_user=current_user)

    async def reapply_candidate(
        self,
        candidate_id: str,
        dto: CandidateReapplyDTO,
        current_user: User | None = None,
    ) -> CandidateDTO:
        prev = await self.candidate_repo.get_by_id(candidate_id)
        if not prev:
            raise NotFoundException("Kandidat tidak ditemukan")
        if prev.vstatus != "REJECTED":
            raise BusinessRuleException(
                f"Hanya kandidat berstatus REJECTED yang dapat diajukan ulang (status saat ini: {prev.vstatus})."
            )

        target_position = (dto.applied_position or prev.vjob_position).strip()
        prior_apps = await self.candidate_repo.list_by_email(prev.vemail)
        active_same_pos = next(
            (
                c
                for c in prior_apps
                if c.vjob_position.strip().lower() == target_position.lower()
                and c.vstatus not in ("REJECTED", "OFFERED")
            ),
            None,
        )
        if active_same_pos:
            raise ConflictException(
                f"Siklus lamaran baru ({active_same_pos.vcandidate_code}) untuk posisi {target_position} sudah aktif."
            )

        max_cycle = (
            max((getattr(c, "napplication_cycle", 1) or 1) for c in prior_apps)
            if prior_apps
            else 1
        )
        next_cycle = max_cycle + 1
        code = await self._generate_unique_code()
        reapply_note = (
            dto.notes
            or f"Re-application (Cycle #{next_cycle}) dari lamaran sebelumnya {prev.vcandidate_code}."
        )

        new_candidate = await self.candidate_repo.create(
            {
                "vcandidate_code": code,
                "vname": prev.vname,
                "vemail": prev.vemail,
                "vphone_number": prev.vphone_number,
                "vpreferred_channel": prev.vpreferred_channel,
                "vjob_position": target_position,
                "vstatus": "SCREENING",
                "vtimezone": prev.vtimezone,
                "vresume_url": prev.vresume_url,
                "vnotes": reapply_note,
                "ncurrent_salary": prev.ncurrent_salary,
                "nexpected_salary": (
                    dto.expected_salary if dto.expected_salary is not None else prev.nexpected_salary
                ),
                "napplication_cycle": next_cycle,
                "nid_previous_application": prev.nid,
            }
        )

        actor_name = current_user.vname if current_user else "HR Admin"
        await self.audit_service.log_event(
            event_type="CANDIDATE_REAPPLIED",
            actor=actor_name,
            actor_type="HUMAN",
            title=f"New Application Cycle #{next_cycle} ({code})",
            description=(
                f"Kandidat {prev.vname} mendaftar kembali untuk posisi {target_position} "
                f"(siklus baru {code}, merujuk riwayat {prev.vcandidate_code})."
            ),
            metadata={
                "new_candidate_id": new_candidate.nid,
                "previous_candidate_id": prev.nid,
                "application_cycle": next_cycle,
            },
        )
        return self._to_candidate_dto(new_candidate, current_user=current_user)

    async def update_candidate(
        self, candidate_id: str, dto: CandidateUpdateDTO, current_user: User | None = None
    ) -> CandidateDTO | None:
        candidate = await self.candidate_repo.get_by_id(candidate_id)
        if not candidate:
            return None
        updates = {}
        if dto.name is not None:
            updates["vname"] = dto.name
        if dto.email is not None:
            updates["vemail"] = dto.email
        if dto.phone is not None:
            updates["vphone_number"] = dto.phone
        if dto.preferred_channel is not None:
            updates["vpreferred_channel"] = dto.preferred_channel
        if dto.applied_position is not None:
            updates["vjob_position"] = dto.applied_position
        if dto.status is not None:
            updates["vstatus"] = dto.status
        if dto.timezone is not None:
            updates["vtimezone"] = dto.timezone
        if dto.resume_url is not None:
            updates["vresume_url"] = dto.resume_url
        if dto.notes is not None:
            updates["vnotes"] = dto.notes
        if dto.current_salary is not None:
            updates["ncurrent_salary"] = dto.current_salary
        if dto.expected_salary is not None:
            updates["nexpected_salary"] = dto.expected_salary

        updated = await self.candidate_repo.update(candidate, updates)
        return self._to_candidate_dto(updated, current_user=current_user)

    async def delete_candidate(
        self, candidate_id: str, current_user: User | None = None
    ) -> None:
        candidate = await self.candidate_repo.get_by_id(candidate_id)
        if not candidate:
            raise NotFoundException("Kandidat tidak ditemukan")

        interview_count = (
            await self.session.execute(
                select(func.count()).select_from(Interview).where(Interview.nid_candidate == candidate.nid)
            )
        ).scalar_one()
        thread_count = (
            await self.session.execute(
                select(func.count()).select_from(NegotiationThread).where(NegotiationThread.nid_candidate == candidate.nid)
            )
        ).scalar_one()
        recipient_count = (
            await self.session.execute(
                select(func.count()).select_from(ActionRecipient).where(ActionRecipient.nid_candidate == candidate.nid)
            )
        ).scalar_one()

        if interview_count or thread_count or recipient_count:
            raise ConflictException(
                f"Kandidat {candidate.vname} ({candidate.vcandidate_code}) tidak dapat dihapus permanen karena telah memiliki riwayat penjadwalan/wawancara untuk integritas audit."
            )

        code = candidate.vcandidate_code
        name = candidate.vname
        cand_nid = candidate.nid
        await self.candidate_repo.delete(candidate)

        actor = current_user.vname if current_user else "HR Admin"
        await self.audit_service.log_event(
            event_type="CANDIDATE_DELETED",
            actor=actor,
            actor_type="HUMAN",
            title=f"Candidate Deleted ({code})",
            description=f"Data kandidat {name} ({code}) dihapus dari direktori master sebelum memiliki riwayat wawancara.",
            metadata={"deleted_candidate_id": cand_nid, "candidate_code": code},
        )
