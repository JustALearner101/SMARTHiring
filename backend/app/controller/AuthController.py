from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.AppSecurity import get_current_user
from app.db.DatabaseSession import get_db
from app.dto.AuthDTO import LoginRequestDTO, LoginResponseDTO, UserDTO
from app.dto.BaseDTO import ApiResponse
from app.model.UserModel import User
from app.service.AuthService import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=ApiResponse[LoginResponseDTO], status_code=status.HTTP_200_OK)
async def login(
    dto: LoginRequestDTO,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[LoginResponseDTO]:
    """Authenticate internal system user (HR, Interviewer, Admin) and issue signed JWT."""
    service = AuthService(db)
    result = await service.authenticate(dto)
    return ApiResponse(data=result, message=f"Logged in successfully as {result.user.name} ({result.user.role})")


@router.get("/me", response_model=ApiResponse[UserDTO])
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[UserDTO]:
    """Retrieve currently authenticated user profile from active session token."""
    service = AuthService(db)
    profile = await service.get_user_by_id(current_user.nid)
    return ApiResponse(data=profile, message="User profile loaded successfully")


@router.get("/users", response_model=ApiResponse[list[UserDTO]])
async def list_active_users(
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[UserDTO]]:
    """List active system users for demo role switching (HR, Interviewer, Admin)."""
    service = AuthService(db)
    users = await service.list_active_users()
    return ApiResponse(data=users, message="Active users retrieved successfully")
