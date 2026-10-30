from __future__ import annotations

from typing import TYPE_CHECKING, Any

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

from app.model.BaseModel import TableBaseModel

if TYPE_CHECKING:
    from app.model.UserModel import User


class Profile(TableBaseModel):
    """Interview round profile with user/division ownership and rubric versioning (tblm_profile)."""

    __tablename__ = "tblm_profile"
    __table_args__ = (
        UniqueConstraint("vcode", "vversion_no", name="uq_tblm_profile_code_version"),
        CheckConstraint(
            "vtarget_role IN ('HR', 'INTERVIEWER')",
            name="ck_tblm_profile_target_role",
        ),
    )

    vcode: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vname: Mapped[str] = mapped_column(String(255), nullable=False)
    vversion_no: Mapped[str] = mapped_column(String(50), nullable=False, default="v1.0")
    vtarget_role: Mapped[str] = mapped_column(String(50), nullable=False, default="HR", server_default="HR")
    vdepartment: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nid_owner_user: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("tblm_user.nid", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    vsummary_format: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    owner: Mapped[User | None] = relationship("User")
    competencies: Mapped[list[Competency]] = relationship(
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

    profile: Mapped[Profile] = relationship("Profile", back_populates="competencies")
