import math
import uuid
from datetime import datetime

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field


class BaseDTO(PydanticBaseModel):
    """Base DTO schema configured to read from SQLAlchemy ORM models."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TimestampedDTO(BaseDTO):
    """Base DTO with standard UUID id and audit timestamps."""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class PaginationParams(BaseDTO):
    """Query parameter dependency for standard pagination."""

    page: int = Field(1, ge=1, description="Nomor halaman (1-based)")
    page_size: int = Field(20, ge=1, le=100, description="Jumlah item per halaman (1-100)")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class ApiResponse[T](BaseDTO):
    """Standardized API response envelope matching frontend ApiResponse[T]."""

    success: bool = True
    message: str = "OK"
    data: T | None = None


class PaginatedResponse[T](BaseDTO):
    """Standardized paginated list envelope matching frontend PaginatedResponse[T] with enriched metadata."""

    items: list[T]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 1
    has_next: bool = False
    has_prev: bool = False

    @classmethod
    def create(cls, items: list[T], total: int, page: int, page_size: int) -> "PaginatedResponse[T]":
        t_pages = math.ceil(total / page_size) if total > 0 and page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=t_pages,
            has_next=page < t_pages,
            has_prev=page > 1,
        )
