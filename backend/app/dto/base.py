import uuid
from datetime import datetime

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict


class BaseDTO(PydanticBaseModel):
    """Base DTO schema configured to read from SQLAlchemy ORM models."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TimestampedDTO(BaseDTO):
    """Base DTO with standard UUID id and audit timestamps."""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ApiResponse[T](BaseDTO):
    """Standardized API response envelope."""

    success: bool = True
    message: str = "OK"
    data: T | None = None
