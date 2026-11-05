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
                "caller_role_override": "HR",
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
                "caller_role_override": "HR",
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
                "caller_role_override": "HR",
                "high_impact_acknowledged": True,
                "notes": "Disetujui oleh HR Manager",
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
                "caller_role_override": "HR",
            },
        )
        undo_data = _unwrap(undo_res)
        assert undo_data["success"] is True
        assert undo_data["status"] == "UNDONE"

    async def test_voice_note_orchestration_and_audit(self):
        """Test voice note transcription-to-action triage with audit log verification."""
        vn_res = await heketon_mcp.call_tool(
            "orchestrate_voice_note",
            {
                "audio_path_or_preset": "standard",
                "caller_role_override": "HR",
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
        """Test RBAC on interview decision recording and salary masking."""
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
                "caller_role_override": "HR",
            },
        )
        dec_data = _unwrap(decision_res)
        assert dec_data["success"] is True
        assert dec_data["decision"] == "ADVANCE"

        # 2. INTERVIEWER is forbidden from executing final HR decision
        inv_decision_res = await heketon_mcp.call_tool(
            "record_interview_decision",
            {
                "interview_id": fresh_id,
                "decision": "ADVANCE",
                "caller_role_override": "INTERVIEWER",
            },
        )
        inv_dec_data = _unwrap(inv_decision_res)
        assert inv_dec_data["success"] is False
        assert inv_dec_data["error_code"] == "403_MCP_PERMISSION_DENIED"

        # 3. INTERVIEWER cannot see salary
        cand_res = await heketon_mcp.call_tool(
            "get_candidate_profile",
            {"candidate_query": "Rina", "caller_role_override": "INTERVIEWER"},
        )
        cand_data = _unwrap(cand_res)
        assert cand_data["candidate"]["expected_salary"] is None
        assert "REDACTED_BY_RBAC" in cand_data["candidate"]["salary_mask_notice"]
