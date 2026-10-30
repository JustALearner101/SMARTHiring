from app.dto.BaseDTO import BaseDTO


class PresetScenarioDTO(BaseDTO):
    id: str
    label: str
    tag: str
    prompt: str
    description: str


class CommandRequestDTO(BaseDTO):
    command: str
    scenario_id: str | None = None
    thread_id: int | None = None


class InboundReplyRequestDTO(BaseDTO):
    thread_id: int | None = None
    sender_role: str = "CANDIDATE"  # "CANDIDATE" | "INTERVIEWER"
    channel: str = "whatsapp"  # "whatsapp" | "email"
    reply_text: str


class DisambiguationProfileDTO(BaseDTO):
    id: str
    name: str
    employee_id: str
    role: str
    department: str
    timezone: str
    email: str
    phone: str
    working_hours: str
    avatar_initials: str
    notes: str
