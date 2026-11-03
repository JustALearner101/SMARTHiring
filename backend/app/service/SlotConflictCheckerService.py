from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.SlotConflictCheckerDTO import (
    SlotConflictCheckRequestDTO,
    SlotConflictCheckResultDTO,
)
from app.model.CandidateModel import Candidate
from app.repository.CalendarMatrixRepository import CalendarMatrixRepository
from app.repository.HolidayRepository import HolidayRepository
from app.repository.OperationalPolicyRepository import OperationalPolicyRepository

TZ_OFFSETS = {
    "WIB": timedelta(hours=7),
    "WITA": timedelta(hours=8),
    "WIT": timedelta(hours=9),
}


class SlotConflictCheckerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.policy_repo = OperationalPolicyRepository(session)
        self.holiday_repo = HolidayRepository(session)
        self.matrix_repo = CalendarMatrixRepository(session)

    async def check_slot_conflict(
        self,
        request: SlotConflictCheckRequestDTO,
    ) -> SlotConflictCheckResultDTO:
        interviewer_id_int = int(request.interviewer_id) if request.interviewer_id.isdigit() else 1
        policy = await self.policy_repo.get_policy()

        try:
            req_date = date.fromisoformat(request.date)
            parts = request.time.split(":")
            req_time = time(int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            return SlotConflictCheckResultDTO(
                is_available=False,
                status="OUTSIDE_WORKING_HOURS",
                message="Invalid date or time format.",
            )

        tz_offset = TZ_OFFSETS.get(request.timezone, TZ_OFFSETS["WIB"])
        local_start = datetime.combine(req_date, req_time)
        local_end = local_start + timedelta(minutes=request.duration_minutes)

        start_utc = local_start - tz_offset
        end_utc = local_end - tz_offset

        # 1. Check Working Hours (09:00 - 17:00 by policy)
        w_start = policy.twork_start
        w_end = policy.twork_end
        if req_time < w_start or local_end.time() > w_end:
            return SlotConflictCheckResultDTO(
                is_available=False,
                status="OUTSIDE_WORKING_HOURS",
                message=f"Slot is outside operational working hours ({w_start.strftime('%H:%M')} - {w_end.strftime('%H:%M')} {request.timezone}).",
                rule_code="[rule-working-hours]",
                suggested_alternatives=[
                    f"{request.date} 10:00 {request.timezone}",
                    f"{request.date} 14:00 {request.timezone}",
                ],
            )

        # Check Candidate Local Working Hours if candidate timezone is different (e.g. WIT)
        if request.candidate_id:
            cand_id_int = int(request.candidate_id) if request.candidate_id.isdigit() else None
            if cand_id_int:
                cand_stmt = select(Candidate).where(Candidate.nid == cand_id_int)
                cand = (await self.session.execute(cand_stmt)).scalars().first()
                if cand and cand.vtimezone and cand.vtimezone != request.timezone:
                    c_offset = TZ_OFFSETS.get(cand.vtimezone, TZ_OFFSETS["WIB"])
                    c_start = start_utc + c_offset
                    c_end = end_utc + c_offset
                    if c_start.time() < w_start or c_end.time() > w_end:
                        return SlotConflictCheckResultDTO(
                            is_available=False,
                            status="OUTSIDE_WORKING_HOURS",
                            message=(
                                f"Slot {request.time} {request.timezone} corresponds to {c_start.strftime('%H:%M')} - {c_end.strftime('%H:%M')} {cand.vtimezone}, "
                                f"which is outside candidate's local working hours ({w_start.strftime('%H:%M')} - {w_end.strftime('%H:%M')} {cand.vtimezone})."
                            ),
                            rule_code="[rule-working-hours]",
                            suggested_alternatives=[
                                f"{request.date} 10:00 {request.timezone} (12:00 {cand.vtimezone})",
                                f"{request.date} 14:00 {request.timezone} (16:00 {cand.vtimezone})",
                            ],
                        )

        # 2. Check Friday Prayer Blackout (11:30 - 13:00 every Friday)
        if req_date.weekday() == 4:
            f_start = policy.tfriday_prayer_start
            f_end = policy.tfriday_prayer_end
            slot_start_t = req_time
            slot_end_t = local_end.time()
            if not (slot_end_t <= f_start or slot_start_t >= f_end):
                return SlotConflictCheckResultDTO(
                    is_available=False,
                    status="BLOCKED_FRIDAY_PRAYER",
                    message=(
                        f"Time slot overlaps with Friday prayer blackout "
                        f"({f_start.strftime('%H:%M')} - {f_end.strftime('%H:%M')} {request.timezone}) "
                        f"according to company operational policy."
                    ),
                    rule_code="[rule-jumatan]",
                    suggested_alternatives=[
                        f"{request.date} 09:30 {request.timezone}",
                        f"{request.date} 13:30 {request.timezone}",
                        f"{request.date} 15:00 {request.timezone}",
                    ],
                )

        # 3. Check National Holiday / Cuti Bersama
        holiday = await self.holiday_repo.is_holiday(req_date)
        if holiday:
            h_type = "Collective Leave" if holiday.vtype == "COLLECTIVE_LEAVE" else "National Holiday"
            return SlotConflictCheckResultDTO(
                is_available=False,
                status="OUTSIDE_WORKING_HOURS",
                message=f"Date {req_date} coincides with {h_type}: {holiday.vname}.",
                rule_code="[rule-holiday]",
                suggested_alternatives=[
                    (req_date + timedelta(days=1)).strftime("%Y-%m-%d") + f" 10:00 {request.timezone}",
                    (req_date + timedelta(days=2)).strftime("%Y-%m-%d") + f" 14:00 {request.timezone}",
                ],
            )

        # 4. Check Existing Interviewer Calendar Events
        conflicts = await self.matrix_repo.find_conflicts(
            user_id=interviewer_id_int,
            start_utc=start_utc.replace(tzinfo=UTC),
            end_utc=end_utc.replace(tzinfo=UTC),
        )
        if conflicts:
            conf_ev = conflicts[0]
            return SlotConflictCheckResultDTO(
                is_available=False,
                status="CONFLICT_EXISTING_EVENT",
                message=f"Interviewer already has an event scheduled ('{conf_ev.vtitle}') during this time slot.",
                rule_code="[cal-interviewer-busy]",
                conflicting_event=conf_ev.vtitle,
                suggested_alternatives=[
                    (local_end + timedelta(minutes=policy.nbuffer_minutes)).strftime("%H:%M") + f" {request.timezone}",
                    (local_start - timedelta(minutes=60 + policy.nbuffer_minutes)).strftime("%H:%M") + f" {request.timezone}",
                ],
            )

        # 5. Check 15-Minute Buffer Requirement
        buffer_delta = timedelta(minutes=policy.nbuffer_minutes)
        buffer_conflicts = await self.matrix_repo.find_conflicts(
            user_id=interviewer_id_int,
            start_utc=(start_utc - buffer_delta).replace(tzinfo=UTC),
            end_utc=(end_utc + buffer_delta).replace(tzinfo=UTC),
        )
        if buffer_conflicts:
            return SlotConflictCheckResultDTO(
                is_available=False,
                status="INSUFFICIENT_BUFFER",
                message=f"Buffer time is less than the required safe buffer of {policy.nbuffer_minutes} minutes before/after another event.",
                rule_code="[rule-buffer-window]",
                suggested_alternatives=[
                    (local_end + buffer_delta).strftime("%H:%M") + f" {request.timezone}",
                ],
            )

        return SlotConflictCheckResultDTO(
            is_available=True,
            status="VALID",
            message=f"Schedule slot is available and complies with all operational rules ({request.timezone}).",
        )
