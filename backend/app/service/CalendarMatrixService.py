from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.CalendarMatrixDTO import CalendarMatrixEventDTO
from app.repository.CalendarMatrixRepository import CalendarMatrixRepository


class CalendarMatrixService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.matrix_repo = CalendarMatrixRepository(session)

    async def list_calendar_events(
        self,
        user_id: str | None = None,
        start_iso: str | None = None,
        end_iso: str | None = None,
    ) -> list[CalendarMatrixEventDTO]:
        u_id = int(user_id) if user_id and user_id.isdigit() else None
        s_dt = datetime.fromisoformat(start_iso) if start_iso else None
        e_dt = datetime.fromisoformat(end_iso) if end_iso else None

        events = await self.matrix_repo.list_events(user_id=u_id, start=s_dt, end=e_dt)
        return [
            CalendarMatrixEventDTO(
                id=str(ev.nid),
                interviewer_id=str(ev.nid_user),
                title=ev.vtitle,
                start=ev.dscheduled_start_utc.isoformat(),
                end=ev.dscheduled_end_utc.isoformat(),
                event_type=ev.vevent_type,  # type: ignore[arg-type]
                candidate_name=ev.vcandidate_name,
                rule_code=ev.vrule_code,
                description=ev.vdescription,
            )
            for ev in events
        ]
