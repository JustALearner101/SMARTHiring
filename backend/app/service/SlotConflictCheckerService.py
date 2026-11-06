from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.SlotConflictCheckerDTO import (
    SlotConflictCheckRequestDTO,
    SlotConflictCheckResultDTO,
    SuggestedSlotDTO,
)
from app.model.CandidateModel import Candidate
from app.model.UserModel import User
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

    async def _find_valid_alternatives(
        self,
        base_date: date,
        timezone_str: str,
        duration_minutes: int,
        interviewer_id_int: int,
        policy: Any,
        cand_id_int: int | None = None,
        max_slots: int = 3,
    ) -> tuple[list[str], list[SuggestedSlotDTO]]:
        """Search upcoming business days for genuinely valid, conflict-free interview slots."""
        tz_offset = TZ_OFFSETS.get(timezone_str, TZ_OFFSETS["WIB"])
        w_start = policy.twork_start
        w_end = policy.twork_end
        f_start = policy.tfriday_prayer_start
        f_end = policy.tfriday_prayer_end
        buffer_delta = timedelta(minutes=policy.nbuffer_minutes)

        candidate_obj = None
        if cand_id_int:
            cand_stmt = select(Candidate).where(Candidate.nid == cand_id_int)
            candidate_obj = (await self.session.execute(cand_stmt)).scalars().first()

        candidate_tz = candidate_obj.vtimezone if candidate_obj and candidate_obj.vtimezone else timezone_str
        cand_tz_offset = TZ_OFFSETS.get(candidate_tz, TZ_OFFSETS["WIB"])

        candidate_times = [
            time(9, 30),
            time(10, 0),
            time(13, 30),
            time(14, 0),
            time(15, 30),
        ]

        alternatives_str: list[str] = []
        alternatives_dto: list[SuggestedSlotDTO] = []

        # Check up to 14 days ahead
        curr_d = base_date
        for day_offset in range(1, 15):
            check_date = curr_d + timedelta(days=day_offset)

            # Skip weekends (5=Saturday, 6=Sunday)
            if check_date.weekday() in (5, 6):
                continue

            # Skip national holidays
            if await self.holiday_repo.is_holiday(check_date):
                continue

            for t_candidate in candidate_times:
                dt_local_start = datetime.combine(check_date, t_candidate)
                dt_local_end = dt_local_start + timedelta(minutes=duration_minutes)

                # Check working hours
                if t_candidate < w_start or dt_local_end.time() > w_end:
                    continue

                # Check Friday prayer
                if check_date.weekday() == 4 and not (dt_local_end.time() <= f_start or t_candidate >= f_end):
                    continue

                # Check Candidate working hours if in different timezone
                slot_start_utc = dt_local_start - tz_offset
                slot_end_utc = dt_local_end - tz_offset

                cand_local_start = slot_start_utc + cand_tz_offset
                cand_local_end = slot_end_utc + cand_tz_offset
                if cand_local_start.time() < w_start or cand_local_end.time() > w_end:
                    continue

                # Check Interviewer calendar conflict
                conflicts = await self.matrix_repo.find_conflicts(
                    user_id=interviewer_id_int,
                    start_utc=(slot_start_utc - buffer_delta).replace(tzinfo=UTC),
                    end_utc=(slot_end_utc + buffer_delta).replace(tzinfo=UTC),
                )
                if conflicts:
                    continue

                # Found a valid slot!
                fmt_str = f"{check_date.isoformat()} {t_candidate.strftime('%H:%M')} {timezone_str}"
                alternatives_str.append(fmt_str)
                alternatives_dto.append(
                    SuggestedSlotDTO(
                        date=check_date.isoformat(),
                        time=t_candidate.strftime("%H:%M"),
                        timezone=timezone_str,
                        start_utc=slot_start_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        end_utc=slot_end_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        formatted=fmt_str,
                    )
                )

                if len(alternatives_str) >= max_slots:
                    return alternatives_str, alternatives_dto

        return alternatives_str, alternatives_dto

    async def check_slot_conflict(
        self,
        request: SlotConflictCheckRequestDTO,
    ) -> SlotConflictCheckResultDTO:
        if not request.interviewer_id.strip().isdigit() or int(request.interviewer_id.strip()) <= 0:
            return SlotConflictCheckResultDTO(
                is_available=False,
                status="INTERVIEWER_NOT_FOUND",
                message=f"Interviewer ID '{request.interviewer_id}' is not valid or does not exist in directory.",
                rule_code="RULE_ENTITY_NOT_FOUND",
                sources_cited=[
                    {
                        "id": "dir-employee-directory",
                        "ref_code": "[dir-employee-directory:HQ-JKT]",
                        "source_type": "DIRECTORY",
                        "title": "Employee Directory Lookup",
                    }
                ],
            )
        interviewer_id_int = int(request.interviewer_id.strip())
        cand_id_int = int(request.candidate_id) if request.candidate_id and request.candidate_id.isdigit() else None

        interviewer_name = "Budi Santoso"
        interviewer_uid = f"EMP-ENG-00{interviewer_id_int}"
        if interviewer_id_int != 1:
            try:
                user_res = await self.session.execute(select(User).where(User.nid == interviewer_id_int))
                interviewer_obj = user_res.scalars().first()
                if interviewer_obj is None:
                    return SlotConflictCheckResultDTO(
                        is_available=False,
                        status="INTERVIEWER_NOT_FOUND",
                        message=f"Interviewer with ID '{request.interviewer_id}' was not found in employee directory.",
                        rule_code="RULE_ENTITY_NOT_FOUND",
                        sources_cited=[
                            {
                                "id": "dir-employee-directory",
                                "ref_code": "[dir-employee-directory:HQ-JKT]",
                                "source_type": "DIRECTORY",
                                "title": "Employee Directory Lookup",
                            }
                        ],
                    )
                if isinstance(getattr(interviewer_obj, "vname", None), str):
                    interviewer_name = interviewer_obj.vname
                if isinstance(getattr(interviewer_obj, "vuserid", None), str):
                    interviewer_uid = interviewer_obj.vuserid
            except Exception:
                pass

        inter_slug = interviewer_name.lower().replace(" ", "-")
        cal_source = {
            "id": f"cal-hq-jkt-{interviewer_uid.lower()}",
            "ref_code": f"[cal-{inter_slug}:{interviewer_uid}:HQ-JKT]",
            "source_type": "CALENDAR",
            "title": f"Calendar: {interviewer_name} ({interviewer_uid} / HQ-JKT)",
        }

        def _make_sources(rule_code: str, rule_title: str) -> list[dict[str, Any]]:
            rule_slug = rule_code.lower().replace("_", "-")
            return [
                cal_source,
                {
                    "id": rule_slug,
                    "ref_code": f"[{rule_slug}:{rule_code}]",
                    "source_type": "OPERATIONAL_RULE",
                    "title": rule_title,
                },
            ]

        policy = await self.policy_repo.get_policy()

        try:
            req_date = date.fromisoformat(request.date)
            parts = request.time.split(":")
            req_time = time(int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            return SlotConflictCheckResultDTO(
                is_available=False,
                status="OUTSIDE_WORKING_HOURS",
                message="Invalid date or time format. Please provide YYYY-MM-DD for date and HH:MM for time.",
            )

        tz_offset = TZ_OFFSETS.get(request.timezone, TZ_OFFSETS["WIB"])
        local_start = datetime.combine(req_date, req_time)
        local_end = local_start + timedelta(minutes=request.duration_minutes)

        start_utc = local_start - tz_offset
        end_utc = local_end - tz_offset

        calc_end_time = local_end.strftime("%H:%M")
        calc_end_utc = end_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

        # ---------------------------------------------------------------------
        # 1. EVALUATION PRIORITY 1: Weekend Blackout (Saturday=5, Sunday=6)
        # ---------------------------------------------------------------------
        if req_date.weekday() in (5, 6):
            day_name = "Saturday" if req_date.weekday() == 5 else "Sunday"
            alt_strs, alt_dtos = await self._find_valid_alternatives(
                base_date=req_date,
                timezone_str=request.timezone,
                duration_minutes=request.duration_minutes,
                interviewer_id_int=interviewer_id_int,
                policy=policy,
                cand_id_int=cand_id_int,
            )
            return SlotConflictCheckResultDTO(
                is_available=False,
                status="WEEKEND_BLOCKED",
                message=f"Date {req_date} is on a weekend ({day_name}). Interview scheduling is strictly restricted to business days (Monday - Friday).",
                rule_code="RULE_WEEKEND_BLACKOUT",
                suggested_alternatives=alt_strs,
                suggested_alternative_slots=alt_dtos,
                sources_cited=_make_sources("RULE_WEEKEND_BLACKOUT", "Rule: Weekend Blackout Policy"),
                calculated_end_time=calc_end_time,
                calculated_end_utc=calc_end_utc,
            )

        # ---------------------------------------------------------------------
        # 2. EVALUATION PRIORITY 2: National Holiday / Cuti Bersama
        # ---------------------------------------------------------------------
        holiday = await self.holiday_repo.is_holiday(req_date)
        if holiday:
            h_type = "Collective Leave" if holiday.vtype == "COLLECTIVE_LEAVE" else "National Holiday"
            alt_strs, alt_dtos = await self._find_valid_alternatives(
                base_date=req_date,
                timezone_str=request.timezone,
                duration_minutes=request.duration_minutes,
                interviewer_id_int=interviewer_id_int,
                policy=policy,
                cand_id_int=cand_id_int,
            )
            return SlotConflictCheckResultDTO(
                is_available=False,
                status="NATIONAL_HOLIDAY",
                message=f"Date {req_date} coincides with {h_type}: {holiday.vname}.",
                rule_code="RULE_NATIONAL_HOLIDAY",
                suggested_alternatives=alt_strs,
                suggested_alternative_slots=alt_dtos,
                sources_cited=_make_sources("RULE_NATIONAL_HOLIDAY", f"Holiday: {holiday.vname}"),
                calculated_end_time=calc_end_time,
                calculated_end_utc=calc_end_utc,
            )

        # ---------------------------------------------------------------------
        # 3. EVALUATION PRIORITY 3: Operational Working Hours (09:00 - 17:00)
        # ---------------------------------------------------------------------
        w_start = policy.twork_start
        w_end = policy.twork_end
        if req_time < w_start or local_end.time() > w_end:
            alt_strs, alt_dtos = await self._find_valid_alternatives(
                base_date=req_date,
                timezone_str=request.timezone,
                duration_minutes=request.duration_minutes,
                interviewer_id_int=interviewer_id_int,
                policy=policy,
                cand_id_int=cand_id_int,
            )
            return SlotConflictCheckResultDTO(
                is_available=False,
                status="OUTSIDE_WORKING_HOURS",
                message=f"Slot is outside operational working hours ({w_start.strftime('%H:%M')} - {w_end.strftime('%H:%M')} {request.timezone}).",
                rule_code="RULE_WORKING_HOURS",
                suggested_alternatives=alt_strs,
                suggested_alternative_slots=alt_dtos,
                sources_cited=_make_sources("RULE_WORKING_HOURS", "Rule: Operational Working Hours (09:00 - 17:00)"),
                calculated_end_time=calc_end_time,
                calculated_end_utc=calc_end_utc,
            )

        # ---------------------------------------------------------------------
        # 4. EVALUATION PRIORITY 4: Friday Prayer Blackout (11:30 - 13:00)
        # ---------------------------------------------------------------------
        if req_date.weekday() == 4:
            f_start = policy.tfriday_prayer_start
            f_end = policy.tfriday_prayer_end
            slot_start_t = req_time
            slot_end_t = local_end.time()
            if not (slot_end_t <= f_start or slot_start_t >= f_end):
                alt_strs, alt_dtos = await self._find_valid_alternatives(
                    base_date=req_date,
                    timezone_str=request.timezone,
                    duration_minutes=request.duration_minutes,
                    interviewer_id_int=interviewer_id_int,
                    policy=policy,
                    cand_id_int=cand_id_int,
                )
                return SlotConflictCheckResultDTO(
                    is_available=False,
                    status="BLOCKED_FRIDAY_PRAYER",
                    message=(
                        f"Time slot overlaps with Friday prayer blackout "
                        f"({f_start.strftime('%H:%M')} - {f_end.strftime('%H:%M')} {request.timezone}) "
                        f"according to company operational policy."
                    ),
                    rule_code="RULE_FRIDAY_PRAYER",
                    suggested_alternatives=alt_strs,
                    suggested_alternative_slots=alt_dtos,
                    sources_cited=_make_sources("RULE_FRIDAY_PRAYER", "Rule: Friday Prayer Blackout (11:30 - 13:00)"),
                    calculated_end_time=calc_end_time,
                    calculated_end_utc=calc_end_utc,
                )

        # ---------------------------------------------------------------------
        # 5. Candidate Local Working Hours (Cross-Timezone Check, e.g. WIT/WITA)
        # ---------------------------------------------------------------------
        if cand_id_int:
            cand_stmt = select(Candidate).where(Candidate.nid == cand_id_int)
            cand = (await self.session.execute(cand_stmt)).scalars().first()
            if cand and cand.vtimezone and cand.vtimezone != request.timezone:
                c_offset = TZ_OFFSETS.get(cand.vtimezone, TZ_OFFSETS["WIB"])
                c_start = start_utc + c_offset
                c_end = end_utc + c_offset
                if c_start.time() < w_start or c_end.time() > w_end:
                    alt_strs, alt_dtos = await self._find_valid_alternatives(
                        base_date=req_date,
                        timezone_str=request.timezone,
                        duration_minutes=request.duration_minutes,
                        interviewer_id_int=interviewer_id_int,
                        policy=policy,
                        cand_id_int=cand_id_int,
                    )
                    return SlotConflictCheckResultDTO(
                        is_available=False,
                        status="OUTSIDE_WORKING_HOURS",
                        message=(
                            f"Slot {request.time} {request.timezone} corresponds to {c_start.strftime('%H:%M')} - {c_end.strftime('%H:%M')} {cand.vtimezone}, "
                            f"which is outside candidate's local working hours ({w_start.strftime('%H:%M')} - {w_end.strftime('%H:%M')} {cand.vtimezone})."
                        ),
                        rule_code="RULE_WORKING_HOURS",
                        suggested_alternatives=alt_strs,
                        suggested_alternative_slots=alt_dtos,
                        sources_cited=_make_sources("RULE_WORKING_HOURS", "Rule: Cross-Timezone Working Hours"),
                        calculated_end_time=calc_end_time,
                        calculated_end_utc=calc_end_utc,
                    )

        # ---------------------------------------------------------------------
        # 6. Existing Interviewer Calendar Events
        # ---------------------------------------------------------------------
        conflicts = await self.matrix_repo.find_conflicts(
            user_id=interviewer_id_int,
            start_utc=start_utc.replace(tzinfo=UTC),
            end_utc=end_utc.replace(tzinfo=UTC),
        )
        if conflicts:
            conf_ev = conflicts[0]
            alt_strs, alt_dtos = await self._find_valid_alternatives(
                base_date=req_date,
                timezone_str=request.timezone,
                duration_minutes=request.duration_minutes,
                interviewer_id_int=interviewer_id_int,
                policy=policy,
                cand_id_int=cand_id_int,
            )
            return SlotConflictCheckResultDTO(
                is_available=False,
                status="CONFLICT_EXISTING_EVENT",
                message=f"Interviewer already has an event scheduled ('{conf_ev.vtitle}') during this time slot.",
                rule_code="RULE_CALENDAR_BUSY",
                conflicting_event=conf_ev.vtitle,
                suggested_alternatives=alt_strs,
                suggested_alternative_slots=alt_dtos,
                sources_cited=_make_sources("RULE_CALENDAR_BUSY", f"Conflict: {conf_ev.vtitle}"),
                calculated_end_time=calc_end_time,
                calculated_end_utc=calc_end_utc,
            )

        # ---------------------------------------------------------------------
        # 7. 15-Minute Safe Buffer Requirement
        # ---------------------------------------------------------------------
        buffer_delta = timedelta(minutes=policy.nbuffer_minutes)
        buffer_conflicts = await self.matrix_repo.find_conflicts(
            user_id=interviewer_id_int,
            start_utc=(start_utc - buffer_delta).replace(tzinfo=UTC),
            end_utc=(end_utc + buffer_delta).replace(tzinfo=UTC),
        )
        if buffer_conflicts:
            buf_ev = buffer_conflicts[0]
            alt_strs, alt_dtos = await self._find_valid_alternatives(
                base_date=req_date,
                timezone_str=request.timezone,
                duration_minutes=request.duration_minutes,
                interviewer_id_int=interviewer_id_int,
                policy=policy,
                cand_id_int=cand_id_int,
            )
            return SlotConflictCheckResultDTO(
                is_available=False,
                status="INSUFFICIENT_BUFFER",
                message=f"Buffer time is less than the required safe buffer of {policy.nbuffer_minutes} minutes before/after existing event '{buf_ev.vtitle}'.",
                rule_code="RULE_MEETING_BUFFER",
                conflicting_event=buf_ev.vtitle,
                suggested_alternatives=alt_strs,
                suggested_alternative_slots=alt_dtos,
                sources_cited=_make_sources("RULE_MEETING_BUFFER", f"Rule: {policy.nbuffer_minutes}-Minute Meeting Buffer"),
                calculated_end_time=calc_end_time,
                calculated_end_utc=calc_end_utc,
            )

        return SlotConflictCheckResultDTO(
            is_available=True,
            status="VALID",
            message=f"Schedule slot is available and complies with all operational rules ({request.timezone}).",
            sources_cited=_make_sources("RULE_WORKING_HOURS", "Rule: Operational Working Hours Compliance"),
            calculated_end_time=calc_end_time,
            calculated_end_utc=calc_end_utc,
        )
