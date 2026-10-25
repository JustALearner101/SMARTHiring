from typing import Any, Literal

from app.dto.BaseDTO import BaseDTO

SimulatorChannel = Literal["email", "whatsapp"]
MessageSenderRole = Literal["candidate", "interviewer", "bot", "system"]
DeliveryStatus = Literal["sending", "sent", "delivered", "read"]
QuickPresetType = Literal["confirm", "reschedule", "friday_conflict", "prompt_injection"]


class SimulatedWhatsAppMessageDTO(BaseDTO):
    id: str
    thread_id: str
    sender: MessageSenderRole
    sender_name: str
    text: str
    timestamp: str
    status: DeliveryStatus
    is_guardrail_flagged: bool = False
    guardrail_reason: str | None = None
    action_trigger: Literal[
        "CONFIRM_SCHEDULE",
        "REQUEST_RESCHEDULE",
        "REJECT_INVITATION",
        "SECURITY_ALERT",
    ] | None = None
    action_metadata: dict[str, Any] | None = None


class QuickReplyPresetDTO(BaseDTO):
    id: str
    preset_type: QuickPresetType
    label: str
    badge: str
    badge_variant: Literal["success", "warning", "danger", "info"]
    description: str
    payload_text: str


class SimulatorNotificationDTO(BaseDTO):
    id: str
    type: Literal["triage_triggered", "guardrail_blocked", "confirmed", "scheduled"]
    title: str
    message: str
    timestamp: str
    action_url: str | None = None
