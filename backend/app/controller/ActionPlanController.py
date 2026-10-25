from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.DatabaseSession import get_db
from app.dto.ActionPlanDTO import (
    ActionPlanDTO,
    PlanApprovalRequestDTO,
    PlanUndoRequestDTO,
)
from app.dto.BaseDTO import ApiResponse
from app.exception.CustomException import NotFoundException
from app.service.ActionPlanService import ActionPlanService

router = APIRouter(prefix="/actionPlans", tags=["ActionPlans"])


@router.get("/current", response_model=ApiResponse[ActionPlanDTO])
async def get_current_plan(
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ActionPlanDTO]:
    service = ActionPlanService(db)
    plan = await service.get_current_plan()
    if not plan:
        raise NotFoundException("Belum ada rencana aksi aktif")
    return ApiResponse(data=plan, message="Berhasil mengambil rencana aksi aktif")


@router.post("/{plan_id}/approve", response_model=ApiResponse[ActionPlanDTO])
async def approve_plan(
    plan_id: str,
    request: PlanApprovalRequestDTO,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ActionPlanDTO]:
    service = ActionPlanService(db)
    try:
        plan = await service.approve_plan(plan_id, request)
        return ApiResponse(data=plan, message="Rencana aksi disetujui, jendela undo 60 detik diaktifkan")
    except ValueError as e:
        raise NotFoundException(str(e)) from e


@router.post("/{plan_id}/undo", response_model=ApiResponse[ActionPlanDTO])
async def undo_plan(
    plan_id: str,
    request: PlanUndoRequestDTO,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ActionPlanDTO]:
    service = ActionPlanService(db)
    try:
        plan = await service.undo_plan(plan_id, request)
        return ApiResponse(data=plan, message="Aksi berhasil dibatalkan dalam batas jendela undo")
    except ValueError as e:
        raise NotFoundException(str(e)) from e
