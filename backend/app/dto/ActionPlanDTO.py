from typing import Literal

from pydantic import Field

from app.dto.BaseDTO import BaseDTO

PlanStatus = Literal[
    "IDLE",
    "ANALYZING",
    "CLARIFICATION_NEEDED",
    "PENDING_APPROVAL",
    "UNDO_WINDOW",
    "EXECUTED",
    "UNDONE",
    "REJECTED",
]


class SourceCitationDTO(BaseDTO):
    id: str
    ref_code: str
    source_type: Literal["CALENDAR", "OPERATIONAL_RULE", "CANDIDATE_ATS", "CONTACT"]
    title: str
    detail: str


class ActionItemDraftDTO(BaseDTO):
    id: str
    action_type: Literal["send_email", "send_whatsapp", "book_calendar"]
    recipient_name: str
    recipient_role: str
    recipient_contact: str
    channel: Literal["email", "whatsapp", "calendar"]
    subject: str | None = None
    content_preview: str
    is_external: bool = False


class ProposedSlotDTO(BaseDTO):
    title: str
    start_utc: str
    end_utc: str
    formatted_wib: str
    formatted_wita: str
    duration_minutes: int
    location_type: Literal["Google Meet", "Tencent Meeting", "On-Site Room"]
    meeting_link: str


class ActionPlanDTO(BaseDTO):
    id: str
    candidate_id: str
    candidate_name: str
    candidate_position: str
    candidate_email: str | None = None
    candidate_phone: str | None = None
    interviewer_id: str
    interviewer_name: str
    interviewer_role: str
    interviewer_dept: str
    interviewer_email: str | None = None
    interviewer_phone: str | None = None
    raw_command: str
    negotiation_round: int
    max_rounds: int = 3
    status: PlanStatus
    is_high_impact: bool = False
    guardrail_passed: bool = True
    guardrail_notes: str = ""
    secondary_validator_passed: bool = True
    validator_notes: str = ""
    proposed_slot: ProposedSlotDTO
    sources_cited: list[SourceCitationDTO] = Field(default_factory=list)
    items: list[ActionItemDraftDTO] = Field(default_factory=list)
    created_at: str
    undo_expires_at: int | None = None


class PlanApprovalRequestDTO(BaseDTO):
    approved_by: str = "HR Admin"
    send_immediately: bool = False
    customized_items: list[ActionItemDraftDTO] | None = None


class PlanUndoRequestDTO(BaseDTO):
    reason: str | None = "Manual cancellation by HR"
