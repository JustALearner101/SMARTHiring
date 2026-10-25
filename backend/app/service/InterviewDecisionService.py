from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.InterviewDecisionDTO import HrDecisionDTO, HrDecisionRequestDTO
from app.model.SummaryModel import HrDecision
from app.repository.InterviewDecisionRepository import InterviewDecisionRepository
from app.repository.InterviewSessionRepository import InterviewSessionRepository


class InterviewDecisionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.interview_repo = InterviewSessionRepository(session)
        self.decision_repo = InterviewDecisionRepository(session)

    async def save_hr_decision(
        self,
        interview_id: str,
        dto: HrDecisionRequestDTO,
    ) -> HrDecisionDTO:
        int_id = int(interview_id) if interview_id.isdigit() else 1
        interview = await self.interview_repo.get_interview_detail(int_id)
        if not interview or not interview.source_files or not interview.source_files[-1].jobs:
            raise ValueError(f"Job wawancara {interview_id} belum selesai diproses.")

        job = interview.source_files[-1].jobs[-1]
        now = datetime.now(UTC)

        decision_data = {
            "nid_job": job.nid,
            "vdecision": "PROCEED" if dto.decision == "ADVANCE" else dto.decision,
            "vnote": dto.notes,
            "nid_decided_by": 1,
            "ddecided_at": now,
        }
        dec = HrDecision(**decision_data)
        self.session.add(dec)
        await self.session.commit()
        await self.session.refresh(dec)

        return HrDecisionDTO(
            decision=dto.decision,
            notes=dto.notes,
            decided_at=now.isoformat(),
            decided_by=dto.decided_by,
        )
