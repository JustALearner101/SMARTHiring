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
