from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.CandidateModel import Candidate
from app.repository.BaseRepository import BaseRepository


class CandidateRepository(BaseRepository[Candidate]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Candidate, session)

    async def get_by_code(self, candidate_code: str) -> Candidate | None:
        stmt = select(Candidate).where(Candidate.vcandidate_code == candidate_code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(
        self,
        query: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Candidate], int]:
        stmt = select(Candidate).order_by(Candidate.nid.desc())
        count_stmt = select(func.count()).select_from(Candidate)

        conditions = []
        if query:
            q = f"%{query}%"
            conditions.append(
                or_(
                    Candidate.vname.ilike(q),
                    Candidate.vemail.ilike(q),
                    Candidate.vcandidate_code.ilike(q),
                    Candidate.vjob_position.ilike(q),
                )
            )
        if status:
            conditions.append(Candidate.vstatus == status)

        if conditions:
            stmt = stmt.where(*conditions)
            count_stmt = count_stmt.where(*conditions)

        total = (await self.session.execute(count_stmt)).scalar_one() or 0
        items = (await self.session.execute(stmt.offset(offset).limit(limit))).scalars().all()
        return items, total
