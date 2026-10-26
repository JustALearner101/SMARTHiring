from datetime import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.dto.SlotConflictCheckerDTO import SlotConflictCheckRequestDTO
from app.model.CalendarModel import WorkCalendar
from app.service.SlotConflictCheckerService import SlotConflictCheckerService


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def default_work_calendar():
    cal = MagicMock(spec=WorkCalendar)
    cal.twork_start = time(9, 0)
    cal.twork_end = time(17, 0)
    cal.tfriday_prayer_start = time(11, 30)
    cal.tfriday_prayer_end = time(13, 0)
    cal.nmax_negotiation_rounds = 3
    cal.nbuffer_minutes = 15
    cal.binjection_guardrail_enabled = True
    return cal


async def test_friday_prayer_blackout_blocked(mock_session, default_work_calendar):
    """Test that scheduling on Friday 12:00 WIB is strictly blocked with rule [rule-jumatan]."""
    service = SlotConflictCheckerService(mock_session)
    service.policy_repo.get_policy = AsyncMock(return_value=default_work_calendar)
    service.holiday_repo.is_holiday = AsyncMock(return_value=None)
    service.matrix_repo.find_conflicts = AsyncMock(return_value=[])

    # 2026-10-30 is a Friday
    request = SlotConflictCheckRequestDTO(
        interviewer_id="1",
        date="2026-10-30",
        time="12:00",
        duration_minutes=60,
        timezone="WIB",
    )
    result = await service.check_slot_conflict(request)

    assert result.is_available is False
    assert result.status == "BLOCKED_FRIDAY_PRAYER"
    assert result.rule_code == "[rule-jumatan]"
    assert "Sholat Jumat" in result.message


async def test_friday_outside_prayer_allowed(mock_session, default_work_calendar):
    """Test that scheduling on Friday 09:30 WIB (before 11:30) is valid."""
    service = SlotConflictCheckerService(mock_session)
    service.policy_repo.get_policy = AsyncMock(return_value=default_work_calendar)
    service.holiday_repo.is_holiday = AsyncMock(return_value=None)
    service.matrix_repo.find_conflicts = AsyncMock(return_value=[])

    # 2026-10-30 is a Friday
    request = SlotConflictCheckRequestDTO(
        interviewer_id="1",
        date="2026-10-30",
        time="09:30",
        duration_minutes=60,
        timezone="WIB",
    )
    result = await service.check_slot_conflict(request)

    assert result.is_available is True
    assert result.status == "VALID"


async def test_outside_working_hours_blocked(mock_session, default_work_calendar):
    """Test that scheduling outside 09:00 - 17:00 is rejected."""
    service = SlotConflictCheckerService(mock_session)
    service.policy_repo.get_policy = AsyncMock(return_value=default_work_calendar)

    # 2026-10-28 is a Wednesday
    request = SlotConflictCheckRequestDTO(
        interviewer_id="1",
        date="2026-10-28",
        time="17:30",
        duration_minutes=60,
        timezone="WIB",
    )
    result = await service.check_slot_conflict(request)

    assert result.is_available is False
    assert result.status == "OUTSIDE_WORKING_HOURS"
    assert result.rule_code == "[rule-working-hours]"
