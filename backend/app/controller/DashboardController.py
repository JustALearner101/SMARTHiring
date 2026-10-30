from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.AppSecurity import get_optional_current_user
from app.db.DatabaseSession import get_db
from app.dto.BaseDTO import ApiResponse
from app.dto.DashboardDTO import (
    ActivityFeedDTO,
    DashboardSummaryDTO,
    UpcomingInterviewDTO,
)
from app.model.UserModel import User
from app.service.DashboardService import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=ApiResponse[DashboardSummaryDTO])
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[DashboardSummaryDTO]:
    """Returns KPI metric summaries, pipeline breakdown, and weekly trends."""
    service = DashboardService(db)
    summary = await service.get_summary()
    return ApiResponse(data=summary, message="Dashboard summary loaded successfully")


@router.get(
    "/upcomingInterviews",
    response_model=ApiResponse[list[UpcomingInterviewDTO]],
)
async def get_upcoming_interviews(
    limit: int = Query(5, ge=1, le=20, description="Maximum number of interviews returned"),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[UpcomingInterviewDTO]]:
    """Returns scheduled interviews within the next 7 days."""
    service = DashboardService(db)
    interviews = await service.get_upcoming_interviews(limit=limit)
    return ApiResponse(data=interviews, message="Upcoming interviews list loaded successfully")


@router.get("/activityFeed", response_model=ApiResponse[ActivityFeedDTO])
async def get_activity_feed(
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ActivityFeedDTO]:
    """Returns pending approvals, active negotiations, and audit history (audit trail for ADMIN role only)."""
    service = DashboardService(db)
    is_admin = current_user is not None and current_user.vrole == "ADMIN"
    feed = await service.get_activity_feed(include_audit=is_admin)
    return ApiResponse(data=feed, message="Activity feed loaded successfully")

