from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.base import TableBaseModel


class Interview(TableBaseModel):
    """Interview session with candidate consent tracking (tblt_interview)."""

    __tablename__ = "tblt_interview"
    __table_args__ = (
        CheckConstraint(
            "vconsent_status IN ('GRANTED', 'NOT_GRANTED', 'WITHDRAWN')",
            name="ck_tblt_interview_vconsent_status",
        ),
    )

    vconsent_status: Mapped[str] = mapped_column(String(50), nullable=False, default="NOT_GRANTED")
    dconsent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    vconsent_notice_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    nid_profile: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tblm_profile.nid", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    nid_candidate: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tblm_candidate.nid", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    profile: Mapped["Profile"] = relationship("Profile")  # noqa: F821
    candidate: Mapped["Candidate"] = relationship("Candidate")  # noqa: F821
    source_files: Mapped[list["SourceFile"]] = relationship(
        "SourceFile",
        back_populates="interview",
        cascade="all, delete-orphan",
    )


class SourceFile(TableBaseModel):
    """Uploaded recording or note files for an interview session (tblt_source_file)."""

    __tablename__ = "tblt_source_file"
    __table_args__ = (
        CheckConstraint(
            "vtype IN ('AUDIO', 'VIDEO', 'TRANSCRIPT_TEXT', 'MANUAL_NOTE')",
            name="ck_tblt_source_file_vtype",
        ),
    )

    vtype: Mapped[str] = mapped_column(String(50), nullable=False)
    vurl: Mapped[str] = mapped_column(String(1000), nullable=False)
    vduration: Mapped[str | None] = mapped_column(String(50), nullable=True)
    nid_interview: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tblt_interview.nid", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    interview: Mapped["Interview"] = relationship("Interview", back_populates="source_files")
    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="source_file")  # noqa: F821
