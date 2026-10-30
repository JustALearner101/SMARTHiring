from collections.abc import Sequence
from datetime import date

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.CalendarModel import Holiday
from app.repository.BaseRepository import BaseRepository


class HolidayRepository(BaseRepository[Holiday]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Holiday, session)

    async def list_holidays(self, year: int | None = None) -> Sequence[Holiday]:
        stmt = select(Holiday).order_by(
            func.coalesce(Holiday.dmodi, Holiday.dcrea).desc(),
            Holiday.nid.desc(),
        )
        if year:
            stmt = stmt.where(extract("year", Holiday.dholiday_date) == year)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def is_holiday(self, target_date: date) -> Holiday | None:
        stmt = select(Holiday).where(Holiday.dholiday_date == target_date)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
