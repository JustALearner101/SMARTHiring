from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.AuditModel import AuditLog
from app.repository.BaseRepository import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AuditLog, session)

    async def get_latest_audit_log(self) -> AuditLog | None:
        stmt = select(AuditLog).order_by(AuditLog.nid.desc()).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def append_audit_log(
        self,
        job_id: int | None,
        actor_type: str,
        actor_id: str,
        event_type: str,
        payload_hash: str,
        masked_detail: str,
        prev_hash: str,
        current_hash: str,
    ) -> AuditLog:
        log = AuditLog(
            nid_job=job_id,
            vactor_type=actor_type,
            vactor_id=actor_id,
            vevent_type=event_type,
            vpayload_hash=payload_hash,
            vmasked_detail=masked_detail,
            vprev_hash=prev_hash,
            vhash=current_hash,
        )
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def list_audit_logs(
        self,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[AuditLog], int]:
        items, total = await self.paginate(
            offset=offset,
            limit=limit,
            order_by=(AuditLog.dcrea.desc(), AuditLog.nid.desc()),
        )
        return items, total
