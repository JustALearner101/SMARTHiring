from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base import AppendOnlyBaseModel


class AuditLog(AppendOnlyBaseModel):
    """Cryptographic hash-chained append-only business event audit log (tblt_audit_log)."""

    __tablename__ = "tblt_audit_log"
    __table_args__ = (
        CheckConstraint(
            "vactor_type IN ('ORCHESTRATOR', 'AGENT', 'HUMAN')",
            name="ck_tblt_audit_log_actor_type",
        ),
    )

    nid_job: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("tblt_job.nid", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    vactor_type: Mapped[str] = mapped_column(String(50), nullable=False)
    vactor_id: Mapped[str] = mapped_column(String(100), nullable=False)
    vevent_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    vpayload_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    vmasked_detail: Mapped[str] = mapped_column(Text, nullable=False)
    vprev_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vhash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    job: Mapped["Job | None"] = relationship("Job")  # noqa: F821


class SystemLog(AppendOnlyBaseModel):
    """Technical application error and access log (tbl_log_system)."""

    __tablename__ = "tbl_log_system"
    __table_args__ = (
        CheckConstraint(
            "vlog_level IN ('INFO', 'WARN', 'ERROR')",
            name="ck_tbl_log_system_level",
        ),
    )

    vlog_level: Mapped[str] = mapped_column(String(20), nullable=False)
    vlog_message: Mapped[str] = mapped_column(Text, nullable=False)
    vlog_stacktrace: Mapped[str | None] = mapped_column(Text, nullable=True)
    vlog_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vlog_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vlog_method: Mapped[str | None] = mapped_column(String(20), nullable=True)
    vlog_status_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
