from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base import TableBaseModel


class Job(TableBaseModel):
    """Processing job pipeline for an interview source file (tblt_job)."""

    __tablename__ = "tblt_job"
    __table_args__ = (
        CheckConstraint(
            "nstatus IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 90, 91, 92, 93)",
            name="ck_tblt_job_nstatus",
        ),
    )

    vasr_engine: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vasr_model_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vlanguage_code: Mapped[str] = mapped_column(String(20), nullable=False, default="id")
    nstatus: Mapped[int] = mapped_column(Integer, nullable=False, default=1, index=True)
    nid_source: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tblt_source_file.nid", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    source_file: Mapped["SourceFile"] = relationship("SourceFile", back_populates="jobs")  # noqa: F821
    transcript_segments: Mapped[list["TranscriptSegment"]] = relationship(
        "TranscriptSegment",
        back_populates="job",
        cascade="all, delete-orphan",
    )
    summary_points: Mapped[list["SummaryPoint"]] = relationship(  # noqa: F821
        "SummaryPoint",
        back_populates="job",
        cascade="all, delete-orphan",
    )
    flags: Mapped[list["Flag"]] = relationship("Flag", back_populates="job")  # noqa: F821
    hr_decisions: Mapped[list["HrDecision"]] = relationship("HrDecision", back_populates="job")  # noqa: F821
    followup_plans: Mapped[list["FollowupPlan"]] = relationship("FollowupPlan", back_populates="job")  # noqa: F821


class TranscriptSegment(TableBaseModel):
    """Timestamped speech-to-text transcript segments (tblt_transcript_segment)."""

    __tablename__ = "tblt_transcript_segment"
    __table_args__ = (
        UniqueConstraint("nid_job", "nsegment_no", name="uq_tblt_transcript_segment_job_no"),
        CheckConstraint("nend_ms >= nstart_ms", name="ck_tblt_transcript_segment_times"),
        CheckConstraint(
            "fconfidence >= 0.0 AND fconfidence <= 1.0",
            name="ck_tblt_transcript_segment_confidence",
        ),
        CheckConstraint(
            "vspeaker_type IN ('CANDIDATE', 'INTERVIEWER', 'UNKNOWN')",
            name="ck_tblt_transcript_segment_speaker_type",
        ),
    )

    nsegment_no: Mapped[int] = mapped_column(Integer, nullable=False)
    nstart_ms: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    nend_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    vspeaker_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vspeaker_type: Mapped[str] = mapped_column(String(50), nullable=False, default="UNKNOWN")
    vtext: Mapped[str] = mapped_column(Text, nullable=False)
    fconfidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    nis_uncertain: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    nid_job: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tblt_job.nid", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    job: Mapped["Job"] = relationship("Job", back_populates="transcript_segments")
