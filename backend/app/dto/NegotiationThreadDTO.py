from typing import Literal

from pydantic import Field

from app.dto.BaseDTO import BaseDTO

ThreadStatus = Literal[
    "NEGOTIATING",
    "SCHEDULED",
    "DEADLOCK_ESCALATED",
    "EXPIRED",
]


class ThreadMessageDTO(BaseDTO):
    id: str
    round_number: int
    sender_role: Literal["AI_ORCHESTRATOR", "CANDIDATE", "HR_ADMIN"]
    sender_name: str
    channel: Literal["whatsapp", "email"]
    sent_at: str
    content: str
    proposed_slot: str | None = None
    source_citation: str | None = None
    is_rejection: bool | None = False


class NegotiationThreadDTO(BaseDTO):
    id: str
    candidate_id: str
    candidate_name: str
    candidate_channel: Literal["whatsapp", "email"]
    candidate_position: str
    candidate_phone: str | None = None
    candidate_email: str | None = None
    interviewer_id: str
    interviewer_name: str
    interviewer_role: str
    interviewer_dept: str
    interviewer_timezone: Literal["WIB", "WITA", "WIT"]
    current_round: int
    max_rounds: int = 3
    status: ThreadStatus
    last_activity_at: str
    last_message_preview: str
    deadline_at: str
    messages: list[ThreadMessageDTO] = Field(default_factory=list)
    escalation_reason: str | None = None
    agreed_slot: str | None = None
