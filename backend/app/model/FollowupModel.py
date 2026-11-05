from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.model.BaseModel import TableBaseModel

if TYPE_CHECKING:
    from app.model.CandidateModel import Candidate
    from app.model.JobModel import Job
    from app.model.OrchestrationModel import NegotiationThread
    from app.model.UserModel import User


class FollowupPlan(TableBaseModel):
    """Discrete action plan items: Email, Calendar booking, or Task (tblt_followup_plan)."""

    __tablename__ = "tblt_followup_plan"
    __table_args__ = (
        CheckConstraint(
            "vaction_type IN ('EMAIL', 'CALENDAR', 'TASK')",
            name="ck_tblt_followup_plan_action_type",
        ),
        CheckConstraint(
            "vimpact_level IN ('NORMAL', 'HIGH')",
            name="ck_tblt_followup_plan_impact_level",
        ),
        CheckConstraint(
            "vapproval_status IN ('DRAFT', 'AWAITING_CLARIFICATION', 'AWAITING_APPROVAL', "
            "'APPROVED', 'REJECTED', 'INVALIDATED', 'EXECUTED', 'UNDONE')",
            name="ck_tblt_followup_plan_approval_status",
        ),
        CheckConstraint(
            "vapproval_status <> 'EXECUTED' OR vapproval_token IS NOT NULL",
            name="ck_tblt_followup_plan_execution_token",
        ),
        CheckConstraint(
            "dscheduled_end_utc IS NULL OR dscheduled_start_utc IS NULL OR dscheduled_end_utc >= dscheduled_start_utc",
            name="ck_tblt_followup_plan_schedule_times",
        ),
    )

    vplan: Mapped[str] = mapped_column(Text, nullable=False)
    vaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    dscheduled_start_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dscheduled_end_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    vlocation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vimpact_level: Mapped[str] = mapped_column(String(50), nullable=False, default="NORMAL")
    vapproval_status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT", index=True)
    vplan_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vapproval_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nid_approved_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("tblm_user.nid", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    dapproved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    vmock_result_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dexecuted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dundo_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    nid_job: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("tblt_job.nid", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    nid_thread: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("tblt_negotiation_thread.nid", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    vagent_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )

    job: Mapped["Job | None"] = relationship("Job", back_populates="followup_plans")
    thread: Mapped["NegotiationThread | None"] = relationship("NegotiationThread")
    approved_by: Mapped["User | None"] = relationship("User")
    recipients: Mapped[list["ActionRecipient"]] = relationship(
        "ActionRecipient",
        back_populates="followup_plan",
        cascade="all, delete-orphan",
    )


class ActionRecipient(TableBaseModel):
    """Many-to-many recipients for a follow-up action plan (tblr_action_recipient)."""

    __tablename__ = "tblr_action_recipient"
    __table_args__ = (
        CheckConstraint(
            "vrecipient_role IN ('TO', 'CC', 'ATTENDEE')",
            name="ck_tblr_action_recipient_role",
        ),
        CheckConstraint(
            "((CASE WHEN nid_user IS NOT NULL THEN 1 ELSE 0 END) + "
            "(CASE WHEN nid_candidate IS NOT NULL THEN 1 ELSE 0 END) + "
            "(CASE WHEN vexternal_email IS NOT NULL THEN 1 ELSE 0 END)) = 1",
            name="ck_tblr_action_recipient_single_target",
        ),
    )

    nid_candidate: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("tblm_candidate.nid", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    nid_user: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("tblm_user.nid", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    vexternal_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vrecipient_role: Mapped[str] = mapped_column(String(50), nullable=False, default="TO")
    nid_followup_plan: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tblt_followup_plan.nid", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    candidate: Mapped["Candidate | None"] = relationship("Candidate")
    user: Mapped["User | None"] = relationship("User")
    followup_plan: Mapped["FollowupPlan"] = relationship("FollowupPlan", back_populates="recipients")
