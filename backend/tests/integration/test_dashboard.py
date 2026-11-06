"""Black-box API checks for TC-DASH-03 .. TC-DASH-05 (TC-DASH-01/02/06 are visual and stay manual).

Run:  uv run pytest tests/integration/test_dashboard_blackbox.py -v
"""

import math

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.AppConfig import settings
from app.middleware.RateLimiterMiddleware import rate_limiter_instance
from app.service.DashboardService import DashboardService

COMMAND_URL = "/api/v1/orchestrator/command"
NORMAL_COMMAND = "Jadwalkan technical interview untuk Rina Kusuma dengan Budi Santoso."


@pytest.fixture(autouse=True)
def _safe_environment(monkeypatch):
    monkeypatch.setattr(settings, "SMTP_ENABLED", False)  # never send real email
    rate_limiter_instance.reset()
    yield
    rate_limiter_instance.reset()


async def _pending_count(client: AsyncClient) -> int:
    res = await client.get("/api/v1/dashboard/summary")
    assert res.status_code == 200, res.text
    return next(m["value"] for m in res.json()["data"]["metrics"] if m["key"] == "pending_approvals")


async def _feed(client: AsyncClient, role: str | None = None) -> dict:
    headers = {"X-Demo-Role": role} if role else {}
    res = await client.get("/api/v1/dashboard/activityFeed", headers=headers)
    assert res.status_code == 200, res.text
    return res.json()["data"]


async def _new_plan(client: AsyncClient) -> str:
    res = await client.post(COMMAND_URL, json={"command": NORMAL_COMMAND})
    assert res.status_code == 200, res.text
    assert res.json()["data"]["status"] in ("PENDING_APPROVAL", "PENDING APPROVAL")
    return res.json()["data"]["id"]


# TC-DASH-03 ---------------------------------------------------------------- #
async def test_dash03_new_plan_appears_in_pending_approvals(client: AsyncClient):
    before = await _pending_count(client)

    plan_id = await _new_plan(client)

    assert await _pending_count(client) == before + 1
    pending = (await _feed(client))["pending_approvals"]
    assert pending[0]["id"] == plan_id, "newest plan must be listed first"
    assert pending[0]["candidate_name"] and pending[0]["proposed_slot"]
    assert pending[0]["items_count"] == 3


# TC-DASH-04 ---------------------------------------------------------------- #
async def test_dash04_approval_is_reflected_on_dashboard(client: AsyncClient):
    plan_id = await _new_plan(client)
    before = await _pending_count(client)

    res = await client.post(
        f"/api/v1/actionPlans/{plan_id}/approve", json={"approved_by": "QA", "send_immediately": False}
    )
    assert res.status_code == 200

    assert await _pending_count(client) == before - 1
    assert plan_id not in [p["id"] for p in (await _feed(client))["pending_approvals"]]
    audit = (await _feed(client, role="ADMIN"))["recent_audit"]
    assert any("APPROVED" in e["event_type"] and f"#{plan_id} " in e["title"] for e in audit)


async def test_dash04_audit_trail_is_hidden_from_non_admin_roles(client: AsyncClient):
    """Documents actual behaviour: the dashboard audit trail is returned for ADMIN only."""
    await _new_plan(client)

    assert (await _feed(client, role="ADMIN"))["recent_audit"], "ADMIN must see audit events"
    assert (await _feed(client, role="HR"))["recent_audit"] == []
    assert (await _feed(client, role="INTERVIEWER"))["recent_audit"] == []


# TC-DASH-05 ---------------------------------------------------------------- #
async def test_dash05_empty_database_returns_zero_states(test_session: AsyncSession):
    """Empties the tables inside a transaction that is ALWAYS rolled back (data is never lost)."""
    try:
        await test_session.execute(
            text(
                "TRUNCATE tblt_followup_plan, tblt_negotiation_thread, tblt_calendar_event, "
                "tblt_interview, tblm_candidate, tblt_audit_log CASCADE"
            )
        )
        service = DashboardService(test_session)

        summary = await service.get_summary()
        feed = await service.get_activity_feed(include_audit=True)
        upcoming = await service.get_upcoming_interviews(limit=5)

        assert [m.value for m in summary.metrics] == [0] * len(summary.metrics)
        for m in summary.metrics:
            assert not math.isnan(m.change_percent) and not math.isinf(m.change_percent)
        assert all(s.count == 0 for s in summary.pipeline)
        assert all(p.count == 0 for p in summary.weekly_trend)
        assert feed.pending_approvals == [] and feed.active_negotiations == [] and feed.recent_audit == []
        assert upcoming == []
    finally:
        await test_session.rollback()