from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.AppSecurity import require_roles
from app.db.DatabaseSession import get_db
from app.dto.AuditLogDTO import AuditEventDTO
from app.dto.BaseDTO import ApiResponse, PaginatedResponse, PaginationParams
from app.model.UserModel import User
from app.service.AuditLogService import AuditLogService

router = APIRouter(prefix="/auditLogs", tags=["AuditLogs"])


@router.get("", response_model=ApiResponse[PaginatedResponse[AuditEventDTO]])
async def list_audit_logs(
    params: PaginationParams = Depends(),
    _current_user: User = Depends(require_roles(["HR", "ADMIN"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedResponse[AuditEventDTO]]:
    service = AuditLogService(db)
    logs = await service.list_audit_events(params=params)
    return ApiResponse(data=logs, message="Berhasil mengambil catatan jejak audit berantai")
