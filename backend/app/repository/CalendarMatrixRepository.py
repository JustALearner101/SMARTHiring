from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.OrchestrationModel import CalendarEvent
from app.repository.BaseRepository import BaseRepository


class CalendarMatrixRepository(BaseRepository[CalendarEvent]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CalendarEvent, session)

    async def list_events(
        self,
        user_id: int | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> Sequence[CalendarEvent]:
        stmt = select(CalendarEvent).order_by(CalendarEvent.dscheduled_start_utc.asc())
        if user_id:
            stmt = stmt.where(CalendarEvent.nid_user == user_id)
        if start:
            stmt = stmt.where(CalendarEvent.dscheduled_end_utc >= start)
        if end:
            stmt = stmt.where(CalendarEvent.dscheduled_start_utc <= end)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_conflicts(
        self,
        user_id: int,
        start_utc: datetime,
        end_utc: datetime,
    ) -> Sequence[CalendarEvent]:
        stmt = select(CalendarEvent).where(
            CalendarEvent.nid_user == user_id,
            CalendarEvent.dscheduled_start_utc < end_utc,
            CalendarEvent.dscheduled_end_utc > start_utc,
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
