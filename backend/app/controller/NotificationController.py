from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.AppSecurity import get_current_user
from app.db.DatabaseSession import get_db
from app.dto.BaseDTO import ApiResponse
from app.dto.NotificationDTO import NotificationDTO
from app.model.UserModel import User
from app.service.NotificationService import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=ApiResponse[list[NotificationDTO]])
async def get_user_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[NotificationDTO]]:
    service = NotificationService(db)
    items = await service.get_user_notifications(current_user=current_user)
    return ApiResponse(
        data=items,
        message=f"Successfully retrieved notifications for the user {current_user.vname}",
    )