from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.DatabaseSession import get_db
from app.dto.BaseDTO import ApiResponse
from app.dto.CalendarMatrixDTO import CalendarMatrixEventDTO
from app.service.CalendarMatrixService import CalendarMatrixService

router = APIRouter(prefix="/calendarMatrix", tags=["CalendarMatrix"])


@router.get("/events", response_model=ApiResponse[list[CalendarMatrixEventDTO]])
async def list_calendar_events(
    user_id: str | None = Query(None, description="Filter by interviewer user ID"),
    start: str | None = Query(None, description="Start date ISO string"),
    end: str | None = Query(None, description="End date ISO string"),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[CalendarMatrixEventDTO]]:
    service = CalendarMatrixService(db)
    events = await service.list_calendar_events(user_id=user_id, start_iso=start, end_iso=end)
    return ApiResponse(data=events, message="Berhasil mengambil event kalender")
