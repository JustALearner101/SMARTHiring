from datetime import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.CalendarModel import WorkCalendar
from app.repository.BaseRepository import BaseRepository


class OperationalPolicyRepository(BaseRepository[WorkCalendar]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(WorkCalendar, session)

    async def get_policy(self) -> WorkCalendar:
        stmt = select(WorkCalendar).order_by(WorkCalendar.nid.asc()).limit(1)
        result = await self.session.execute(stmt)
        policy = result.scalar_one_or_none()
        if not policy:
            policy = WorkCalendar(
                voffice_code="JKT-HQ",
                vtimezone="WIB",
                twork_start=time(9, 0),
                twork_end=time(17, 0),
                tfriday_prayer_start=time(11, 30),
                tfriday_prayer_end=time(13, 0),
                nmax_negotiation_rounds=3,
                nbuffer_minutes=15,
                binjection_guardrail_enabled=True,
            )
            self.session.add(policy)
            await self.session.commit()
            await self.session.refresh(policy)
        return policy

    async def update_policy(self, updates: dict) -> WorkCalendar:
        policy = await self.get_policy()
        for k, v in updates.items():
            setattr(policy, k, v)
        self.session.add(policy)
        await self.session.commit()
        await self.session.refresh(policy)
        return policy
