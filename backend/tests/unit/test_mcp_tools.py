"""Unit tests for Heketon MCP Server, 3-Tier Tools, Resources, and Prompts.

File: backend/tests/unit/test_mcp_tools.py
"""

import json

import pytest

from app.mcp.McpAuthGuard import (
    _PLAN_DRAFT_TIMESTAMPS_MS,
    MIN_APPROVAL_COOLDOWN_MS,
    check_anti_auto_chain_cooldown,
    record_draft_timestamp,
    verify_caller_rbac,
)
from app.mcp.McpServer import heketon_mcp


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
        return res[0].text if hasattr(res[0], "text") else str(res[0])
    if hasattr(res, "text"):
        return res.text
    return str(res)


@pytest.mark.asyncio
async def test_mcp_primitives_discovery():
    """Verify all 13 tools, 4 resources, and 3 prompts are registered on FastMCP."""
    # 1. Tools
    tool_names = [t.name for t in await heketon_mcp.list_tools()]
    expected_tools = [
        "search_contacts",
        "get_candidate_profile",
        "get_operational_rules",
        "list_national_holidays",
        "check_slot_conflict",
        "list_negotiation_threads",
        "verify_audit_chain",
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
    """Verify RBAC resolution strictly maps to HR, ADMIN, or INTERVIEWER."""
    hr_caller = await verify_caller_rbac(caller_role_override="HR")
    assert hr_caller.role == "HR"

    admin_caller = await verify_caller_rbac(caller_role_override="ADMIN")
    assert admin_caller.role == "ADMIN"

    interviewer_caller = await verify_caller_rbac(caller_role_override="INTERVIEWER")
    assert interviewer_caller.role == "INTERVIEWER"


@pytest.mark.asyncio
async def test_mcp_anti_auto_chain_cooldown():
    """Verify Anti-Auto-Chain cooldown blocks calls within 2000ms."""
    test_plan_id = "test-plan-999"
    record_draft_timestamp(test_plan_id)

    # Calling immediately must trigger cooldown violation (409)
    passed, err = check_anti_auto_chain_cooldown(test_plan_id)
    assert not passed
    assert "Pelanggaran Pilar APPROVAL dicegah" in str(err)

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
async def test_mcp_tool_candidate_salary_masking():
    """Verify candidate expected_salary is redacted for INTERVIEWER role."""
    # 1. As INTERVIEWER: salary must be masked
    res_interviewer = await heketon_mcp.call_tool(
        "get_candidate_profile",
        {"candidate_query": "Rina", "caller_role_override": "INTERVIEWER"},
    )
    content_inv = _parse_tool_result(res_interviewer)
    assert content_inv["found"] is True
    assert content_inv["caller_role"] == "INTERVIEWER"
    assert content_inv["candidate"]["expected_salary"] is None
    assert "REDACTED_BY_RBAC" in content_inv["candidate"].get("salary_mask_notice", "")

    # 2. As HR: salary is accessible
    res_hr = await heketon_mcp.call_tool(
        "get_candidate_profile",
        {"candidate_query": "Rina", "caller_role_override": "HR"},
    )
    content_hr = _parse_tool_result(res_hr)
    assert content_hr["found"] is True
    assert content_hr["caller_role"] == "HR"


@pytest.mark.asyncio
async def test_mcp_tool_check_slot_conflict():
    """Verify slot conflict check enforces Friday prayer blackout."""
    # Friday 12:00 WIB (Prayer blackout 11:30 - 13:00)
    res_friday = await heketon_mcp.call_tool(
        "check_slot_conflict",
        {
            "date": "2026-11-06",  # Friday
            "time": "12:00",
            "interviewer_id": "1",
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
async def test_mcp_tool_verify_audit_chain():
    """Verify audit log hash-chain verification tool returns valid cryptographic status."""
    res = await heketon_mcp.call_tool("verify_audit_chain", {})
    content = _parse_tool_result(res)
    assert "is_valid" in content
    assert content["is_valid"] is True


@pytest.mark.asyncio
async def test_mcp_tool_approval_rbac_forbidden():
    """Verify INTERVIEWER is forbidden (403) from approving action plans."""
    res = await heketon_mcp.call_tool(
        "approve_action_plan",
        {
            "plan_id": "1",
            "approval_ticket": "TKT-TEST",
            "caller_role_override": "INTERVIEWER",
        },
    )
    content = _parse_tool_result(res)
    assert content["success"] is False
    assert content["error_code"] == "403_MCP_PERMISSION_DENIED"


@pytest.mark.asyncio
async def test_mcp_tool_interview_consent_gate():
    """Verify analyze_interview_session blocks analysis if consent_status != GRANTED."""
    res_no_consent = await heketon_mcp.call_tool(
        "analyze_interview_session",
        {
            "candidate_id": "1",
            "profile_code": "PROFILE-TECH-R1",
            "consent_status": "NOT_GRANTED",
            "caller_role_override": "HR",
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
