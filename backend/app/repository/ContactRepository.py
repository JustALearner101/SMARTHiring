from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.UserModel import User
from app.repository.BaseRepository import BaseRepository


class ContactRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def list_interviewers(self, department: str | None = None) -> Sequence[User]:
        stmt = select(User).where(User.vstatus == "ACTIVE")
        if department:
            stmt = stmt.where(User.vdepartment == department)
        stmt = stmt.order_by(
            func.coalesce(User.dmodi, User.dcrea).desc(),
            User.nid.desc(),
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_ambiguous_names(self, first_name: str) -> Sequence[User]:
        stmt = select(User).where(
            User.vname.ilike(f"{first_name}%"),
            User.vstatus == "ACTIVE",
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
