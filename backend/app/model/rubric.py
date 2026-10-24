from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base import TableBaseModel


class Profile(TableBaseModel):
    """Interview round profile with rubric versioning (tblm_profile)."""

    __tablename__ = "tblm_profile"
    __table_args__ = (
        UniqueConstraint("vcode", "vversion_no", name="uq_tblm_profile_code_version"),
    )

    vcode: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vname: Mapped[str] = mapped_column(String(255), nullable=False)
    vversion_no: Mapped[str] = mapped_column(String(50), nullable=False)
    vsummary_format: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    competencies: Mapped[list["Competency"]] = relationship(
        "Competency",
        back_populates="profile",
        cascade="all, delete-orphan",
    )


class Competency(TableBaseModel):
    """Competency criteria under a specific rubric profile (tblm_competency)."""

    __tablename__ = "tblm_competency"
    __table_args__ = (
        UniqueConstraint("nid_profile", "vcode", name="uq_tblm_competency_profile_code"),
        CheckConstraint(
            "vvisibility_class IN ('GENERAL', 'HR_ONLY', 'SALARY', 'SENSITIVE_FLAG', 'AUDIT_LOG')",
            name="ck_tblm_competency_vvisibility_class",
        ),
    )

    vvisibility_class: Mapped[str] = mapped_column(String(50), nullable=False, default="GENERAL")
    vcode: Mapped[str] = mapped_column(String(50), nullable=False)
    vname: Mapped[str] = mapped_column(String(255), nullable=False)
    nsort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    vreference_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    nid_profile: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tblm_profile.nid", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    profile: Mapped["Profile"] = relationship("Profile", back_populates="competencies")
