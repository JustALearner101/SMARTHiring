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
        buffer_minutes: int = 15,
    ) -> list[dict[str, Any]]:
        """Finds non-conflicting available slots for an interviewer on target_date.

        Complies with 09:00 - 17:00 working hours, Friday prayer blackout (11:30 - 13:00),
        checks for public holidays, and strictly enforces buffer_minutes before and after events.
        """
        # 1. Check if public holiday
        holiday_stmt = select(Holiday).where(Holiday.dholiday_date == target_date)
        holiday = (await self.session.execute(holiday_stmt)).scalars().first()
        if holiday:
            return []

        # Candidate slot times in local hours
        # Mon-Thu: 09:00, 09:30, 10:00, 10:30, 11:00, 13:30, 14:00, 14:15, 14:30, 15:00, 15:30, 16:00
        # Friday: exclude 11:30 - 13:00
        candidate_times = [
            time(9, 0),
            time(9, 30),
            time(10, 0),
            time(10, 30),
            time(11, 0),
            time(13, 30),
            time(14, 0),
            time(14, 15),
            time(14, 30),
            time(15, 0),
            time(15, 30),
            time(16, 0),
        ]

        is_friday = target_date.weekday() == 4  # 4 is Friday
        tz_offset_hours = 8 if timezone_str == "WITA" else (9 if timezone_str == "WIT" else 7)
        buffer_delta = timedelta(minutes=buffer_minutes)

        # Fetch all events on target date in ONE single query to avoid 17 sequential DB round-trips
        day_start_utc = datetime.combine(target_date, time(0, 0)).replace(tzinfo=UTC) - timedelta(hours=tz_offset_hours)
        day_end_utc = datetime.combine(target_date, time(23, 59, 59)).replace(tzinfo=UTC) - timedelta(hours=tz_offset_hours)
        existing_events = list(
            await self.find_conflicts(
                user_id,
                day_start_utc - buffer_delta,
                day_end_utc + buffer_delta,
            )
        )

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

            # Check working hours bounds (09:00 - 17:00 local time)
            local_end_time = (local_dt + timedelta(minutes=duration_minutes)).time()
            if local_end_time > time(17, 0):
                continue

            # In-memory conflict check against existing events with buffer enforcement
            slot_buf_start = slot_start_utc - buffer_delta
            slot_buf_end = slot_end_utc + buffer_delta
            has_conflict = False
            for ev in existing_events:
                ev_start = (
                    ev.dscheduled_start_utc.replace(tzinfo=UTC)
                    if ev.dscheduled_start_utc.tzinfo is None
                    else ev.dscheduled_start_utc
                )
                ev_end = (
                    ev.dscheduled_end_utc.replace(tzinfo=UTC)
                    if ev.dscheduled_end_utc.tzinfo is None
                    else ev.dscheduled_end_utc
                )
                if ev_start < slot_buf_end and ev_end > slot_buf_start:
                    has_conflict = True
                    break

            if not has_conflict:
                wib_dt = slot_start_utc + timedelta(hours=7)
                wita_dt = slot_start_utc + timedelta(hours=8)
                wit_dt = slot_start_utc + timedelta(hours=9)
                available_slots.append({
                    "start_utc": slot_start_utc.isoformat(),
                    "end_utc": slot_end_utc.isoformat(),
                    "time_str": c_time.strftime("%H:%M"),
                    "formatted_wib": f"{wib_dt.strftime('%A, %d %b %Y, %H:%M')} WIB",
                    "formatted_wita": f"{wita_dt.strftime('%A, %d %b %Y, %H:%M')} WITA",
                    "formatted_wit": f"{wit_dt.strftime('%A, %d %b %Y, %H:%M')} WIT",
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
