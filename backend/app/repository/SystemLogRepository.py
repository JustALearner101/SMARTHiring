from collections.abc import Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.DatabaseSession import AsyncSessionLocal
from app.model.AuditModel import SystemLog
from app.repository.BaseRepository import BaseRepository


class SystemLogRepository(BaseRepository[SystemLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SystemLog, session)

    async def create_log(
        self,
        vlog_level: str,
        vlog_message: str,
        vlog_stacktrace: str | None = None,
        vlog_source: str | None = "API",
        vlog_path: str | None = None,
        vlog_method: str | None = None,
        vlog_status_code: str | None = None,
    ) -> SystemLog:
        log_entry = SystemLog(
            vlog_level=vlog_level.upper(),
            vlog_message=vlog_message,
            vlog_stacktrace=vlog_stacktrace,
            vlog_source=vlog_source,
            vlog_path=vlog_path,
            vlog_method=vlog_method,
            vlog_status_code=str(vlog_status_code) if vlog_status_code else None,
        )
        self.session.add(log_entry)
        await self.session.commit()
        await self.session.refresh(log_entry)
        return log_entry

    @classmethod
    async def log_direct(
        cls,
        vlog_level: str,
        vlog_message: str,
        vlog_stacktrace: str | None = None,
        vlog_source: str | None = "System",
        vlog_path: str | None = None,
        vlog_method: str | None = None,
        vlog_status_code: str | None = None,
    ) -> None:
        async with AsyncSessionLocal() as session:
            try:
                log_entry = SystemLog(
                    vlog_level=vlog_level.upper(),
                    vlog_message=vlog_message,
                    vlog_stacktrace=vlog_stacktrace,
                    vlog_source=vlog_source,
                    vlog_path=vlog_path,
                    vlog_method=vlog_method,
                    vlog_status_code=str(vlog_status_code) if vlog_status_code else None,
                )
                session.add(log_entry)
                await session.commit()
            except Exception:
                await session.rollback()

    async def list_logs(
        self,
        offset: int = 0,
        limit: int = 20,
        level: str | None = None,
        source: str | None = None,
        search: str | None = None,
    ) -> tuple[Sequence[SystemLog], int]:
        conditions: list[Any] = []
        if level:
            conditions.append(SystemLog.vlog_level == level.upper())
        if source:
            conditions.append(SystemLog.vlog_source == source)
        if search:
            search_pattern = f"%{search}%"
            conditions.append(
                (SystemLog.vlog_message.ilike(search_pattern))
                | (SystemLog.vlog_path.ilike(search_pattern))
            )

        return await self.paginate(
            offset=offset,
            limit=limit,
            where_conditions=conditions if conditions else None,
            order_by=SystemLog.nid.desc(),
        )