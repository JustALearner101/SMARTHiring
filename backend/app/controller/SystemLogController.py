from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.DatabaseSession import get_db
from app.dto.BaseDTO import ApiResponse, PaginatedResponse, PaginationParams
from app.dto.SystemLogDTO import SystemLogDTO, SystemLogFilterParams
from app.service.SystemLogService import SystemLogService

router = APIRouter(prefix="/systemLogs", tags=["SystemLogs"])


@router.get("", response_model=ApiResponse[PaginatedResponse[SystemLogDTO]])
async def list_system_logs(
    pagination: PaginationParams = Depends(),
    filters: SystemLogFilterParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedResponse[SystemLogDTO]]:
    service = SystemLogService(db)
    result = await service.list_system_logs(pagination=pagination, filters=filters)
    return ApiResponse(data=result, message="Successfully retrieved the system log")