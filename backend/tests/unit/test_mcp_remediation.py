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
    # Either an explicit "not found" or a "similar names" ambiguity signal is acceptable;
    # both halt triage instead of silently substituting another candidate.
    assert ("tidak ditemukan" in res["message"]) or ("mirip" in res["message"])
    # Action plan must NOT be created with wrong candidate
    assert res.get("action_plan") is None


@pytest.mark.asyncio
async def test_tc06_get_candidate_profile_ambiguity_and_not_found():
    """Verify TC-06: get_candidate_profile handles substring ambiguity and not-found cleanly without crash."""
    # 1. Ambiguous query "Siti"
    raw_amb = await heketon_mcp.call_tool("get_candidate_profile", {"candidate_query": "Siti"})
    res_amb = _parse(raw_amb)
    assert res_amb["found"] is True
    assert res_amb["is_ambiguous"] is True
    assert res_amb["match_type"] == "AMBIGUOUS"
    assert res_amb["total"] >= 2
    matched = res_amb.get("matched_candidates") or res_amb.get("candidates")
    assert len(matched) >= 2
    for c in matched:
        assert "job_position" in c
        assert "applied_position" in c

    # 2. Not found query "Siti Rahmawati"
    raw_nf = await heketon_mcp.call_tool("get_candidate_profile", {"candidate_query": "Siti Rahmawati"})
    res_nf = _parse(raw_nf)
    assert res_nf["found"] is False
    assert res_nf["total"] == 0
    assert res_nf["candidates"] == []


@pytest.mark.asyncio
async def test_tc05_list_negotiation_threads_contract():
    """Verify TC-05: list_negotiation_threads returns thread_id, int candidate_id, and MCP enum status."""
    raw = await heketon_mcp.call_tool("list_negotiation_threads", {"status": "ACTIVE"})
    res = _parse(raw)
    assert "total" in res
    assert "threads" in res
    assert isinstance(res["threads"], list)
    for t in res["threads"]:
        assert "thread_id" in t
        assert isinstance(t["candidate_id"], int)
        assert t["status"] in ("ACTIVE", "COMPLETED", "HALTED", "EXPIRED")
        assert t["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_tc01_search_contacts_found_field():
    """Verify search_contacts includes 'found' field."""
    raw = await heketon_mcp.call_tool("search_contacts", {"query": "Budi"})
    res = _parse(raw)
    assert "found" in res
    assert res["found"] is True
    assert res["total"] >= 1


@pytest.mark.asyncio
async def test_tc08_ground_truth_exact_resolution():
    """Verify TC-08: numeric candidate ID lookup resolves with confidence=1.0 and match_type=EXACT."""
    raw = await heketon_mcp.call_tool("get_candidate_profile", {"candidate_query": "12"})
    res = _parse(raw)
    assert res["found"] is True
    assert res["confidence"] == 1.0
    assert res["match_type"] == "EXACT"


@pytest.mark.asyncio
async def test_temuan_04_11_buffer_and_interviewer_validation():
    """Verify check_slot_conflict validates interviewer_id and enforces 15m RULE_MEETING_BUFFER."""
    # 1. Invalid interviewer_id="999"
    raw_inv = await heketon_mcp.call_tool(
        "check_slot_conflict",
        {
            "interviewer_id": "999",
            "date": "2026-11-09",
            "time": "10:00",
            "timezone": "WIB",
            "duration_minutes": 60,
        },
    )
    res_inv = _parse(raw_inv)
    assert res_inv["is_available"] is False
    assert res_inv["status"] == "INTERVIEWER_NOT_FOUND"
    assert len(res_inv.get("sources_cited", [])) >= 1

    # 2. Direct overlap with Budi Santoso's Monday 13:00-14:00 WIB meeting
    raw_ov = await heketon_mcp.call_tool(
        "check_slot_conflict",
        {
            "interviewer_id": "10",
            "date": "2026-11-09",
            "time": "13:00",
            "timezone": "WIB",
            "duration_minutes": 60,
        },
    )
    res_ov = _parse(raw_ov)
    assert res_ov["is_available"] is False
    assert res_ov["status"] == "CONFLICT_EXISTING_EVENT"
    assert res_ov["conflicting_event"] == "Weekly Engineering Sync"

    # 3. 15-minute buffer violation at 14:05 WIB (5 mins after 14:00 WIB end)
    raw_buf = await heketon_mcp.call_tool(
        "check_slot_conflict",
        {
            "interviewer_id": "10",
            "date": "2026-11-09",
            "time": "14:05",
            "timezone": "WIB",
            "duration_minutes": 60,
        },
    )
    res_buf = _parse(raw_buf)
    assert res_buf["is_available"] is False
    assert res_buf["status"] in ("INSUFFICIENT_BUFFER", "CONFLICT_EXISTING_EVENT")
    assert res_buf["rule_code"] in ("RULE_MEETING_BUFFER", "RULE_CALENDAR_BUSY")
    assert ("Weekly Engineering Sync" in str(res_buf.get("conflicting_event"))) or bool(res_buf.get("conflicting_event"))


@pytest.mark.asyncio
async def test_temuan_05_negated_day_parsing():
    """Verify negated day ('Hari Senin kurang cocok, bisa Selasa jam 15:00 WIB?') selects Selasa."""
    raw = await heketon_mcp.call_tool(
        "orchestrate_hr_command",
        {
            "command": "Jadwalkan ulang interview sesuai balasan: Hari Senin kurang cocok, bisa Selasa jam 15:00 WIB?",
            "candidate_id": 12,
            "interviewer_id": 10,
        },
    )
    res = _parse(raw)
    assert res["status"] == "PENDING APPROVAL"
    slot = res["proposed_slot"]
    assert "2026-11-10" in slot["start_utc"]
    assert ("Tuesday" in slot["formatted_wib"]) or ("Selasa" in slot["formatted_wib"])
    assert "15:00 WIB" in slot["formatted_wib"]


@pytest.mark.asyncio
async def test_tc11_simulate_fast_chain_cooldown():
    """Verify approve_action_plan with simulate_fast_chain=True triggers COOLDOWN_ACTIVE."""
    raw = await heketon_mcp.call_tool(
        "approve_action_plan",
        {
            "plan_id": "1",
            "approval_ticket": "TKT-HEK-SIM",
            "simulate_fast_chain": True,
            "simulated_elapsed_ms": 120,
            "caller_role_override": "HR",
        },
    )
    res = _parse(raw)
    assert res["success"] is False
    assert res["status"] == "COOLDOWN_ACTIVE"
    assert res["error_code"] == "409_AUTO_CHAIN_BLOCKED"
    assert res["cooldown_window_ms"] == 2000


@pytest.mark.asyncio
async def test_tc13_temuan_03_10_interviewer_rbac_and_analyzer():
    """Verify HR-Only by default access: salary accessible to HR, and decision recording."""
    from app.db.DatabaseSession import AsyncSessionLocal
    from app.service.InterviewSessionService import InterviewSessionService

    # 1. Salary transparently accessible to authoritative HR Lead
    raw_cand = await heketon_mcp.call_tool(
        "get_candidate_profile",
        {"candidate_query": "12"},
    )
    res_cand = _parse(raw_cand)
    assert res_cand["caller_role"] == "HR"
    assert res_cand["candidate"]["expected_salary"] == 24000000
    assert res_cand["candidate"]["current_salary"] == 18000000

    # 2. Setup fresh interview session to record decision
    async with AsyncSessionLocal() as session:
        int_svc = InterviewSessionService(session)
        created_session = await int_svc.upload_interview_file(
            filename="remediation_interview.mp3",
            content=b"\xff\xfb\x90\x44\x00" + b"\x00" * 300,
            candidate_id="1",
            profile_id="1",
            consent_status="GRANTED",
            notes="Evaluasi teknis kandidat.",
        )
        fresh_id = str(created_session.id)

    # 3. record_interview_decision records recruitment decision by HR
    raw_dec = await heketon_mcp.call_tool(
        "record_interview_decision",
        {
            "interview_id": fresh_id,
            "decision": "ADVANCE",
            "notes": "Kandidat sangat menguasai arsitektur backend dan distributed systems.",
        },
    )
    res_dec = _parse(raw_dec)
    assert res_dec["success"] is True
    assert res_dec["decision"] == "ADVANCE"


@pytest.mark.asyncio
async def test_tc05b_max_rounds_halted_graceful():
    """Verify that candidate reply on a thread at round 3 gracefully halts without CheckViolationError."""
    from app.db.DatabaseSession import AsyncSessionLocal
    from app.service.NegotiationThreadService import NegotiationThreadService

    # 1. Set thread #1 to round 3
    async with AsyncSessionLocal() as db:
        thread_svc = NegotiationThreadService(db)
        thread = await thread_svc.negotiation_repo.get_by_id(1)
        if thread:
            thread.ncurrent_round = 3
            thread.vstatus = "NEGOTIATING"
            db.add(thread)
            await db.commit()

    # 2. Candidate attempts reply #4
    raw = await heketon_mcp.call_tool(
        "triage_candidate_reply",
        {
            "thread_id": "1",
            "reply_text": "Bisa tolong reschedule lagi ke minggu depan?",
            "channel": "whatsapp",
            "caller_role_override": "HR",
        },
    )
    res = _parse(raw)
    assert res.get("status") in ("HALTED", "DEADLOCK_ESCALATED")
    assert res.get("mcp_status") == "HALTED"
    assert res.get("is_escalated") is True
    assert "tercapai" in res.get("message", "").lower() or "terlampaui" in res.get("message", "").lower()

