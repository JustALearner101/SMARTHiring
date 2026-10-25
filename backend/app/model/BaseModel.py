import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, MetaData, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Declarative base for all SQLAlchemy ORM models."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class AuditMixin:
    """Standard tracking columns (vcrea, dcrea, vmodi, dmodi)."""

    vcrea: Mapped[str | None] = mapped_column(String(100), nullable=True, default="SYSTEM")
    dcrea: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    vmodi: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dmodi: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )


class AppendOnlyMixin:
    """Append-only audit column (dcrea only)."""

    dcrea: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class TableBaseModel(Base, AuditMixin):
    """Standard base model with BigInteger nid primary key and full audit trail."""

    __abstract__ = True

    nid: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        index=True,
    )


class AppendOnlyBaseModel(Base, AppendOnlyMixin):
    """Base model for append-only tables with BigInteger nid and dcrea."""

    __abstract__ = True

    nid: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        index=True,
    )


class BaseModel(Base):
    """Abstract base model providing UUID primary key and audit timestamps (legacy/generic)."""

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
