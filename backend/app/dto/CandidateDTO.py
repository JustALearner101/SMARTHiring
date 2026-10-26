from datetime import datetime
from typing import Literal

from app.dto.BaseDTO import BaseDTO

Timezone = Literal["WIB", "WITA", "WIT"]
PreferredChannel = Literal["whatsapp", "email"]
ApplicationStatus = Literal[
    "SCREENING",
    "ESCALATED",
    "INTERVIEW_SCHEDULED",
    "COMPLETED",
    "OFFERED",
    "REJECTED",
]


class CandidateDTO(BaseDTO):
    id: str
    candidate_code: str
    name: str
    email: str
    phone: str
    preferred_channel: PreferredChannel
    applied_position: str
    status: ApplicationStatus
    timezone: Timezone
    resume_url: str | None = None
    notes: str | None = None
    current_salary: int | None = None
    expected_salary: int | None = None
    created_at: datetime | str


class CandidateCreateDTO(BaseDTO):
    name: str
    email: str
    phone: str
    preferred_channel: PreferredChannel = "whatsapp"
    applied_position: str
    status: ApplicationStatus = "SCREENING"
    timezone: Timezone = "WIB"
    resume_url: str | None = None
    notes: str | None = None
    current_salary: int | None = None
    expected_salary: int | None = None


class CandidateUpdateDTO(BaseDTO):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    preferred_channel: PreferredChannel | None = None
    applied_position: str | None = None
    status: ApplicationStatus | None = None
    timezone: Timezone | None = None
    resume_url: str | None = None
    notes: str | None = None
    current_salary: int | None = None
    expected_salary: int | None = None
