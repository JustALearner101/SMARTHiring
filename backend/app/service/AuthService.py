from sqlalchemy.ext.asyncio import AsyncSession

from app.core.AppSecurity import create_access_token, verify_password
from app.dto.AuthDTO import LoginRequestDTO, LoginResponseDTO, UserDTO
from app.exception.CustomException import NotFoundException, UnauthorizedException
from app.model.UserModel import User
from app.repository.UserRepository import UserRepository


class AuthService:
    """Business logic service for authentication and user sessions."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)

    @staticmethod
    def _to_user_dto(user: User) -> UserDTO:
        return UserDTO(
            id=str(user.nid),
            employee_id=user.vuserid,
            name=user.vname,
            username=user.vusername,
            email=user.vemail,
            role=user.vrole,
            department=user.vdepartment,
            position=user.vposition,
            timezone=user.vtimezone,
            working_hours=user.vworking_hours,
            status=user.vstatus,
        )

    async def authenticate(self, dto: LoginRequestDTO) -> LoginResponseDTO:
        user = await self.user_repo.get_by_username(dto.username.strip())
        if not user:
            raise UnauthorizedException("Username atau password salah")

        if not verify_password(dto.password, user.vpassword_hash):
            raise UnauthorizedException("Username atau password salah")

        if user.vstatus != "ACTIVE":
            raise UnauthorizedException("Akun pengguna berstatus nonaktif")

        extra_claims = {
            "username": user.vusername,
            "role": user.vrole,
            "name": user.vname,
            "email": user.vemail,
        }
        token = create_access_token(subject=str(user.nid), extra_claims=extra_claims)

        return LoginResponseDTO(
            access_token=token,
            token_type="bearer",
            user=self._to_user_dto(user),
        )

    async def get_user_by_id(self, user_id: str | int) -> UserDTO:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User tidak ditemukan")
        return self._to_user_dto(user)

    async def list_active_users(self) -> list[UserDTO]:
        users = await self.user_repo.list_active_users()
        return [self._to_user_dto(u) for u in users]
