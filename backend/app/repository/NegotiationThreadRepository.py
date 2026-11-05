from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.model.OrchestrationModel import NegotiationThread, ThreadMessage
from app.repository.BaseRepository import BaseRepository


class NegotiationThreadRepository(BaseRepository[NegotiationThread]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(NegotiationThread, session)

    async def list_threads(
        self,
        status: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[NegotiationThread], int]:
        latest_activity_expr = func.greatest(
            func.coalesce(NegotiationThread.dlast_activity_at, NegotiationThread.dcrea),
            func.coalesce(NegotiationThread.dmodi, NegotiationThread.dcrea),
        )
        stmt = (
            select(NegotiationThread)
            .options(
                selectinload(NegotiationThread.candidate),
                selectinload(NegotiationThread.interviewer),
                selectinload(NegotiationThread.messages),
            )
            .order_by(latest_activity_expr.desc(), NegotiationThread.nid.desc())
        )
        count_stmt = select(func.count()).select_from(NegotiationThread)
        if status:
            if status.strip().upper() == "ACTIVE":
                stmt = stmt.where(
                    NegotiationThread.vstatus.in_(["NEGOTIATING", "SCHEDULED"])
                )
                count_stmt = count_stmt.where(
                    NegotiationThread.vstatus.in_(["NEGOTIATING", "SCHEDULED"])
                )
            else:
                stmt = stmt.where(NegotiationThread.vstatus == status)
                count_stmt = count_stmt.where(NegotiationThread.vstatus == status)

        total = (await self.session.execute(count_stmt)).scalar_one() or 0
        items = (await self.session.execute(stmt.offset(offset).limit(limit))).scalars().all()
        return items, total

    async def get_thread(self, thread_id: int) -> NegotiationThread | None:
        stmt = (
            select(NegotiationThread)
            .options(
                selectinload(NegotiationThread.candidate),
                selectinload(NegotiationThread.interviewer),
                selectinload(NegotiationThread.messages),
            )
            .where(NegotiationThread.nid == thread_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def append_message(self, thread_id: int, message_data: dict) -> ThreadMessage:
        now = datetime.now(UTC)
        msg = ThreadMessage(nid_thread=thread_id, **message_data)
        self.session.add(msg)

        thread = await self.get_by_id(thread_id)
        if thread:
            thread.dlast_activity_at = now
            thread.dmodi = now
            self.session.add(thread)

        await self.session.commit()
        await self.session.refresh(msg)
        return msg
