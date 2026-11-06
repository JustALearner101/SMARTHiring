from datetime import datetime
from typing import Any, Literal

from pydantic import model_validator

from app.dto.BaseDTO import BaseDTO

Timezone = Literal["WIB", "WITA", "WIT"]
PreferredChannel = Literal["whatsapp", "email"]
ApplicationStatus = Literal[
    "SCREENING",
    "ESCALATED",
    "INTERVIEW_SCHEDULED",
    "PENDING_HR_REVIEW",
    "TECHNICAL_TEST",
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
    job_position: str | None = None
    status: ApplicationStatus
    timezone: Timezone
    resume_url: str | None = None
    notes: str | None = None
    current_salary: int | None = None
    expected_salary: int | None = None
    application_cycle: int = 1
    previous_application_id: str | None = None
    created_at: datetime | str

    @model_validator(mode="before")
    @classmethod
    def _sync_positions_before(cls, data: Any) -> Any:
        if isinstance(data, dict):
            pos = data.get("applied_position") or data.get("job_position") or data.get("vjob_position")
            if pos:
                data.setdefault("applied_position", pos)
                data.setdefault("job_position", pos)
        elif hasattr(data, "vjob_position"):
            pos = data.vjob_position
            if pos and not hasattr(data, "applied_position"):
                data.applied_position = pos
        return data

    @model_validator(mode="after")
    def _sync_positions_after(self) -> "CandidateDTO":
        if not self.job_position and self.applied_position:
            self.job_position = self.applied_position
        elif not self.applied_position and self.job_position:
            self.applied_position = self.job_position
        return self


class CandidateCreateDTO(BaseDTO):
    name: str
    email: str
    phone: str
    preferred_channel: PreferredChannel = "whatsapp"
    applied_position: str | None = None
    job_position: str | None = None
    status: ApplicationStatus = "SCREENING"
    timezone: Timezone = "WIB"
    resume_url: str | None = None
    notes: str | None = None
    current_salary: int | None = None
    expected_salary: int | None = None

    @model_validator(mode="before")
    @classmethod
    def _sync_create_positions(cls, data: Any) -> Any:
        if isinstance(data, dict):
            pos = data.get("applied_position") or data.get("job_position")
            if pos:
                data.setdefault("applied_position", pos)
                data.setdefault("job_position", pos)
        return data

    @model_validator(mode="after")
    def _ensure_applied_position(self) -> "CandidateCreateDTO":
        pos = self.applied_position or self.job_position or "Software Engineer"
        self.applied_position = pos
        self.job_position = pos
        return self


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


class CandidateReapplyDTO(BaseDTO):
    applied_position: str | None = None
    notes: str | None = None
    expected_salary: int | None = None
