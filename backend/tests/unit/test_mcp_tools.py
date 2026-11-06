"""Unit tests for Heketon MCP Server, 3-Tier Tools, Resources, and Prompts.

File: backend/tests/unit/test_mcp_tools.py
"""

import json

import pytest
from sqlalchemy import delete

from app.db.DatabaseSession import AsyncSessionLocal
from app.mcp.McpAuthGuard import (
    _PLAN_DRAFT_TIMESTAMPS_MS,
    MIN_APPROVAL_COOLDOWN_MS,
    check_anti_auto_chain_cooldown,
    record_draft_timestamp,
    verify_caller_rbac,
)
from app.mcp.McpServer import heketon_mcp
from app.model.OrchestrationModel import CalendarEvent


def _parse_tool_result(res) -> dict:
    """Helper to unwrap FastMCP tool call results cleanly across tuple/list/dict formats."""
    if isinstance(res, tuple):
        if len(res) > 1 and isinstance(res[1], dict):
            return res[1]
        if (
            len(res) > 0
            and isinstance(res[0], list)
            and len(res[0]) > 0
            and hasattr(res[0][0], "text")
        ):
            return json.loads(res[0][0].text)
    if isinstance(res, list) and res and hasattr(res[0], "text"):
        return json.loads(res[0].text)
    if hasattr(res, "text"):
        return json.loads(res.text)
    if isinstance(res, dict):
        return res
    raise TypeError(f"Unexpected tool result type: {type(res)} -> {res}")


def _parse_resource_text(res) -> str:
    """Helper to extract text from FastMCP read_resource response."""
    if isinstance(res, list) and len(res) > 0:
        first = res[0]
        if hasattr(first, "content"):
            return first.content
        return first.text if hasattr(first, "text") else str(first)
    if hasattr(res, "content"):
        return res.content
    if hasattr(res, "text"):
        return res.text
    return str(res)


@pytest.mark.asyncio
async def test_mcp_primitives_discovery():
    """Verify all 17 tools, 4 resources, and 3 prompts are registered on FastMCP."""
    # 1. Tools
    tool_names = [t.name for t in await heketon_mcp.list_tools()]
    expected_tools = [
        "search_contacts",
        "get_candidate_profile",
        "get_operational_rules",
        "list_national_holidays",
        "check_slot_conflict",
        "validate_schedule",
        "list_negotiation_threads",
        "verify_audit_chain",
        "draft_action_plan",
        "orchestrate_hr_command",
        "orchestrate_voice_note",
        "triage_candidate_reply",
        "analyze_interview_session",
        "approve_action_plan",
        "undo_action_plan",
        "reject_action_plan",
        "record_interview_decision",
    ]
    for exp in expected_tools:
        assert exp in tool_names, (
            f"Tool '{exp}' missing from registered tools: {tool_names}"
        )

    # 2. Resources
    resource_uris = [str(r.uri) for r in await heketon_mcp.list_resources()]
    expected_resources = [
        "heketon://rules/operational",
        "heketon://accountability/sheet",
        "heketon://plans/current",
        "heketon://audit/recent",
    ]
    for res in expected_resources:
        assert res in resource_uris, (
            f"Resource '{res}' missing from registered resources: {resource_uris}"
        )

    # 3. Prompts
    prompt_names = [p.name for p in await heketon_mcp.list_prompts()]
    expected_prompts = [
        "schedule-triage",
        "meeting-to-action",
        "interview-review",
    ]
    for pr in expected_prompts:
        assert pr in prompt_names, (
            f"Prompt '{pr}' missing from registered prompts: {prompt_names}"
        )


@pytest.mark.asyncio
async def test_mcp_rbac_guard_resolution():
    """Verify RBAC resolution strictly returns authoritative HR identity."""
    caller = await verify_caller_rbac()
    assert caller.role == "HR"
    assert caller.actor_id == "hr.lead@company.com"


@pytest.mark.asyncio
async def test_mcp_anti_auto_chain_cooldown():
    """Verify Anti-Auto-Chain cooldown blocks calls within 2000ms."""
    test_plan_id = "test-plan-999"
    record_draft_timestamp(test_plan_id)

    # Calling immediately must trigger cooldown violation (409)
    passed, err = check_anti_auto_chain_cooldown(test_plan_id)
    assert not passed
    assert "Pelanggaran dicegah" in str(err)

    # Calling for non-existent plan ID has no timestamp, thus passes
    passed_other, _ = check_anti_auto_chain_cooldown("untracked-plan-id")
    assert passed_other

    # Simulating elapsed time beyond cooldown
    _PLAN_DRAFT_TIMESTAMPS_MS[test_plan_id] -= MIN_APPROVAL_COOLDOWN_MS + 500
    passed_after, _ = check_anti_auto_chain_cooldown(test_plan_id)
    assert passed_after


@pytest.mark.asyncio
async def test_mcp_tool_search_contacts():
    """Verify search_contacts returns contacts and detects ambiguous query."""
    res_budi = await heketon_mcp.call_tool("search_contacts", {"query": "Budi"})
    content = _parse_tool_result(res_budi)

    assert "contacts" in content
    assert content["total"] >= 1
    # Check that contact structure includes timezone and role
    if content["contacts"]:
        first = content["contacts"][0]
        assert "name" in first
        assert "timezone" in first


@pytest.mark.asyncio
async def test_mcp_tool_candidate_profile():
    """Verify candidate profile is accessible to authoritative HR caller."""
    res_hr = await heketon_mcp.call_tool(
        "get_candidate_profile",
        {"candidate_query": "Rina"},
    )
    content_hr = _parse_tool_result(res_hr)
    assert content_hr["found"] is True
    assert content_hr["caller_role"] == "HR"
    assert "candidate" in content_hr
    assert content_hr["candidate"]["name"] == "Rina Kusuma"


@pytest.mark.asyncio
async def test_mcp_tool_check_slot_conflict():
    """Verify slot conflict check enforces Friday prayer blackout."""
    # Friday 12:00 WIB (Prayer blackout 11:30 - 13:00)
    res_friday = await heketon_mcp.call_tool(
        "check_slot_conflict",
        {
            "date": "2026-11-06",  # Friday
            "time": "12:00",
            "interviewer_id": "10",
            "timezone": "WIB",
            "duration_minutes": 60,
        },
    )
    content = _parse_tool_result(res_friday)
    assert content["is_available"] is False
    assert content["status"] in (
        "BLOCKED_FRIDAY_PRAYER",
        "FRIDAY_PRAYER_BLACKOUT",
        "CONFLICT_DETECTED",
        "OUTSIDE_WORKING_HOURS",
    )


@pytest.mark.asyncio
async def test_mcp_tool_validate_schedule():
    """Verify validate_schedule enforces operational rules and buffer deterministically."""
    async with AsyncSessionLocal() as session:
        await session.execute(delete(CalendarEvent).where(CalendarEvent.vrule_code == "[cal-agent-booked]"))
        await session.commit()

    # 1. Valid slot (Monday 10:00 WIB)
    res_valid = await heketon_mcp.call_tool(
        "validate_schedule",
        {
            "start_time": "2026-11-09T10:00:00+07:00",
            "duration_minutes": 60,
            "candidate_id": 1,
            "interviewer_id": 10,
        },
    )
    val_data = _parse_tool_result(res_valid)
    assert val_data["is_valid"] is True
    assert val_data["status"] == "VALID"
    assert len(val_data["violations"]) == 0

    # 2. Friday prayer conflict (11:30 - 13:00)
    res_friday = await heketon_mcp.call_tool(
        "validate_schedule",
        {
            "start_time": "2026-11-13T12:00:00+07:00",
            "duration_minutes": 60,
            "candidate_id": 1,
            "interviewer_id": 10,
        },
    )
    fri_data = _parse_tool_result(res_friday)
    assert fri_data["is_valid"] is False
    assert any(v.get("rule_id") == "RULE_FRIDAY_PRAYER" for v in fri_data["violations"])
    assert len(fri_data["suggestions"]) > 0

    # 3. Weekend blackout
    res_weekend = await heketon_mcp.call_tool(
        "validate_schedule",
        {
            "start_time": "2026-11-07T10:00:00+07:00",  # Saturday
            "duration_minutes": 60,
            "candidate_id": 1,
            "interviewer_id": 10,
        },
    )
    wk_data = _parse_tool_result(res_weekend)
    assert wk_data["is_valid"] is False
    assert any(
        v.get("rule_id") == "RULE_WEEKEND_BLACKOUT" for v in wk_data["violations"]
    )

    # 4. Meeting buffer violation (Budi has sync 13:00 - 14:00 on 2026-11-09)
    res_buf = await heketon_mcp.call_tool(
        "validate_schedule",
        {
            "start_time": "2026-11-09T14:05:00+07:00",
            "duration_minutes": 60,
            "candidate_id": 1,
            "interviewer_id": 10,
        },
    )
    buf_data = _parse_tool_result(res_buf)
    assert buf_data["is_valid"] is False
    assert any(
        v.get("rule_id") == "RULE_MEETING_BUFFER" for v in buf_data["violations"]
    )


@pytest.mark.asyncio
async def test_mcp_tool_draft_action_plan():
    """Verify draft_action_plan creates pending plan and enforces server defense-in-depth."""
    async with AsyncSessionLocal() as session:
        await session.execute(delete(CalendarEvent).where(CalendarEvent.vrule_code == "[cal-agent-booked]"))
        await session.commit()

    # 1. Happy path: valid draft creation
    res_draft = await heketon_mcp.call_tool(
        "draft_action_plan",
        {
            "title": "Technical Interview Round 1",
            "candidate_id": 1,
            "interviewer_id": 10,
            "start_time": "2026-11-09T10:00:00+07:00",
            "duration_minutes": 60,
            "location_type": "Google Meet",
            "candidate_channel": "whatsapp",
            "interviewer_channel": "email",
        },
    )
    draft_data = _parse_tool_result(res_draft)
    assert draft_data["success"] is True
    assert draft_data["status"] == "PENDING APPROVAL"
    assert draft_data["approval_ticket"].startswith("TKT-HEK-")
    assert draft_data["confirmation_card_ready"] is True
    assert len(draft_data["items"]) == 3
    assert len(draft_data["sources_cited"]) >= 4

    # 2. Defense-in-depth: Rejects Friday prayer conflict
    res_fri_draft = await heketon_mcp.call_tool(
        "draft_action_plan",
        {
            "title": "Technical Interview Friday Clash",
            "candidate_id": 1,
            "interviewer_id": 10,
            "start_time": "2026-11-13T12:00:00+07:00",
            "duration_minutes": 60,
        },
    )
    fri_draft_data = _parse_tool_result(res_fri_draft)
    assert fri_draft_data["success"] is False
    assert fri_draft_data["status"] == "REJECTED_BY_OPERATIONAL_RULES"
    assert "RULE_FRIDAY_PRAYER" in fri_draft_data["rejected_rules"]

    # 3. Defense-in-depth: Rejects buffer conflict (14:05)
    res_buf_draft = await heketon_mcp.call_tool(
        "draft_action_plan",
        {
            "title": "Technical Interview Buffer Conflict",
            "candidate_id": 1,
            "interviewer_id": 10,
            "start_time": "2026-11-09T14:05:00+07:00",
            "duration_minutes": 60,
        },
    )
    buf_draft_data = _parse_tool_result(res_buf_draft)
    assert buf_draft_data["success"] is False
    assert buf_draft_data["status"] == "REJECTED_BY_OPERATIONAL_RULES"
    assert "RULE_MEETING_BUFFER" in buf_draft_data["rejected_rules"]


@pytest.mark.asyncio
async def test_mcp_tool_verify_audit_chain():
    """Verify audit log hash-chain verification tool returns valid cryptographic status."""
    res = await heketon_mcp.call_tool("verify_audit_chain", {})
    content = _parse_tool_result(res)
    assert "is_valid" in content
    assert content["is_valid"] is True


@pytest.mark.asyncio
async def test_mcp_tool_interview_consent_gate():
    """Verify analyze_interview_session blocks analysis if consent_status != GRANTED."""
    res_no_consent = await heketon_mcp.call_tool(
        "analyze_interview_session",
        {
            "candidate_id": "1",
            "profile_code": "PROFILE-TECH-R1",
            "consent_status": "NOT_GRANTED",
        },
    )
    content = _parse_tool_result(res_no_consent)
    assert content["success"] is False
    assert content["error_code"] == "CONSENT_GATE_BLOCKED"
    assert content["job_status"] == "REJECTED_NO_CONSENT"


@pytest.mark.asyncio
async def test_mcp_resources_reading():
    """Verify reading operational rules and accountability sheet resources."""
    # 1. Operational rules resource
    raw_rules = await heketon_mcp.read_resource("heketon://rules/operational")
    rules_text = _parse_resource_text(raw_rules)
    assert "working_hours_local" in rules_text
    assert "11:30 - 13:00" in rules_text

    # 2. Accountability sheet resource
    raw_sheet = await heketon_mcp.read_resource("heketon://accountability/sheet")
    sheet_text = _parse_resource_text(raw_sheet)
    assert "What the Agent CAN Access" in sheet_text
    assert "What the Agent Will NEVER Do" in sheet_text


# =============================================================================
# Regression tests for the blackbox audit findings (F-01, F-05, F-13, F-04)
# =============================================================================

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.model.FollowupModel import FollowupPlan
from app.model.OrchestrationModel import NegotiationThread
from app.service.ActionPlanService import ActionPlanService


def _plan_metadata(start: datetime) -> dict:
    return {
        "proposed_slot": {
            "title": "Technical Interview",
            "start_utc": start.isoformat(),
            "end_utc": (start + timedelta(minutes=60)).isoformat(),
            "formatted_wib": "10:00 WIB",
            "formatted_wita": "11:00 WITA",
            "formatted_wit": "12:00 WIT",
            "duration_minutes": 60,
            "location_type": "Google Meet",
            "meeting_link": "https://meet.google.com/hkt-ops-2026",
        },
        "candidate_id": "1",
        "candidate_name": "Rina Kusuma",
        "interviewer_id": "10",
        "interviewer_name": "Budi Santoso",
        "sources_cited": [],
        "items": [],
    }


async def _create_test_plan(
    ticket: str, start: datetime, thread_id: int | None = None
) -> int:
    async with AsyncSessionLocal() as db:
        plan = FollowupPlan(
            vplan="Regression test plan",
            vaction_type="CALENDAR",
            dscheduled_start_utc=start,
            dscheduled_end_utc=start + timedelta(minutes=60),
            vimpact_level="HIGH",
            vapproval_status="AWAITING_APPROVAL",
            vapproval_token=ticket,
            nid_thread=thread_id,
            vagent_metadata=_plan_metadata(start),
        )
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        return plan.nid


async def _delete_test_plan(plan_id: int) -> None:
    async with AsyncSessionLocal() as db:
        plan = await db.get(FollowupPlan, plan_id)
        if plan:
            await db.delete(plan)
            await db.commit()


@pytest.mark.asyncio
async def test_audit_resource_returns_25_events():
    """heketon://audit/recent must honour the documented 25-event page size."""
    raw = await heketon_mcp.read_resource("heketon://audit/recent")
    payload = json.loads(_parse_resource_text(raw))
    assert payload["total_returned"] == 25
    assert len(payload["events"]) == 25
    assert payload["chain_integrity"]["is_valid"] is True


@pytest.mark.asyncio
async def test_approval_ticket_rejected_when_wrong():
    """A forged approval ticket must never authorise an ActionPlan."""
    start = datetime(2026, 11, 12, 3, 0, tzinfo=UTC)
    plan_id = await _create_test_plan("TKT-HEK-VALID001", start)
    try:
        raw = await heketon_mcp.call_tool(
            "approve_action_plan",
            {
                "plan_id": str(plan_id),
                "approval_ticket": "TKT-HEK-FAKE0000",
                "high_impact_acknowledged": True,
            },
        )
        res = _parse_tool_result(raw)
        assert res["success"] is False
        assert res["error_code"] == "403_INVALID_APPROVAL_TICKET"
    finally:
        await _delete_test_plan(plan_id)


@pytest.mark.asyncio
async def test_approve_rejects_weekend_slot():
    """Approval gate must reject a Saturday slot even if it slipped through drafting."""
    start = datetime(2026, 11, 7, 3, 0, tzinfo=UTC)  # Saturday 10:00 WIB
    plan_id = await _create_test_plan("TKT-HEK-WEEKEND01", start)
    try:
        with pytest.raises(Exception) as excinfo:
            await heketon_mcp.call_tool(
                "approve_action_plan",
                {
                    "plan_id": str(plan_id),
                    "approval_ticket": "TKT-HEK-WEEKEND01",
                    "high_impact_acknowledged": True,
                },
            )
        assert "RULE_WEEKEND_BLACKOUT" in str(excinfo.value)
    finally:
        await _delete_test_plan(plan_id)


@pytest.mark.asyncio
async def test_action_plan_thread_id_roundtrip():
    """thread_id must survive the read path instead of always being null."""
    async with AsyncSessionLocal() as db:
        thread_id = (
            await db.execute(select(NegotiationThread.nid).limit(1))
        ).scalar_one()

    start = datetime(2026, 11, 12, 3, 0, tzinfo=UTC)
    plan_id = await _create_test_plan("TKT-HEK-THREAD01", start, thread_id=thread_id)
    try:
        async with AsyncSessionLocal() as db:
            svc = ActionPlanService(db)
            dto = await svc.get_plan_by_id(str(plan_id))
        assert dto is not None
        assert dto.thread_id == str(thread_id)
    finally:
        await _delete_test_plan(plan_id)


@pytest.mark.asyncio
async def test_triage_reply_unknown_thread_returns_404():
    """Triage must never fall back to thread #1 for an unknown thread id."""
    raw = await heketon_mcp.call_tool(
        "triage_candidate_reply",
        {"thread_id": "999999", "reply_text": "Saya bisa hadir"},
    )
    res = _parse_tool_result(raw)
    assert res["success"] is False
    assert res["error_code"] == "404_THREAD_NOT_FOUND"
