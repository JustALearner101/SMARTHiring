from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.middleware.RateLimiterMiddleware import rate_limiter_instance
from app.model.CalendarModel import WorkCalendar
from app.model.OrchestrationModel import CalendarEvent
from app.model.UserModel import User

CHECK = "/api/v1/slotConflictChecker/check"
WIB = timedelta(hours=7)


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    rate_limiter_instance.reset()
    yield
    rate_limiter_instance.reset()


def _weekday_on_or_after(start: date, weekday: int) -> date:
    d = start
    while d.weekday() != weekday:
        d += timedelta(days=1)
    return d


TUESDAY = _weekday_on_or_after(date(2040, 3, 1), 1)
FRIDAY = _weekday_on_or_after(date(2040, 3, 1), 4)


@pytest.fixture
async def interviewer_id(test_session: AsyncSession) -> int:
    return (await test_session.execute(select(User.nid).where(User.vusername == "budi.santoso"))).scalar_one()


@pytest.fixture
async def book(test_session: AsyncSession, interviewer_id: int) -> AsyncGenerator:
    """Create a booking for the interviewer (local WIB start/end) and delete it after the test."""
    created: list[int] = []

    async def _book(day: date, start: str, end: str) -> None:
        def utc(hhmm: str) -> datetime:
            h, m = (int(x) for x in hhmm.split(":"))
            return datetime(day.year, day.month, day.day, h, m, tzinfo=UTC) - WIB

        ev = CalendarEvent(
            nid_user=interviewer_id,
            vtitle="QA existing meeting",
            dscheduled_start_utc=utc(start),
            dscheduled_end_utc=utc(end),
            vevent_type="SCHEDULED_INTERVIEW",
            vrule_code="[qa-blocker]",
        )
        test_session.add(ev)
        await test_session.commit()
        created.append(ev.nid)

    yield _book
    test_session.expire_all()
    for ev_id in created:
        row = await test_session.get(CalendarEvent, ev_id)
        if row:
            await test_session.delete(row)
    await test_session.commit()


async def _check(client: AsyncClient, interviewer: int, day: date, start: str, minutes: int = 60, tz: str = "WIB") -> dict:
    res = await client.post(
        CHECK,
        json={
            "interviewer_id": str(interviewer),
            "date": day.isoformat(),
            "time": start,
            "duration_minutes": minutes,
            "timezone": tz,
        },
    )
    assert res.status_code == 200, res.text
    return res.json()["data"]


# CAL-01 / 02 (API side) ---------------------------------------------------- #
async def test_cal01_matrix_events_endpoint_returns_events_for_hr(client: AsyncClient, book, interviewer_id: int):
    await book(TUESDAY, "10:00", "11:00")

    res = await client.get("/api/v1/calendarMatrix/events", params={"user_id": str(interviewer_id)})

    assert res.status_code == 200
    events = res.json()["data"]
    assert any(e["title"] == "QA existing meeting" for e in events)
    assert all({"start", "end", "event_type", "interviewer_id"} <= set(e) for e in events)


async def test_cal02_interviewer_role_can_read_calendar_matrix(client: AsyncClient):
    res = await client.get("/api/v1/calendarMatrix/events", headers={"X-Demo-Role": "INTERVIEWER"})
    assert res.status_code == 200


# CAL-03 .. 06 working hours ------------------------------------------------ #
async def test_cal03_slot_inside_working_hours_is_available(client: AsyncClient, interviewer_id: int):
    result = await _check(client, interviewer_id, TUESDAY, "10:00")

    assert result["is_available"] is True and result["status"] == "VALID"


@pytest.mark.parametrize(("start", "label"), [("08:30", "before work start"), ("16:30", "crosses work end")])
async def test_cal04_05_outside_working_hours_is_rejected_with_alternatives(
    client: AsyncClient, interviewer_id: int, start: str, label: str
):
    result = await _check(client, interviewer_id, TUESDAY, start)

    assert result["is_available"] is False, label
    assert result["status"] == "OUTSIDE_WORKING_HOURS"
    assert result["rule_code"] == "[rule-working-hours]"
    assert result["suggested_alternatives"]


@pytest.mark.parametrize("start", ["09:00", "16:00"])
async def test_cal06_work_hour_boundaries_are_inclusive(client: AsyncClient, interviewer_id: int, start: str):
    result = await _check(client, interviewer_id, TUESDAY, start)

    assert result["status"] == "VALID", result


# CAL-07 .. 09 Friday prayer ------------------------------------------------ #
@pytest.mark.parametrize("start", ["12:00", "11:00"])
async def test_cal07_08_friday_prayer_window_is_blocked(client: AsyncClient, interviewer_id: int, start: str):
    result = await _check(client, interviewer_id, FRIDAY, start)

    assert result["status"] == "BLOCKED_FRIDAY_PRAYER"
    assert result["rule_code"] == "[rule-jumatan]"
    assert result["suggested_alternatives"]


@pytest.mark.parametrize("start", ["13:00", "10:30"])
async def test_cal09_friday_prayer_boundaries_are_exclusive(client: AsyncClient, interviewer_id: int, start: str):
    result = await _check(client, interviewer_id, FRIDAY, start)

    assert result["status"] == "VALID", result


# CAL-10 holiday ------------------------------------------------------------ #
async def test_cal10_holiday_is_blocked_and_next_working_day_suggested(client: AsyncClient, interviewer_id: int):
    holiday = _weekday_on_or_after(date(2040, 6, 1), 2)  # a Wednesday
    created = await client.post("/api/v1/holidays", json={"date": holiday.isoformat(), "name": "QA National Holiday"})
    assert created.status_code == 201, created.text
    try:
        result = await _check(client, interviewer_id, holiday, "10:00")

        assert result["is_available"] is False
        assert result["rule_code"] == "[rule-holiday]"
        assert result["suggested_alternatives"][0].startswith((holiday + timedelta(days=1)).isoformat())
    finally:
        await client.delete(f"/api/v1/holidays/{created.json()['data']['id']}")


# CAL-11 / 12 conflict and buffer ------------------------------------------- #
async def test_cal11_overlapping_meeting_is_reported_as_conflict(client: AsyncClient, interviewer_id: int, book):
    await book(TUESDAY, "10:00", "11:00")

    result = await _check(client, interviewer_id, TUESDAY, "10:30")

    assert result["is_available"] is False
    assert result["status"] == "CONFLICT_EXISTING_EVENT"
    assert result["conflicting_event"] == "QA existing meeting"


async def test_cal12_configured_buffer_is_enforced(
    client: AsyncClient, test_session: AsyncSession, interviewer_id: int, book
):
    """The buffer comes from the operational policy (seed default 20 min; the TC text assumes 15). Read it, don't guess."""
    buffer_min = (await test_session.execute(select(WorkCalendar.nbuffer_minutes))).scalars().first()
    await book(TUESDAY, "10:00", "11:00")
    base = datetime(2000, 1, 1, 11, 0)

    too_close = await _check(client, interviewer_id, TUESDAY, (base + timedelta(minutes=buffer_min - 5)).strftime("%H:%M"))
    exactly_buffer = await _check(client, interviewer_id, TUESDAY, (base + timedelta(minutes=buffer_min)).strftime("%H:%M"))

    assert too_close["status"] == "INSUFFICIENT_BUFFER"
    assert too_close["rule_code"] == "[rule-buffer-window]"
    assert exactly_buffer["status"] == "VALID"


# CAL-13 timezone ----------------------------------------------------------- #
async def test_cal13_wit_request_is_checked_in_local_working_hours(client: AsyncClient, interviewer_id: int):
    inside = await _check(client, interviewer_id, TUESDAY, "10:00", tz="WIT")
    outside = await _check(client, interviewer_id, TUESDAY, "08:30", tz="WIT")

    assert inside["status"] == "VALID"
    assert outside["status"] == "OUTSIDE_WORKING_HOURS"


@pytest.mark.xfail(
    strict=True,
    reason="KNOWN GAP: the checker never returns the candidate's local time. A request for 10:00 WIB with a WIT "
    "candidate gives no '12:00 WIT' anywhere in the response (CAL-13 expects the candidate local time).",
)
async def test_cal13_candidate_local_time_is_displayed(client: AsyncClient, interviewer_id: int):
    result = await _check(client, interviewer_id, TUESDAY, "10:00")

    assert "12:00" in str(result)


# Security observation relevant to CAL-01 / 02 / 03 -------------------------- #
@pytest.mark.xfail(
    strict=True,
    reason="KNOWN GAP: calendar events and the slot checker declare no authentication, so interviewer schedules "
    "are readable without a token.",
)
@pytest.mark.parametrize(
    ("method", "path"),
    [("get", "/api/v1/calendarMatrix/events"), ("post", "/api/v1/slotConflictChecker/check")],
)
def test_cal_endpoints_require_authentication(method: str, path: str):
    spec = app.openapi()
    assert "security" in spec["paths"]["/api/v1/auditLogs"]["get"], "control: a protected endpoint is marked secured"
    assert "security" in spec["paths"][path][method]