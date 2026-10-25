from typing import Any, Literal

from pydantic import Field

from app.dto.BaseDTO import BaseDTO


class SimulatedEmailDTO(BaseDTO):
    id: str
    thread_id: str
    sender_name: str
    sender_email: str
    sender_role: str
    recipient_name: str
    recipient_email: str
    subject: str
    body_text: str
    sent_at: str
    is_read: bool = False
    is_starred: bool = False
    folder: Literal["inbox", "sent", "starred"] = "inbox"
    tags: list[Literal["Invitation", "Reschedule", "Confirmation", "High-Impact"]] = Field(default_factory=list)
    meeting_details: dict[str, Any] | None = None
