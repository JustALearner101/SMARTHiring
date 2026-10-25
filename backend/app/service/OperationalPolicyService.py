from datetime import time as dt_time

from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.OperationalPolicyDTO import OperationalPolicyDTO
from app.model.CalendarModel import WorkCalendar
from app.repository.OperationalPolicyRepository import OperationalPolicyRepository


class OperationalPolicyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.policy_repo = OperationalPolicyRepository(session)

    async def get_operational_policy(self) -> OperationalPolicyDTO:
        policy = await self.policy_repo.get_policy()
        return OperationalPolicyDTO(
            work_start_time=policy.twork_start.strftime("%H:%M"),
            work_end_time=policy.twork_end.strftime("%H:%M"),
            friday_prayer_start=policy.tfriday_prayer_start.strftime("%H:%M"),
            friday_prayer_end=policy.tfriday_prayer_end.strftime("%H:%M"),
            max_negotiation_rounds=policy.nmax_negotiation_rounds,
            buffer_minutes=policy.nbuffer_minutes,
            injection_guardrail_enabled=policy.binjection_guardrail_enabled,
        )

    async def get_raw_policy(self) -> WorkCalendar:
        return await self.policy_repo.get_policy()

    async def update_operational_policy(self, dto: OperationalPolicyDTO) -> OperationalPolicyDTO:
        def parse_hh_mm(val: str, default: dt_time) -> dt_time:
            try:
                parts = val.split(":")
                return dt_time(int(parts[0]), int(parts[1]))
            except (ValueError, IndexError):
                return default

        updates = {
            "twork_start": parse_hh_mm(dto.work_start_time, dt_time(9, 0)),
            "twork_end": parse_hh_mm(dto.work_end_time, dt_time(17, 0)),
            "tfriday_prayer_start": parse_hh_mm(dto.friday_prayer_start, dt_time(11, 30)),
            "tfriday_prayer_end": parse_hh_mm(dto.friday_prayer_end, dt_time(13, 0)),
            "nmax_negotiation_rounds": dto.max_negotiation_rounds,
            "nbuffer_minutes": dto.buffer_minutes,
            "binjection_guardrail_enabled": dto.injection_guardrail_enabled,
        }
        await self.policy_repo.update_policy(updates)
        return dto
