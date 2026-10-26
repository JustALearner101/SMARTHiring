from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.JobModel import TranscriptSegment
from app.repository.BaseRepository import BaseRepository


class InterviewTranscriptRepository(BaseRepository[TranscriptSegment]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(TranscriptSegment, session)

    async def list_by_job(self, job_id: int) -> Sequence[TranscriptSegment]:
        stmt = (
            select(TranscriptSegment)
            .where(TranscriptSegment.nid_job == job_id)
            .order_by(TranscriptSegment.nsegment_no.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
