from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.model.BaseModel import TableBaseModel


class Candidate(TableBaseModel):
    """Job applicant data with pseudonymization code and application cycle tracking (tblm_candidate)."""

    __tablename__ = "tblm_candidate"
    __table_args__ = (
        CheckConstraint(
            "vpreferred_channel IN ('whatsapp', 'email')",
            name="ck_tblm_candidate_vpreferred_channel",
        ),
        CheckConstraint(
            "vstatus IN ('SCREENING', 'ESCALATED', 'INTERVIEW_SCHEDULED', 'PENDING_HR_REVIEW', 'TECHNICAL_TEST', 'COMPLETED', 'OFFERED', 'REJECTED')",
            name="ck_tblm_candidate_vstatus",
        ),
        CheckConstraint(
            "vtimezone IN ('WIB', 'WITA', 'WIT')",
            name="ck_tblm_candidate_vtimezone",
        ),
    )

    vcandidate_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    vname: Mapped[str] = mapped_column(String(255), nullable=False)
    vemail: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    vphone_number: Mapped[str] = mapped_column(String(50), nullable=False)
    vpreferred_channel: Mapped[str] = mapped_column(String(20), nullable=False, default="whatsapp")
    vjob_position: Mapped[str] = mapped_column(String(100), nullable=False)
    vstatus: Mapped[str] = mapped_column(String(50), nullable=False, default="SCREENING")
    vtimezone: Mapped[str] = mapped_column(String(10), nullable=False, default="WIB")
    vresume_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    vnotes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ncurrent_salary: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    nexpected_salary: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    napplication_cycle: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    nid_previous_application: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("tblm_candidate.nid", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
