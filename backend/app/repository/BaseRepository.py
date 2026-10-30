import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.BaseModel import Base


class BaseRepository[ModelType: Base]:
    """Generic async repository supporting models with integer `nid` or UUID `id`."""

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    @property
    def pk_column(self) -> Any:
        if hasattr(self.model, "nid"):
            return self.model.nid
        if hasattr(self.model, "id"):
            return self.model.id
        raise AttributeError(f"Model {self.model.__name__} has neither 'nid' nor 'id' primary key.")

    async def get_by_id(self, entity_id: int | uuid.UUID | str) -> ModelType | None:
        pk = self.pk_column
        # Safely cast integer PKs if passed as string
        target_id: Any = entity_id
        if hasattr(self.model, "nid") and isinstance(entity_id, str):
            try:
                target_id = int(entity_id)
            except ValueError:
                return None

        stmt = select(self.model).where(pk == target_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(
        self, *, skip: int = 0, limit: int = 100
    ) -> Sequence[ModelType]:
        stmt = select(self.model)
        if hasattr(self.model, "dmodi") and hasattr(self.model, "dcrea"):
            stmt = stmt.order_by(
                func.coalesce(self.model.dmodi, self.model.dcrea).desc(),
                self.pk_column.desc(),
            )
        elif hasattr(self.model, "dcrea"):
            stmt = stmt.order_by(self.model.dcrea.desc(), self.pk_column.desc())
        else:
            stmt = stmt.order_by(self.pk_column.desc())
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def paginate(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        where_conditions: Sequence[Any] | None = None,
        order_by: Any = None,
    ) -> tuple[Sequence[ModelType], int]:
        """Generic paginated query returning a tuple of (items, total_count)."""
        stmt = select(self.model)
        count_stmt = select(func.count()).select_from(self.model)

        if where_conditions:
            stmt = stmt.where(*where_conditions)
            count_stmt = count_stmt.where(*where_conditions)

        if order_by is not None:
            if isinstance(order_by, (list, tuple)):
                stmt = stmt.order_by(*order_by)
            else:
                stmt = stmt.order_by(order_by)

        total = (await self.session.execute(count_stmt)).scalar_one() or 0
        items = (await self.session.execute(stmt.offset(offset).limit(limit))).scalars().all()
        return items, total

    async def count(self) -> int:
        stmt = select(func.count()).select_from(self.model)
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def create(self, obj_in: dict[str, Any]) -> ModelType:
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(
        self, db_obj: ModelType, obj_in: dict[str, Any]
    ) -> ModelType:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        if hasattr(db_obj, "dmodi"):
            db_obj.dmodi = datetime.now(UTC)  # type: ignore[attr-defined]
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, db_obj: ModelType) -> None:
        await self.session.delete(db_obj)
        await self.session.commit()
