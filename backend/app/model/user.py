from sqlalchemy import CheckConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.model.base import TableBaseModel


class User(TableBaseModel):
    """Internal system users: HR, Interviewers, and Auditors (tblm_user)."""

    __tablename__ = "tblm_user"
    __table_args__ = (
        CheckConstraint(
            "vrole IN ('HR', 'USER_INTERVIEWER', 'TECH_INTERVIEWER', 'AUDITOR')",
            name="ck_tblm_user_vrole",
        ),
        CheckConstraint(
            "vtimezone IN ('WIB', 'WITA', 'WIT')",
            name="ck_tblm_user_vtimezone",
        ),
        CheckConstraint(
            "vstatus IN ('ACTIVE', 'INACTIVE')",
            name="ck_tblm_user_vstatus",
        ),
    )

    vuserid: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    vname: Mapped[str] = mapped_column(String(255), nullable=False)
    vusername: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    vemail: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    vpassword_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    vposition: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vdepartment: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vrole: Mapped[str] = mapped_column(String(50), nullable=False, default="USER_INTERVIEWER")
    vtimezone: Mapped[str] = mapped_column(String(10), nullable=False, default="WIB")
    vstatus: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    vuser_token: Mapped[str | None] = mapped_column(String(500), nullable=True)


class Permission(TableBaseModel):
    """Data access permissions by role and data visibility class (tblm_permission)."""

    __tablename__ = "tblm_permission"
    __table_args__ = (
        UniqueConstraint("vrole", "vvisibility_class", name="uq_tblm_permission_role_visibility"),
        CheckConstraint(
            "vrole IN ('HR', 'USER_INTERVIEWER', 'TECH_INTERVIEWER', 'AUDITOR')",
            name="ck_tblm_permission_vrole",
        ),
        CheckConstraint(
            "vvisibility_class IN ('GENERAL', 'HR_ONLY', 'SALARY', 'SENSITIVE_FLAG', 'AUDIT_LOG')",
            name="ck_tblm_permission_vvisibility_class",
        ),
        CheckConstraint(
            "vaccess_level IN ('READ', 'WRITE', 'NONE')",
            name="ck_tblm_permission_vaccess_level",
        ),
    )

    vrole: Mapped[str] = mapped_column(String(50), nullable=False)
    vvisibility_class: Mapped[str] = mapped_column(String(50), nullable=False)
    vaccess_level: Mapped[str] = mapped_column(String(20), nullable=False, default="NONE")
