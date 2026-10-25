from typing import Literal

from app.dto.BaseDTO import BaseDTO

CalendarEventType = Literal[
    "SCHEDULED_INTERVIEW",
    "TEAM_MEETING",
    "FRIDAY_PRAYER_BLOCK",
    "OUT_OF_OFFICE",
    "BUFFER_BLOCK",
]


class CalendarMatrixEventDTO(BaseDTO):
    id: str
    interviewer_id: str
    title: str
    start: str
    end: str
    event_type: CalendarEventType
    candidate_name: str | None = None
    rule_code: str | None = None
    description: str | None = None
