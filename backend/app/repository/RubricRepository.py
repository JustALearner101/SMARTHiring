from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.model.RubricModel import Profile
from app.repository.BaseRepository import BaseRepository


class RubricRepository(BaseRepository[Profile]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Profile, session)

    async def list_profiles_with_competencies(self) -> Sequence[Profile]:
        stmt = (
            select(Profile)
            .options(selectinload(Profile.competencies))
            .order_by(Profile.nid.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
