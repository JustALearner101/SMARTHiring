from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.model.CandidateModel import Candidate
from app.model.InterviewModel import Interview, SourceFile
from app.model.JobModel import Job
from app.model.RubricModel import Profile
from app.model.SummaryModel import HrDecision, SummaryEvidence, SummaryPoint
from app.repository.BaseRepository import BaseRepository


class InterviewSessionRepository(BaseRepository[Interview]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Interview, session)

    def _eager_options(self):
        return (
            selectinload(Interview.candidate),
            selectinload(Interview.interviewer),
            selectinload(Interview.profile).selectinload(Profile.owner),
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

    async def list_interviews(
        self,
        candidate_code: str | None = None,
        interviewer_id: int | None = None,
        awaiting_hr_only: bool = False,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Interview], int]:
        stmt = (
            select(Interview)
            .options(*self._eager_options())
            .order_by(
                func.coalesce(Interview.dmodi, Interview.dcrea).desc(),
                Interview.nid.desc(),
            )
        )
        count_stmt = select(func.count()).select_from(Interview)

        if candidate_code:
            stmt = stmt.join(Interview.candidate).where(Candidate.vcandidate_code == candidate_code)
            count_stmt = count_stmt.join(Interview.candidate).where(Candidate.vcandidate_code == candidate_code)

        if interviewer_id is not None:
            stmt = stmt.where(Interview.nid_interviewer == interviewer_id)
            count_stmt = count_stmt.where(Interview.nid_interviewer == interviewer_id)

        if awaiting_hr_only:
            pending_subq = (
                select(HrDecision.nid)
                .join(Job, HrDecision.nid_job == Job.nid)
                .join(SourceFile, Job.nid_source == SourceFile.nid)
                .where(
                    SourceFile.nid_interview == Interview.nid,
                    HrDecision.vworkflow_status == "PENDING_HR_FOLLOWUP",
                )
            )
            finalized_subq = (
                select(HrDecision.nid)
                .join(Job, HrDecision.nid_job == Job.nid)
                .join(SourceFile, Job.nid_source == SourceFile.nid)
                .where(
                    SourceFile.nid_interview == Interview.nid,
                    HrDecision.vworkflow_status == "FINALIZED",
                )
            )
            stmt = stmt.where(pending_subq.exists(), ~finalized_subq.exists())
            count_stmt = count_stmt.where(pending_subq.exists(), ~finalized_subq.exists())

        total = (await self.session.execute(count_stmt)).scalar_one() or 0
        items = (await self.session.execute(stmt.offset(offset).limit(limit))).scalars().all()
        return items, total

    async def get_interview_detail(self, interview_id: int) -> Interview | None:
        stmt = select(Interview).options(*self._eager_options()).where(Interview.nid == interview_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
