from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.BaseModel import TableBaseModel

if TYPE_CHECKING:
    from app.model.CandidateModel import Candidate
    from app.model.UserModel import User


class CalendarEvent(TableBaseModel):
    """Calendar matrix event for interviewers, blockers, and prayer times (tblt_calendar_event)."""

    __tablename__ = "tblt_calendar_event"
    __table_args__ = (
        CheckConstraint(
            "vevent_type IN ('SCHEDULED_INTERVIEW', 'TEAM_MEETING', 'FRIDAY_PRAYER_BLOCK', 'OUT_OF_OFFICE', 'BUFFER_BLOCK')",
            name="ck_tblt_calendar_event_type",
        ),
        CheckConstraint(
            "dscheduled_end_utc >= dscheduled_start_utc",
            name="ck_tblt_calendar_event_times",
        ),
    )

    nid_user: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tblm_user.nid", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    vtitle: Mapped[str] = mapped_column(String(255), nullable=False)
    dscheduled_start_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    dscheduled_end_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    vevent_type: Mapped[str] = mapped_column(String(50), nullable=False, default="SCHEDULED_INTERVIEW")
    vcandidate_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vrule_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vdescription: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User")


class NegotiationThread(TableBaseModel):
    """Multi-round interview scheduling negotiation thread (tblt_negotiation_thread)."""

    __tablename__ = "tblt_negotiation_thread"
    __table_args__ = (
        CheckConstraint(
            "vstatus IN ('NEGOTIATING', 'SCHEDULED', 'DEADLOCK_ESCALATED', 'EXPIRED')",
            name="ck_tblt_negotiation_thread_status",
        ),
        CheckConstraint(
            "ncurrent_round >= 1 AND ncurrent_round <= nmax_rounds",
            name="ck_tblt_negotiation_thread_round_limit",
        ),
    )

    nid_candidate: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tblm_candidate.nid", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    nid_interviewer: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tblm_user.nid", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    ncurrent_round: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    nmax_rounds: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    vstatus: Mapped[str] = mapped_column(String(50), nullable=False, default="NEGOTIATING")
    ddeadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dlast_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    vescalation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    vagreed_slot: Mapped[str | None] = mapped_column(String(255), nullable=True)

    candidate: Mapped["Candidate"] = relationship("Candidate")
    interviewer: Mapped["User"] = relationship("User")
    messages: Mapped[list["ThreadMessage"]] = relationship(
        "ThreadMessage",
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="ThreadMessage.nid",
    )


class ThreadMessage(TableBaseModel):
    """Individual dialogue message within a negotiation round (tblt_thread_message)."""

    __tablename__ = "tblt_thread_message"
    __table_args__ = (
        CheckConstraint(
            "vsender_role IN ('AI_ORCHESTRATOR', 'CANDIDATE', 'HR_ADMIN')",
            name="ck_tblt_thread_message_sender_role",
        ),
        CheckConstraint(
            "vchannel IN ('whatsapp', 'email')",
            name="ck_tblt_thread_message_channel",
        ),
    )

    nid_thread: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tblt_negotiation_thread.nid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nround_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    vsender_role: Mapped[str] = mapped_column(String(50), nullable=False)
    vsender_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vchannel: Mapped[str] = mapped_column(String(20), nullable=False, default="whatsapp")
    vcontent: Mapped[str] = mapped_column(Text, nullable=False)
    vproposed_slot: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vsource_citation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bis_rejection: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    thread: Mapped["NegotiationThread"] = relationship("NegotiationThread", back_populates="messages")
