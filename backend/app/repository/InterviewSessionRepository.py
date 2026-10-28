from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.model.CandidateModel import Candidate
from app.model.InterviewModel import Interview, SourceFile
from app.model.JobModel import Job
from app.model.SummaryModel import HrDecision, SummaryEvidence, SummaryPoint
from app.repository.BaseRepository import BaseRepository


class InterviewSessionRepository(BaseRepository[Interview]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Interview, session)

    async def list_interviews(
        self,
        candidate_code: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Interview], int]:
        stmt = (
            select(Interview)
            .options(
                selectinload(Interview.candidate),
                selectinload(Interview.profile),
                selectinload(Interview.source_files)
                .selectinload(SourceFile.jobs)
                .selectinload(Job.summary_points)
                .selectinload(SummaryPoint.competency),
                selectinload(Interview.source_files)
                .selectinload(SourceFile.jobs)
                .selectinload(Job.summary_points)
                .selectinload(SummaryPoint.evidences)
                .selectinload(SummaryEvidence.transcript),
                selectinload(Interview.source_files)
                .selectinload(SourceFile.jobs)
                .selectinload(Job.hr_decisions)
                .selectinload(HrDecision.decided_by),
            )
            .order_by(Interview.nid.desc())
        )
        count_stmt = select(func.count()).select_from(Interview)

        if candidate_code:
            stmt = stmt.join(Interview.candidate).where(Candidate.vcandidate_code == candidate_code)
            count_stmt = count_stmt.join(Interview.candidate).where(Candidate.vcandidate_code == candidate_code)

        total = (await self.session.execute(count_stmt)).scalar_one() or 0
        items = (await self.session.execute(stmt.offset(offset).limit(limit))).scalars().all()
        return items, total

    async def get_interview_detail(self, interview_id: int) -> Interview | None:
        stmt = (
            select(Interview)
            .options(
                selectinload(Interview.candidate),
                selectinload(Interview.profile),
                selectinload(Interview.source_files)
                .selectinload(SourceFile.jobs)
                .selectinload(Job.summary_points)
                .selectinload(SummaryPoint.competency),
                selectinload(Interview.source_files)
                .selectinload(SourceFile.jobs)
                .selectinload(Job.summary_points)
                .selectinload(SummaryPoint.evidences)
                .selectinload(SummaryEvidence.transcript),
                selectinload(Interview.source_files)
                .selectinload(SourceFile.jobs)
                .selectinload(Job.hr_decisions)
                .selectinload(HrDecision.decided_by),
            )
            .where(Interview.nid == interview_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
