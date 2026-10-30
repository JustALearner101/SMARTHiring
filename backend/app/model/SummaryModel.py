from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

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

from app.model.BaseModel import TableBaseModel

if TYPE_CHECKING:
    from app.model.JobModel import Job, TranscriptSegment
    from app.model.RubricModel import Competency
    from app.model.UserModel import User


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

    competency: Mapped[Competency] = relationship("Competency")
    job: Mapped[Job] = relationship("Job", back_populates="summary_points")
    evidences: Mapped[list[SummaryEvidence]] = relationship(
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

    transcript: Mapped[TranscriptSegment] = relationship("TranscriptSegment")
    summary_point: Mapped[SummaryPoint] = relationship("SummaryPoint", back_populates="evidences")


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

    job: Mapped[Job] = relationship("Job", back_populates="flags")
    transcript: Mapped[TranscriptSegment | None] = relationship("TranscriptSegment")
    reviewed_by: Mapped[User | None] = relationship("User")


class HrDecision(TableBaseModel):
    """Immutable human decision or interviewer recommendation on interview outcome (tblt_hr_decision)."""

    __tablename__ = "tblt_hr_decision"
    __table_args__ = (
        CheckConstraint(
            "vdecision IN ('PROCEED', 'HOLD', 'REJECT')",
            name="ck_tblt_hr_decision_val",
        ),
        CheckConstraint(
            "vnext_stage IS NULL OR vnext_stage IN ('NEXT_INTERVIEW', 'TECHNICAL_TEST', 'OFFERED')",
            name="ck_tblt_hr_decision_next_stage",
        ),
        CheckConstraint(
            "vactor_role IN ('INTERVIEWER', 'HR')",
            name="ck_tblt_hr_decision_actor_role",
        ),
        CheckConstraint(
            "vworkflow_status IN ('PENDING_HR_FOLLOWUP', 'FINALIZED')",
            name="ck_tblt_hr_decision_workflow_status",
        ),
    )

    vdecision: Mapped[str] = mapped_column(String(50), nullable=False)
    vnext_stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vactor_role: Mapped[str] = mapped_column(String(30), nullable=False, default="HR", server_default="HR")
    vworkflow_status: Mapped[str] = mapped_column(String(30), nullable=False, default="FINALIZED", server_default="FINALIZED")
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

    job: Mapped[Job] = relationship("Job", back_populates="hr_decisions")
    decided_by: Mapped[User] = relationship("User")
