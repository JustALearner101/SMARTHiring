from collections.abc import Sequence
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exception.CustomException import ConflictException
from app.model.CalendarModel import Holiday
from app.model.OrchestrationModel import CalendarEvent
from app.repository.BaseRepository import BaseRepository


class CalendarMatrixRepository(BaseRepository[CalendarEvent]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CalendarEvent, session)

    async def list_events(
        self,
        user_id: int | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> Sequence[CalendarEvent]:
        stmt = select(CalendarEvent).order_by(CalendarEvent.dscheduled_start_utc.asc())
        if user_id:
            stmt = stmt.where(CalendarEvent.nid_user == user_id)
        if start:
            stmt = stmt.where(CalendarEvent.dscheduled_end_utc >= start)
        if end:
            stmt = stmt.where(CalendarEvent.dscheduled_start_utc <= end)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_conflicts(
        self,
        user_id: int,
        start_utc: datetime,
        end_utc: datetime,
    ) -> Sequence[CalendarEvent]:
        stmt = select(CalendarEvent).where(
            CalendarEvent.nid_user == user_id,
            CalendarEvent.dscheduled_start_utc < end_utc,
            CalendarEvent.dscheduled_end_utc > start_utc,
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_available_slots(
        self,
        user_id: int,
        target_date: date,
        duration_minutes: int = 60,
        timezone_str: str = "WIB",
    ) -> list[dict[str, Any]]:
        """Finds non-conflicting available slots for an interviewer on target_date.

        Complies with 09:00 - 17:00 working hours, Friday prayer blackout (11:30 - 13:00),
        and checks for public holidays.
        """
        # 1. Check if public holiday
        holiday_stmt = select(Holiday).where(Holiday.dholiday_date == target_date)
        holiday = (await self.session.execute(holiday_stmt)).scalars().first()
        if holiday:
            return []

        # Candidate slot times in local hours
        # Mon-Thu: 09:00, 10:00, 11:00, 13:30, 14:00, 15:00, 16:00
        # Friday: exclude 11:30 - 13:00
        candidate_times = [
            time(9, 0),
            time(10, 0),
            time(11, 0),
            time(13, 30),
            time(14, 0),
            time(15, 0),
            time(16, 0),
        ]

        is_friday = target_date.weekday() == 4  # 4 is Friday
        tz_offset_hours = 8 if timezone_str == "WITA" else (9 if timezone_str == "WIT" else 7)

        available_slots: list[dict[str, Any]] = []

        for c_time in candidate_times:
            # Check Friday prayer overlap in local time
            if is_friday:
                # If slot starts or ends within 11:30 - 13:00
                if c_time == time(11, 0) and duration_minutes > 30:
                    continue
                if time(11, 30) <= c_time < time(13, 0):
                    continue

            # Convert to UTC
            local_dt = datetime.combine(target_date, c_time)
            slot_start_utc = local_dt.replace(tzinfo=UTC) - timedelta(hours=tz_offset_hours)
            slot_end_utc = slot_start_utc + timedelta(minutes=duration_minutes)

            # Check conflicts against database calendar events
            conflicts = await self.find_conflicts(user_id, slot_start_utc, slot_end_utc)
            if not conflicts:
                wib_dt = slot_start_utc + timedelta(hours=7)
                wita_dt = slot_start_utc + timedelta(hours=8)
                available_slots.append({
                    "start_utc": slot_start_utc.isoformat(),
                    "end_utc": slot_end_utc.isoformat(),
                    "time_str": c_time.strftime("%H:%M"),
                    "formatted_wib": f"{wib_dt.strftime('%A, %d %b %Y, %H:%M')} WIB",
                    "formatted_wita": f"{wita_dt.strftime('%A, %d %b %Y, %H:%M')} WITA",
                })

        return available_slots

    async def book_slot_atomic(
        self,
        user_id: int,
        title: str,
        start_utc: datetime,
        end_utc: datetime,
        candidate_name: str | None = None,
        event_type: str = "SCHEDULED_INTERVIEW",
        description: str | None = None,
        rule_code: str | None = None,
    ) -> CalendarEvent:
        """Atomically books a calendar slot while preventing double-booking race conditions.

        Locks conflicting user events using SELECT ... FOR UPDATE.
        Raises ConflictException if an overlapping event already exists.
        """
        conflict_stmt = (
            select(CalendarEvent)
            .where(
                CalendarEvent.nid_user == user_id,
                CalendarEvent.dscheduled_start_utc < end_utc,
                CalendarEvent.dscheduled_end_utc > start_utc,
            )
            .with_for_update()
        )
        conflicts = (await self.session.execute(conflict_stmt)).scalars().all()
        if conflicts:
            raise ConflictException(
                f"Time slot ({start_utc.isoformat()} - {end_utc.isoformat()}) conflicts with another scheduled event."
            )

        new_event = CalendarEvent(
            nid_user=user_id,
            vtitle=title,
            dscheduled_start_utc=start_utc,
            dscheduled_end_utc=end_utc,
            vevent_type=event_type,
            vcandidate_name=candidate_name,
            vrule_code=rule_code,
            vdescription=description,
        )
        self.session.add(new_event)
        await self.session.commit()
        await self.session.refresh(new_event)
        return new_event
