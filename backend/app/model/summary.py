from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base import TableBaseModel


class SummaryPoint(TableBaseModel):
    """Neutral summary point per evaluated competency (tblt_summary_point)."""

    __tablename__ = "tblt_summary_point"
    __table_args__ = (
        CheckConstraint(
            "vcoverage_status IN ('COVERED', 'PARTIAL', 'NOT_DISCUSSED')",
            name="ck_tblt_summary_point_coverage",
        ),
        CheckConstraint(
            "vverification_status IN ('VERIFIED', 'UNVERIFIED', 'NOT_APPLICABLE')",
            name="ck_tblt_summary_point_verification",
        ),
    )

    vcoverage_status: Mapped[str] = mapped_column(String(50), nullable=False, default="COVERED")
    vcontent: Mapped[str] = mapped_column(Text, nullable=False)
    vverification_status: Mapped[str] = mapped_column(String(50), nullable=False, default="UNVERIFIED")
    nid_competency: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tblm_competency.nid", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    nid_job: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tblt_job.nid", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    competency: Mapped["Competency"] = relationship("Competency")  # noqa: F821
    job: Mapped["Job"] = relationship("Job", back_populates="summary_points")  # noqa: F821
    evidences: Mapped[list["SummaryEvidence"]] = relationship(
        "SummaryEvidence",
        back_populates="summary_point",
        cascade="all, delete-orphan",
    )


class SummaryEvidence(TableBaseModel):
    """Direct transcript quote evidence supporting a summary point (tblt_summary_evidence)."""

    __tablename__ = "tblt_summary_evidence"

    vquote: Mapped[str] = mapped_column(Text, nullable=False)
    nid_transcript: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tblt_transcript_segment.nid", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    nid_summary_point: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tblt_summary_point.nid", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    transcript: Mapped["TranscriptSegment"] = relationship("TranscriptSegment")  # noqa: F821
    summary_point: Mapped["SummaryPoint"] = relationship("SummaryPoint", back_populates="evidences")


class Flag(TableBaseModel):
    """Flags for human attention: clarification, sensitive, or prompt injection (tblt_flag)."""

    __tablename__ = "tblt_flag"
    __table_args__ = (
        CheckConstraint(
            "vflag_type IN ('NEEDS_CLARIFICATION', 'SENSITIVE_ATTRIBUTE', 'UNCERTAIN_SEGMENT', 'EMBEDDED_INSTRUCTION')",
            name="ck_tblt_flag_type",
        ),
        CheckConstraint(
            "vstatus IN ('OPEN', 'REVIEWED')",
            name="ck_tblt_flag_status",
        ),
    )

    vflag_type: Mapped[str] = mapped_column(String(50), nullable=False)
    vneutral_text: Mapped[str] = mapped_column(Text, nullable=False)
    vstatus: Mapped[str] = mapped_column(String(50), nullable=False, default="OPEN")
    nid_job: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tblt_job.nid", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    nid_transcript: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("tblt_transcript_segment.nid", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    nid_reviewed_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("tblm_user.nid", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    dreviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    job: Mapped["Job"] = relationship("Job", back_populates="flags")  # noqa: F821
    transcript: Mapped["TranscriptSegment | None"] = relationship("TranscriptSegment")  # noqa: F821
    reviewed_by: Mapped["User | None"] = relationship("User")  # noqa: F821


class HrDecision(TableBaseModel):
    """Immutable human HR decision on interview outcome (tblt_hr_decision)."""

    __tablename__ = "tblt_hr_decision"
    __table_args__ = (
        CheckConstraint(
            "vdecision IN ('PROCEED', 'HOLD', 'REJECT')",
            name="ck_tblt_hr_decision_val",
        ),
    )

    vdecision: Mapped[str] = mapped_column(String(50), nullable=False)
    vnote: Mapped[str | None] = mapped_column(Text, nullable=True)
    vsummary_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nid_job: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tblt_job.nid", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    nid_decided_by: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tblm_user.nid", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    ddecided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    job: Mapped["Job"] = relationship("Job", back_populates="hr_decisions")  # noqa: F821
    decided_by: Mapped["User"] = relationship("User")  # noqa: F821
