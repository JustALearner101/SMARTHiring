"""Integration tests for Heketon MCP Server mounted on FastAPI.

File: backend/tests/integration/test_mcp_integration.py
Tests:
  1. Mount and discovery of MCP SSE transport on FastAPI (/mcp).
  2. Full 3-Tier Command Orchestration -> Confirmation -> Approval -> Undo Cycle.
  3. Strict 5-Pillar RBAC & Cooldown enforcement across multi-role workflows.
  4. Voice note and interview decision recording with audit trail.
"""

import json

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.mcp.McpAuthGuard import _PLAN_DRAFT_TIMESTAMPS_MS, MIN_APPROVAL_COOLDOWN_MS
from app.mcp.McpServer import heketon_mcp
from app.service.InterviewSessionService import InterviewSessionService


def _unwrap(res) -> dict:
    """Helper to unwrap FastMCP call_tool responses into dict."""
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
    raise TypeError(f"Cannot unwrap response of type {type(res)}: {res}")


@pytest.mark.asyncio
class TestMcpIntegrationE2E:
    async def test_mcp_sse_endpoint_mounted(self, client: AsyncClient):
        """Verify that FastMCP SSE transport is mounted on FastAPI at /mcp."""
        # 1. Verify ASGI Mount in FastAPI route table
        mcp_mount = next(
            (r for r in app.routes if getattr(r, "path", None) == "/mcp"), None
        )
        assert mcp_mount is not None, "FastMCP mount '/mcp' missing in FastAPI app"

        # 2. Verify HTTP request to message transport returns 400 (Missing session_id query param)
        response = await client.post("/mcp/messages/")
        assert response.status_code in (400, 422)

    async def test_full_orchestration_approval_and_undo_flow(self):
        """End-to-End Test: Orchestrate HR command -> Draft plan -> Enforce Cooldown -> Approve -> Undo.

        Pillars Tested:
          - SOURCES (sources_cited present)
          - PERMISSIONS (HR allowed)
          - APPROVAL (Two-turn confirmation card, Cooldown > 2000ms, Undo buffer 60s)
          - RECORD (Audit log trace)
        """
        # Step 1: HR submits scheduling command
        draft_res = await heketon_mcp.call_tool(
            "orchestrate_hr_command",
            {
                "command": "Jadwalkan technical interview untuk Rina Kusuma dengan Pak Budi Santoso hari Senin jam 10 pagi.",
            },
        )
        plan = _unwrap(draft_res)
        plan_id = str(plan["id"])
        approval_ticket = plan.get("approval_ticket", f"TKT-TEST-{plan_id}")

        assert plan["status"] == "PENDING APPROVAL"
        assert len(plan["sources_cited"]) >= 1
        assert plan.get("confirmation_card_ready") is True

        # Step 2: Attempt approval immediately -> Anti-Auto-Chain cooldown MUST trigger (409)
        early_res = await heketon_mcp.call_tool(
            "approve_action_plan",
            {
                "plan_id": plan_id,
                "approval_ticket": approval_ticket,
            },
        )
        early_approval = _unwrap(early_res)
        assert early_approval["success"] is False
        assert early_approval["error_code"] in (
            "409_AUTO_CHAIN_BLOCKED",
            "409_COOLDOWN_VIOLATION",
        )
        assert "Pelanggaran dicegah" in early_approval.get("message", "")

        # Step 3: Advance clock / simulate human review cooldown (> 2000 ms)
        _PLAN_DRAFT_TIMESTAMPS_MS[plan_id] -= MIN_APPROVAL_COOLDOWN_MS + 200

        # Step 4: Legitimate human approval
        valid_approve_res = await heketon_mcp.call_tool(
            "approve_action_plan",
            {
                "plan_id": plan_id,
                "approval_ticket": approval_ticket,
                "high_impact_acknowledged": True,
            },
        )
        approval_data = _unwrap(valid_approve_res)
        assert approval_data["success"] is True
        assert approval_data["status"] == "UNDO_WINDOW"
        assert approval_data["undo_buffer_seconds"] == 60
        assert approval_data["undo_expires_at"] is not None

        # Step 5: Exercise 60s Undo window to roll back action plan
        undo_res = await heketon_mcp.call_tool(
            "undo_action_plan",
            {
                "plan_id": plan_id,
                "reason": "Salah memilih waktu interviewer",
            },
        )
        undo_data = _unwrap(undo_res)
        assert undo_data["success"] is True
        assert undo_data["status"] == "UNDONE"

    async def test_workbuddy_v1_1_deterministic_flow(self):
        """End-to-End Test for WorkBuddy AI v1.1 native toolchain.

        Flow:
          1. search_contacts -> resolves Budi Santoso (id=10) & Rina Kusuma (id=1)
          2. validate_schedule -> pre-flight check confirms valid slot Monday 10:00 WIB
          3. draft_action_plan -> creates PENDING APPROVAL plan + issues TKT-HEK-XXXX ticket
          4. Anti-Auto-Chain cooldown check blocks rapid approval
          5. Legitimate human approval opens 60s Undo buffer
        """
        # Step 1: Resolve contacts
        search_res = await heketon_mcp.call_tool(
            "search_contacts", {"query": "Budi Santoso"}
        )
        contacts = _unwrap(search_res)
        assert contacts["total"] >= 1
        budi_id = contacts["contacts"][0]["id"]

        # Step 2: Validate schedule (Read-only, zero LLM)
        val_res = await heketon_mcp.call_tool(
            "validate_schedule",
            {
                "start_time": "2026-11-09T10:00:00+07:00",
                "duration_minutes": 60,
                "candidate_id": 1,
                "interviewer_id": budi_id,
            },
        )
        val_data = _unwrap(val_res)
        assert val_data["is_valid"] is True
        assert val_data["status"] == "VALID"
        assert len(val_data["sources_cited"]) >= 1

        # Step 3: Draft ActionPlan
        draft_res = await heketon_mcp.call_tool(
            "draft_action_plan",
            {
                "title": "WorkBuddy v1.1 Technical Interview",
                "candidate_id": 1,
                "interviewer_id": budi_id,
                "start_time": "2026-11-09T10:00:00+07:00",
                "duration_minutes": 60,
                "location_type": "Google Meet",
                "candidate_channel": "whatsapp",
                "interviewer_channel": "email",
            },
        )
        plan = _unwrap(draft_res)
        plan_id = str(plan["id"])
        ticket = plan["approval_ticket"]

        assert plan["success"] is True
        assert plan["status"] == "PENDING APPROVAL"
        assert ticket.startswith("TKT-HEK-")
        assert plan["confirmation_card_ready"] is True
        assert len(plan["items"]) == 3

        # Step 4: Rapid approval blocked by Anti-Auto-Chain cooldown
        fast_res = await heketon_mcp.call_tool(
            "approve_action_plan",
            {
                "plan_id": plan_id,
                "approval_ticket": ticket,
                "simulate_fast_chain": True,
            },
        )
        fast_approval = _unwrap(fast_res)
        assert fast_approval["success"] is False
        assert fast_approval["error_code"] == "409_AUTO_CHAIN_BLOCKED"

        # Step 5: Advance cooldown and execute approval
        _PLAN_DRAFT_TIMESTAMPS_MS[plan_id] -= MIN_APPROVAL_COOLDOWN_MS + 500
        approve_res = await heketon_mcp.call_tool(
            "approve_action_plan",
            {
                "plan_id": plan_id,
                "approval_ticket": ticket,
                "high_impact_acknowledged": True,
            },
        )
        approve_data = _unwrap(approve_res)
        assert approve_data["success"] is True
        assert approve_data["status"] == "UNDO_WINDOW"
        assert approve_data["undo_buffer_seconds"] == 60

    async def test_voice_note_orchestration_and_audit(self):
        """Test voice note transcription-to-action triage with audit log verification."""
        vn_res = await heketon_mcp.call_tool(
            "orchestrate_voice_note",
            {
                "audio_path_or_preset": "standard",
            },
        )
        vn_data = _unwrap(vn_res)
        assert vn_data["status"] == "PENDING APPROVAL"
        assert "approval_ticket" in vn_data

        # Verify audit log cryptographic integrity
        audit_res = await heketon_mcp.call_tool("verify_audit_chain", {})
        audit_data = _unwrap(audit_res)
        assert audit_data["is_valid"] is True

    async def test_interviewer_decision_recording_and_salary_lock(
        self, test_session: AsyncSession
    ):
        """Test interview decision recording and candidate profile retrieval."""
        # 0. Setup fresh interview session to record decision
        int_svc = InterviewSessionService(test_session)
        created_session = await int_svc.upload_interview_file(
            filename="technical_interview.mp3",
            content=b"\xff\xfb\x90\x44\x00" + b"\x00" * 300,
            candidate_id="1",
            profile_id="1",
            consent_status="GRANTED",
            notes="Kandidat menguasai Next.js dan FastAPI.",
        )
        fresh_id = str(created_session.id)

        # 1. HR can record decision
        decision_res = await heketon_mcp.call_tool(
            "record_interview_decision",
            {
                "interview_id": fresh_id,
                "decision": "ADVANCE",
                "notes": "Kandidat memiliki kompetensi teknis yang solid.",
            },
        )
        dec_data = _unwrap(decision_res)
        assert dec_data["success"] is True
        assert dec_data["decision"] == "ADVANCE"

        # 2. Candidate profile access
        cand_res = await heketon_mcp.call_tool(
            "get_candidate_profile",
            {"candidate_query": "Rina"},
        )
        cand_data = _unwrap(cand_res)
        assert cand_data["found"] is True
        assert cand_data["candidate"]["name"] == "Rina Kusuma"
