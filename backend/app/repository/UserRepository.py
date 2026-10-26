from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.UserModel import User
from app.repository.BaseRepository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data access repository for internal system users (tblm_user)."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.vusername == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.vemail == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_first_by_role(self, role: str) -> User | None:
        stmt = select(User).where(User.vrole == role, User.vstatus == "ACTIVE").order_by(User.nid.asc()).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active_users(self) -> Sequence[User]:
        stmt = select(User).where(User.vstatus == "ACTIVE").order_by(User.nid.asc())
        result = await self.session.execute(stmt)
        return result.scalars().all()
