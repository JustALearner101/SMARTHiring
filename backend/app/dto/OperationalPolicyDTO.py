from typing import Literal

from app.dto.BaseDTO import BaseDTO

Timezone = Literal["WIB", "WITA", "WIT"]


class OperationalPolicyDTO(BaseDTO):
    work_start_time: str = "09:00"
    work_end_time: str = "17:00"
    friday_prayer_start: str = "11:30"
    friday_prayer_end: str = "13:00"
    max_negotiation_rounds: int = 3
    buffer_minutes: int = 15
    injection_guardrail_enabled: bool = True
