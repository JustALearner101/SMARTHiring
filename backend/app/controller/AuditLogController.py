from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.AppSecurity import require_roles
from app.db.DatabaseSession import get_db
from app.dto.AuditLogDTO import (
    AuditEventDTO,
    AuditStatsDTO,
    HashChainVerificationDTO,
)
from app.dto.BaseDTO import ApiResponse, PaginatedResponse, PaginationParams
from app.model.UserModel import User
from app.service.AuditLogService import AuditLogService

router = APIRouter(prefix="/auditLogs", tags=["AuditLogs"])


@router.get("/stats", response_model=ApiResponse[AuditStatsDTO])
async def get_audit_stats(
    _current_user: User = Depends(require_roles(["ADMIN", "HR"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AuditStatsDTO]:
    """Returns summary statistics of the Audit & Security module."""
    service = AuditLogService(db)
    stats = await service.get_audit_stats()
    return ApiResponse(data=stats, message="Audit & security statistics loaded successfully")


@router.get("/verify", response_model=ApiResponse[HashChainVerificationDTO])
async def verify_hash_chain(
    _current_user: User = Depends(require_roles(["ADMIN", "HR"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[HashChainVerificationDTO]:
    """Runs cryptographic SHA-256 hash-chain integrity verification across audit ledger blocks."""
    service = AuditLogService(db)
    verification = await service.verify_hash_chain()
    return ApiResponse(data=verification, message="Hash chain integrity verification completed")


@router.get("", response_model=ApiResponse[PaginatedResponse[AuditEventDTO]])
async def list_audit_logs(
    params: PaginationParams = Depends(),
    _current_user: User = Depends(require_roles(["HR", "ADMIN"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedResponse[AuditEventDTO]]:
    service = AuditLogService(db)
    logs = await service.list_audit_events(params=params)
    return ApiResponse(data=logs, message="Chained audit log records retrieved successfully")
