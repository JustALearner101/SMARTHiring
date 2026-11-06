"""Black-box API checks for the TC-SCHED group (Autonomous Scheduling).

UI-only cases (SCHED-01 loader/badge, 02 button state, 10/11 banner and countdown, 16 button label)
stay manual; this file proves the same behaviour at API level.

Run:  uv run pytest tests/integration/test_scheduling_blackbox.py -v -rx
"""

import asyncio
import re
from datetime import datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.AppConfig import settings
from app.main import app
from app.middleware.RateLimiterMiddleware import rate_limiter_instance
from app.model.AuditModel import AuditLog
from app.model.FollowupModel import FollowupPlan
from app.model.OrchestrationModel import CalendarEvent
from app.model.UserModel import User

COMMAND_URL = "/api/v1/orchestrator/command"
SANTOSO_CMD = "Jadwalkan technical interview untuk Rina Kusuma dengan Budi Santoso."
HARTONO_CMD = "Schedule an interview for Rina Kusuma with Budi Hartono (Finance, WITA)"


@pytest.fixture(autouse=True)
def _safe_environment(monkeypatch):
    monkeypatch.setattr(settings, "SMTP_ENABLED", False)  # never send real email
    rate_limiter_instance.reset()
    yield
    rate_limiter_instance.reset()


@pytest.fixture
async def safe_client():
    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test") as ac:
        yield ac


async def _plan(client: AsyncClient, command: str = SANTOSO_CMD) -> dict:
    res = await client.post(COMMAND_URL, json={"command": command})
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["status"] in ("PENDING_APPROVAL", "PENDING APPROVAL"), data
    return data


async def _count(session: AsyncSession, stmt) -> int:
    return (await session.execute(stmt)).scalar_one()


async def _plan_status(session: AsyncSession, plan_id: str) -> str:
    session.expire_all()
    return (await session.execute(select(FollowupPlan.vapproval_status).where(FollowupPlan.nid == int(plan_id)))).scalar_one()


async def _agent_bookings(session: AsyncSession) -> int:
    return await _count(
        session, select(func.count()).select_from(CalendarEvent).where(CalendarEvent.vrule_code == "[cal-agent-booked]")
    )


def _wib(iso: str) -> datetime:
    return datetime.fromisoformat(iso) + timedelta(hours=7)


# SCHED-02 / 03 ------------------------------------------------------------- #
@pytest.mark.xfail(
    strict=False,
    reason="KNOWN GAP: only the UI blocks an empty command. The API accepts it and still creates an approvable plan "
    "(a blank command produces a default plan for the default candidate).",
)
@pytest.mark.parametrize("command", ["", "   "])
async def test_sched02_empty_command_creates_no_plan(safe_client: AsyncClient, test_session: AsyncSession, command: str):
    before = await _count(test_session, select(func.count()).select_from(FollowupPlan))

    res = await safe_client.post(COMMAND_URL, json={"command": command})

    assert res.status_code < 500, "empty command must not crash the server"
    assert await _count(test_session, select(func.count()).select_from(FollowupPlan)) == before


async def test_sched03_preset_scenarios_are_available_and_usable(client: AsyncClient):
    res = await client.get("/api/v1/orchestrator/scenarios")

    assert res.status_code == 200
    scenarios = res.json()["data"]
    assert scenarios, "at least one preset scenario is required"
    assert all(s["label"] and s["prompt"] for s in scenarios)
    first = await client.post(COMMAND_URL, json={"command": scenarios[0]["prompt"], "scenario_id": scenarios[0]["id"]})
    assert first.status_code == 200, first.text


# SCHED-04 / 05 ------------------------------------------------------------- #
async def test_sched04_ambiguous_name_returns_both_budis_without_a_plan(client: AsyncClient, test_session: AsyncSession):
    before = await _count(test_session, select(func.count()).select_from(FollowupPlan))

    res = await client.post(COMMAND_URL, json={"command": "Schedule Rina Kusuma's interview with Pak Budi next week"})

    data = res.json()["data"]
    assert data["status"] == "CLARIFICATION_NEEDED"
    assert len(data["profiles"]) == 2
    for p in data["profiles"]:
        assert p["name"] and p["department"] and p["role"] and p["timezone"] and p["email"]
    assert await _count(test_session, select(func.count()).select_from(FollowupPlan)) == before


async def test_sched05_choosing_hartono_builds_plan_for_him_only(client: AsyncClient):
    plan = await _plan(client, HARTONO_CMD)

    assert plan["interviewer_name"] == "Budi Hartono"
    assert plan["interviewer_dept"] == "Finance"
    assert "Budi Santoso" not in " ".join(i["recipient_name"] for i in plan["items"])


# SCHED-07 / 08 / 09 -------------------------------------------------------- #
@pytest.mark.parametrize("command", [SANTOSO_CMD, "Schedule Rina Kusuma's interview with Budi Santoso next week"])
async def test_sched07_slot_is_inside_working_hours(client: AsyncClient, command: str):
    plan = await _plan(client, command)

    start, end = _wib(plan["proposed_slot"]["start_utc"]), _wib(plan["proposed_slot"]["end_utc"])
    assert start.weekday() < 5, "no weekend slots"
    assert start.hour >= 9 and (end.hour, end.minute) <= (17, 0)


async def test_sched08_friday_noon_request_never_lands_in_prayer_window(client: AsyncClient):
    plan = await _plan(client, "Schedule Rina Kusuma's interview with Budi Santoso this Friday at 12:00")

    start, end = _wib(plan["proposed_slot"]["start_utc"]), _wib(plan["proposed_slot"]["end_utc"])
    if start.weekday() == 4:
        assert end.time() <= datetime(2000, 1, 1, 11, 30).time() or start.time() >= datetime(2000, 1, 1, 13, 0).time()


@pytest.mark.xfail(
    strict=False,
    reason="KNOWN GAP: invitation drafts never mention the proposed time, so the candidate-timezone conversion "
    "(WIB 10:00 = WITA 11:00 = WIT 12:00) required by SCHED-09 is not shown anywhere in the draft text.",
)
async def test_sched09_candidate_draft_states_the_time(client: AsyncClient):
    plan = await _plan(client)

    candidate_item = next(i for i in plan["items"] if i["recipient_role"] == "Candidate")
    assert re.search(r"\d{1,2}[:.]\d{2}", candidate_item["content_preview"])


# SCHED-12 / 13 ------------------------------------------------------------- #
async def test_sched12_execution_happens_exactly_once(client: AsyncClient, test_session: AsyncSession):
    plan_id = (await _plan(client))["id"]
    bookings_before = await _agent_bookings(test_session)

    res = await client.post(f"/api/v1/actionPlans/{plan_id}/approve", json={"approved_by": "QA", "send_immediately": True})
    assert res.status_code == 200 and res.json()["data"]["status"] == "EXECUTED"
    await client.get("/api/v1/actionPlans/current")  # polling must not execute a second time

    assert await _plan_status(test_session, plan_id) == "EXECUTED"
    assert await _agent_bookings(test_session) == bookings_before + 1
    executed = await _count(
        test_session,
        select(func.count())
        .select_from(AuditLog)
        .where(AuditLog.vevent_type == "ACTION_EXECUTED", AuditLog.vmasked_detail.contains(f"#{plan_id} ")),
    )
    assert executed <= 1

    from sqlalchemy import delete
    await test_session.execute(delete(CalendarEvent).where(CalendarEvent.vrule_code == "[cal-agent-booked]"))
    await test_session.commit()


async def test_sched13_rapid_triple_approve_approves_only_once(client: AsyncClient, test_session: AsyncSession):
    plan_id = (await _plan(client))["id"]
    body = {"approved_by": "QA", "send_immediately": False}

    results = await asyncio.gather(*[client.post(f"/api/v1/actionPlans/{plan_id}/approve", json=body) for _ in range(3)])

    codes = sorted(r.status_code for r in results)
    assert codes.count(200) == 1, codes
    assert all(c in (200, 409) for c in codes), codes
    approvals = await _count(
        test_session,
        select(func.count())
        .select_from(AuditLog)
        .where(AuditLog.vevent_type == "HUMAN_APPROVED", AuditLog.vmasked_detail.contains(f"#{plan_id} ")),
    )
    assert approvals == 1
    assert await _plan_status(test_session, plan_id) == "APPROVED"


# SCHED-14 / 15 / 16 -------------------------------------------------------- #
@pytest.mark.xfail(
    strict=False,
    reason="KNOWN GAP: there is no reject endpoint. 'Reject Plan' only hides the card in the browser, so the plan "
    "stays AWAITING_APPROVAL, returns after refresh and no rejection is written to the audit log (SCHED-14/15).",
)
async def test_sched15_rejection_is_persisted_and_audited(client: AsyncClient, test_session: AsyncSession):
    plan_id = (await _plan(client))["id"]

    res = await client.post(f"/api/v1/actionPlans/{plan_id}/reject", json={"reason": "QA"})

    assert res.status_code == 200
    assert await _plan_status(test_session, plan_id) == "REJECTED"


@pytest.mark.xfail(
    strict=False,
    reason="KNOWN GAP: the UI disables Approve for ADMIN, but the API accepts approval from ADMIN "
    "(require_roles(['HR','ADMIN'])). Anyone calling the API directly bypasses the 'HR approval required' rule.",
)
async def test_sched16_admin_cannot_approve_via_api(client: AsyncClient):
    plan_id = (await _plan(client))["id"]

    res = await client.post(
        f"/api/v1/actionPlans/{plan_id}/approve",
        json={"approved_by": "auditor", "send_immediately": False},
        headers={"X-Demo-Role": "ADMIN"},
    )

    assert res.status_code == 403


# SCHED-17 ------------------------------------------------------------------ #
@pytest.mark.xfail(
    strict=False,
    reason="KNOWN GAP: with an existing booking for the interviewer, the plan still proposes the same time. "
    "The slot checker endpoint detects the conflict, but the command planner does not avoid it.",
)
async def test_sched17_existing_booking_is_not_double_booked(client: AsyncClient, test_session: AsyncSession):
    first = await _plan(client)
    start = datetime.fromisoformat(first["proposed_slot"]["start_utc"])
    end = datetime.fromisoformat(first["proposed_slot"]["end_utc"])
    budi_id = (await test_session.execute(select(User.nid).where(User.vusername == "budi.santoso"))).scalar_one()
    blocker = CalendarEvent(
        nid_user=budi_id, vtitle="QA blocker", dscheduled_start_utc=start, dscheduled_end_utc=end,
        vevent_type="SCHEDULED_INTERVIEW", vrule_code="[qa-blocker]",
    )
    test_session.add(blocker)
    await test_session.commit()
    try:
        second = await _plan(client)
        s2 = datetime.fromisoformat(second["proposed_slot"]["start_utc"])
        e2 = datetime.fromisoformat(second["proposed_slot"]["end_utc"])
        assert s2 >= end or e2 <= start, "proposed slot overlaps an existing booking"
    finally:
        await test_session.delete(blocker)
        await test_session.commit()


# SCHED-18 ------------------------------------------------------------------ #
@pytest.mark.xfail(
    strict=False,
    reason="KNOWN GAP: customized_items sent with Approve are mutated in place on the JSON column, so SQLAlchemy "
    "never writes them. The edit is silently dropped and the ORIGINAL draft is what gets executed (SCHED-18).",
)
async def test_sched18_edited_draft_replaces_original_on_approval(client: AsyncClient, test_session: AsyncSession):
    plan = await _plan(client)
    items = [dict(i) for i in plan["items"]]
    marker = "QA custom closing sentence."
    next(i for i in items if i["recipient_role"] == "Candidate")["content_preview"] += f" {marker}"

    res = await client.post(
        f"/api/v1/actionPlans/{plan['id']}/approve",
        json={"approved_by": "QA", "send_immediately": False, "customized_items": items},
    )

    assert res.status_code == 200
    test_session.expire_all()
    stored = (await test_session.execute(select(FollowupPlan.vagent_metadata).where(FollowupPlan.nid == int(plan["id"])))).scalar_one()
    assert marker in " ".join(i["content_preview"] for i in stored["items"])
    await client.post(f"/api/v1/actionPlans/{plan['id']}/undo", json={"reason": "cleanup"})


# SCHED-19 ------------------------------------------------------------------ #
async def test_sched19_planner_survives_llm_failure(client: AsyncClient, test_session: AsyncSession, monkeypatch):
    from app.agent.LlmFactory import LlmFactory

    monkeypatch.setattr(LlmFactory, "get_chat_model", staticmethod(lambda *a, **k: None))
    booked_before = await _agent_bookings(test_session)

    plan = await _plan(client)

    assert plan["status"] in ("PENDING_APPROVAL", "PENDING APPROVAL")
    assert await _agent_bookings(test_session) == booked_before