from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.AppSecurity import require_roles
from app.db.DatabaseSession import get_db
from app.dto.ActionPlanDTO import (
    ActionPlanDTO,
    PlanApprovalRequestDTO,
    PlanRejectRequestDTO,
    PlanUndoRequestDTO,
)
from app.dto.BaseDTO import ApiResponse
from app.exception.CustomException import NotFoundException
from app.model.UserModel import User
from app.service.ActionPlanService import ActionPlanService

router = APIRouter(prefix="/actionPlans", tags=["ActionPlans"])


@router.get("/current", response_model=ApiResponse[ActionPlanDTO])
async def get_current_plan(
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ActionPlanDTO]:
    service = ActionPlanService(db)
    plan = await service.get_current_plan()
    if not plan:
        raise NotFoundException("No active action plan available")
    return ApiResponse(data=plan, message="Active action plan retrieved successfully")


@router.post("/{plan_id}/approve", response_model=ApiResponse[ActionPlanDTO])
async def approve_plan(
    plan_id: str,
    request: PlanApprovalRequestDTO,
    current_user: User = Depends(require_roles(["HR", "ADMIN"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ActionPlanDTO]:
    service = ActionPlanService(db)
    try:
        plan = await service.approve_plan(plan_id, request)
        return ApiResponse(data=plan, message="Action plan approved by HR, 60-second undo window activated")
    except ValueError as e:
        raise NotFoundException(str(e)) from e


@router.post("/{plan_id}/undo", response_model=ApiResponse[ActionPlanDTO])
async def undo_plan(
    plan_id: str,
    request: PlanUndoRequestDTO,
    current_user: User = Depends(require_roles(["HR", "ADMIN"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ActionPlanDTO]:
    service = ActionPlanService(db)
    try:
        plan = await service.undo_plan(plan_id, request)
        return ApiResponse(data=plan, message="Action successfully undone by HR within undo window")
    except ValueError as e:
        raise NotFoundException(str(e)) from e


@router.post("/{plan_id}/reject", response_model=ApiResponse[ActionPlanDTO])
async def reject_plan(
    plan_id: str,
    request: PlanRejectRequestDTO,
    current_user: User = Depends(require_roles(["HR", "ADMIN"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ActionPlanDTO]:
    service = ActionPlanService(db)
    try:
        plan = await service.reject_plan(plan_id, request)
        return ApiResponse(data=plan, message="Action plan rejected by HR, no external actions executed")
    except ValueError as e:
        raise NotFoundException(str(e)) from e


