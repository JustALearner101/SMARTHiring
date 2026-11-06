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
            normalized = status.strip().upper()
            if normalized == "ACTIVE":
                db_statuses = ["NEGOTIATING"]
            elif normalized == "COMPLETED":
                db_statuses = ["SCHEDULED"]
            elif normalized == "HALTED":
                db_statuses = ["DEADLOCK_ESCALATED"]
            elif normalized == "EXPIRED":
                db_statuses = ["EXPIRED"]
            else:
                db_statuses = [normalized]
            stmt = stmt.where(func.upper(NegotiationThread.vstatus).in_(db_statuses))
            count_stmt = count_stmt.where(
                func.upper(NegotiationThread.vstatus).in_(db_statuses)
            )

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

    async def update_thread_status(
        self,
        thread_id: int,
        status: str,
        escalation_reason: str | None = None,
    ) -> NegotiationThread | None:
        """Update a negotiation thread's status (and optional escalation reason)."""
        thread = await self.get_by_id(thread_id)
        if not thread:
            return None
        thread.vstatus = status
        if escalation_reason is not None:
            thread.vescalation_reason = escalation_reason
        thread.dmodi = datetime.now(UTC)
        self.session.add(thread)
        await self.session.commit()
        await self.session.refresh(thread)
        return thread

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
