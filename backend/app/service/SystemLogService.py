from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.BaseDTO import PaginatedResponse, PaginationParams
from app.dto.SystemLogDTO import SystemLogDTO, SystemLogFilterParams
from app.repository.SystemLogRepository import SystemLogRepository


class SystemLogService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = SystemLogRepository(session)

    async def list_system_logs(
        self,
        pagination: PaginationParams,
        filters: SystemLogFilterParams,
    ) -> PaginatedResponse[SystemLogDTO]:
        items, total = await self.repo.list_logs(
            offset=pagination.offset,
            limit=pagination.limit,
            level=filters.level,
            source=filters.source,
            search=filters.search,
        )

        dtos = [
            SystemLogDTO(
                nid=item.nid,
                vlog_level=item.vlog_level,
                vlog_message=item.vlog_message,
                vlog_stacktrace=item.vlog_stacktrace,
                vlog_source=item.vlog_source,
                vlog_path=item.vlog_path,
                vlog_method=item.vlog_method,
                vlog_status_code=item.vlog_status_code,
                dcrea=item.dcrea,
            )
            for item in items
        ]

        return PaginatedResponse.create(
            items=dtos,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )