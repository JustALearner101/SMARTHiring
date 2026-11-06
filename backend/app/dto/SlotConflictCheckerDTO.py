from typing import Any, Literal

from pydantic import Field

from app.dto.BaseDTO import BaseDTO


class SuggestedSlotDTO(BaseDTO):
    date: str
    time: str
    timezone: str
    start_utc: str
    end_utc: str
    formatted: str


class SlotConflictCheckRequestDTO(BaseDTO):
    interviewer_id: str
    candidate_id: str | None = None
    date: str
    time: str
    duration_minutes: int = 60
    timezone: Literal["WIB", "WITA", "WIT"] = "WIB"


class SlotConflictCheckResultDTO(BaseDTO):
    is_available: bool
    status: Literal[
        "VALID",
        "CONFLICT_EXISTING_EVENT",
        "BLOCKED_FRIDAY_PRAYER",
        "OUTSIDE_WORKING_HOURS",
        "INSUFFICIENT_BUFFER",
        "NATIONAL_HOLIDAY",
        "WEEKEND_BLOCKED",
        "INTERVIEWER_NOT_FOUND",
    ]
    message: str
    rule_code: str | None = None
    conflicting_event: str | None = None
    suggested_alternatives: list[str] = Field(default_factory=list)
    suggested_alternative_slots: list[SuggestedSlotDTO] = Field(default_factory=list)
    sources_cited: list[dict[str, Any]] = Field(default_factory=list)
    calculated_end_time: str | None = None
    calculated_end_utc: str | None = None
