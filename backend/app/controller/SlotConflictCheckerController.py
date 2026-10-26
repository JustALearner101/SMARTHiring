from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.DatabaseSession import get_db
from app.dto.BaseDTO import ApiResponse
from app.dto.SlotConflictCheckerDTO import (
    SlotConflictCheckRequestDTO,
    SlotConflictCheckResultDTO,
)
from app.service.SlotConflictCheckerService import SlotConflictCheckerService

router = APIRouter(prefix="/slotConflictChecker", tags=["SlotConflictChecker"])


@router.post("/check", response_model=ApiResponse[SlotConflictCheckResultDTO])
async def check_slot_conflict(
    request: SlotConflictCheckRequestDTO,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[SlotConflictCheckResultDTO]:
    service = SlotConflictCheckerService(db)
    result = await service.check_slot_conflict(request)
    return ApiResponse(data=result, message=result.message)
