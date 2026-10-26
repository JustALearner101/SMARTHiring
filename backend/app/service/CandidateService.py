from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.BaseDTO import PaginatedResponse, PaginationParams
from app.dto.CandidateDTO import (
    CandidateCreateDTO,
    CandidateDTO,
    CandidateUpdateDTO,
)
from app.model.CandidateModel import Candidate
from app.repository.CandidateRepository import CandidateRepository


class CandidateService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.candidate_repo = CandidateRepository(session)

    @staticmethod
    def _to_candidate_dto(candidate: Candidate) -> CandidateDTO:
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
            created_at=candidate.dcrea.isoformat() if candidate.dcrea else datetime.now(UTC).isoformat(),
        )

    async def list_candidates(
        self,
        query: str | None = None,
        status: str | None = None,
        params: PaginationParams | None = None,
    ) -> PaginatedResponse[CandidateDTO]:
        p = params or PaginationParams()
        items, total = await self.candidate_repo.search(
            query=query, status=status, offset=p.offset, limit=p.limit
        )
        return PaginatedResponse.create(
            items=[self._to_candidate_dto(c) for c in items],
            total=total,
            page=p.page,
            page_size=p.page_size,
        )

    async def get_candidate_by_id(self, candidate_id: str) -> CandidateDTO | None:
        candidate = await self.candidate_repo.get_by_id(candidate_id)
        return self._to_candidate_dto(candidate) if candidate else None

    async def create_candidate(self, dto: CandidateCreateDTO) -> CandidateDTO:
        total = await self.candidate_repo.count()
        code = f"CAND-2026-{(total + 1):03d}"
        candidate_data = {
            "vcandidate_code": code,
            "vname": dto.name,
            "vemail": dto.email,
            "vphone_number": dto.phone,
            "vpreferred_channel": dto.preferred_channel,
            "vjob_position": dto.applied_position,
            "vstatus": dto.status,
            "vtimezone": dto.timezone,
            "vresume_url": dto.resume_url,
            "vnotes": dto.notes,
        }
        candidate = await self.candidate_repo.create(candidate_data)
        return self._to_candidate_dto(candidate)

    async def update_candidate(self, candidate_id: str, dto: CandidateUpdateDTO) -> CandidateDTO | None:
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

        updated = await self.candidate_repo.update(candidate, updates)
        return self._to_candidate_dto(updated)
