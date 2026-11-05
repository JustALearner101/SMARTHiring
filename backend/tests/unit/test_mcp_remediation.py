"""Unit tests for MCP Server Remediation: P0 Bugs, Weekend Blackout, Holiday Separation, and Anti-Substitution.

File: backend/tests/unit/test_mcp_remediation.py
"""

import json

import pytest

from app.mcp.McpServer import heketon_mcp


def _parse(res) -> dict:
    if isinstance(res, tuple):
        if len(res) > 1 and isinstance(res[1], dict):
            return res[1]
        if len(res) > 0 and isinstance(res[0], list) and len(res[0]) > 0 and hasattr(res[0][0], "text"):
            return json.loads(res[0][0].text)
    if isinstance(res, list) and res and hasattr(res[0], "text"):
        return json.loads(res[0].text)
    if hasattr(res, "text"):
        return json.loads(res.text)
    if isinstance(res, dict):
        return res
    raise TypeError(f"Unexpected tool result type: {type(res)} -> {res}")


@pytest.mark.asyncio
async def test_p0_list_negotiation_threads_pagination():
    """Verify list_negotiation_threads executes without 'PaginatedResponse has no len()'."""
    raw = await heketon_mcp.call_tool("list_negotiation_threads", {})
    res = _parse(raw)
    assert "total" in res
    assert "threads" in res
    assert isinstance(res["threads"], list)


@pytest.mark.asyncio
async def test_get_operational_rules_tool():
    """Verify get_operational_rules returns authoritative working hours and blackout rules."""
    raw = await heketon_mcp.call_tool("get_operational_rules", {})
    res = _parse(raw)
    assert "09:00" in res["working_hours"]
    assert "17:00" in res["working_hours"]
    assert "11:30" in res["friday_prayer_blackout"]
    assert "13:00" in res["friday_prayer_blackout"]
    assert "Saturday and Sunday" in res["weekend_blackout"]
    assert res["buffer_minutes"] in (15, 20)
    assert len(res["rules"]) >= 5


@pytest.mark.asyncio
async def test_list_national_holidays_tool():
    """Verify list_national_holidays lists 2026 official holidays."""
    raw = await heketon_mcp.call_tool("list_national_holidays", {"year": 2026})
    res = _parse(raw)
    assert res["year"] == 2026
    assert res["total"] > 0
    holiday_dates = [h["date"] for h in res["holidays"]]
    assert "2026-08-17" in holiday_dates
    assert "2026-12-25" in holiday_dates


@pytest.mark.asyncio
async def test_slot_conflict_weekend_blackout():
    """Verify scheduling on Saturday (2026-11-07) or Sunday (2026-11-08) is blocked."""
    raw = await heketon_mcp.call_tool(
        "check_slot_conflict",
        {
            "interviewer_id": "1",
            "date": "2026-11-07",
            "time": "10:00",
            "timezone": "WIB",
            "duration_minutes": 60,
        },
    )
    res = _parse(raw)
    assert res["is_available"] is False
    assert res["status"] == "WEEKEND_BLOCKED"
    assert res["rule_code"] == "RULE_WEEKEND_BLACKOUT"
    assert "Saturday" in res["message"]


@pytest.mark.asyncio
async def test_slot_conflict_national_holiday_and_valid_alternatives():
    """Verify Christmas (2026-12-25) returns NATIONAL_HOLIDAY and alternatives do not suggest Christmas."""
    raw = await heketon_mcp.call_tool(
        "check_slot_conflict",
        {
            "interviewer_id": "1",
            "date": "2026-12-25",
            "time": "10:00",
            "timezone": "WIB",
            "duration_minutes": 60,
        },
    )
    res = _parse(raw)
    assert res["is_available"] is False
    assert res["status"] == "NATIONAL_HOLIDAY"
    assert res["rule_code"] == "RULE_NATIONAL_HOLIDAY"
    assert "Hari Raya Natal" in res["message"]

    # Verify suggested alternatives NEVER contain 2026-12-25 or weekend dates
    for alt in res["suggested_alternatives"]:
        assert "2026-12-25" not in alt
        assert "2026-12-26" not in alt  # Saturday
        assert "2026-12-27" not in alt  # Sunday


@pytest.mark.asyncio
async def test_orchestrator_anti_silent_substitution():
    """Verify orchestrator halts with NEEDS_CLARIFICATION when requested candidate does not exist."""
    raw = await heketon_mcp.call_tool(
        "orchestrate_hr_command",
        {
            "command": "Jadwalkan technical interview untuk kandidat Siti Rahmawati posisi Backend Engineer minggu ini",
        },
    )
    res = _parse(raw)
    assert res["status"] == "NEEDS_CLARIFICATION"
    assert res["action_required"] == "HUMAN_CLARIFICATION"
    assert "tidak ditemukan" in res["message"]
    # Action plan must NOT be created with wrong candidate
    assert res.get("action_plan") is None
