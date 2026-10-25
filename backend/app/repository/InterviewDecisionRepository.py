from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.SummaryModel import HrDecision
from app.repository.BaseRepository import BaseRepository


class InterviewDecisionRepository(BaseRepository[HrDecision]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(HrDecision, session)

    async def get_by_job(self, job_id: int) -> HrDecision | None:
        stmt = select(HrDecision).where(HrDecision.nid_job == job_id).order_by(HrDecision.nid.desc()).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
