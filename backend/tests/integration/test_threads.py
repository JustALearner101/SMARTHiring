from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.AppConfig import settings
from app.main import app
from app.middleware.RateLimiterMiddleware import rate_limiter_instance
from app.model.AuditModel import AuditLog
from app.model.CandidateModel import Candidate
from app.model.FollowupModel import FollowupPlan
from app.model.OrchestrationModel import NegotiationThread
from app.model.UserModel import User

THREADS = "/api/v1/negotiationThreads"
REPLY = "/api/v1/orchestrator/inbound-reply"
STATUSES = ["NEGOTIATING", "SCHEDULED", "DEADLOCK_ESCALATED", "EXPIRED"]


@pytest.fixture(autouse=True)
def _safe_environment(monkeypatch):
    monkeypatch.setattr(settings, "SMTP_ENABLED", False)  # never send real email
    rate_limiter_instance.reset()
    yield
    rate_limiter_instance.reset()


@pytest.fixture
async def make_thread(test_session: AsyncSession) -> AsyncGenerator:
    created: list[int] = []

    async def _make(status: str = "NEGOTIATING", round_no: int = 1) -> int:
        cand_id = (await test_session.execute(select(Candidate.nid).order_by(Candidate.nid).limit(1))).scalar_one()
        inter_id = (await test_session.execute(select(User.nid).where(User.vusername == "budi.santoso"))).scalar_one()
        now = datetime.now(UTC)
        thread = NegotiationThread(
            nid_candidate=cand_id,
            nid_interviewer=inter_id,
            ncurrent_round=round_no,
            nmax_rounds=3,
            vstatus=status,
            ddeadline_at=now + timedelta(days=1),
            dlast_activity_at=now,
        )
        test_session.add(thread)
        await test_session.commit()
        created.append(thread.nid)
        return thread.nid

    yield _make
    test_session.expire_all()
    for tid in created:
        row = await test_session.get(NegotiationThread, tid)
        if row:
            await test_session.delete(row)
    await test_session.commit()


async def _get(client: AsyncClient, thread_id: int) -> dict:
    res = await client.get(f"{THREADS}/{thread_id}")
    assert res.status_code == 200, res.text
    return res.json()["data"]


async def _plan_count(session: AsyncSession) -> int:
    return (await session.execute(select(func.count()).select_from(FollowupPlan))).scalar_one()


async def _audit_count(session: AsyncSession, event_type: str) -> int:
    return (
        await session.execute(select(func.count()).select_from(AuditLog).where(AuditLog.vevent_type == event_type))
    ).scalar_one()


# THR-01 / THR-06 ----------------------------------------------------------- #
async def test_thr01_list_returns_paginated_threads_with_required_columns(client: AsyncClient, make_thread):
    thread_id = await make_thread()

    res = await client.get(THREADS)

    assert res.status_code == 200
    page = res.json()["data"]
    assert {"items", "total", "page", "page_size", "total_pages"} <= set(page)
    row = next(t for t in page["items"] if t["id"] == str(thread_id))
    for key in ("candidate_name", "candidate_position", "interviewer_name", "candidate_channel", "status"):
        assert row[key], key


async def test_thr06_detail_shows_timeline_round_and_slot_fields(client: AsyncClient, make_thread):
    thread_id = await make_thread(round_no=2)
    await client.post(f"{THREADS}/{thread_id}/reply", params={"content": "Halo, kami tawarkan Selasa 14:00 WIB"})

    thread = await _get(client, thread_id)

    assert thread["current_round"] == 2 and thread["max_rounds"] == 3
    assert [m["content"] for m in thread["messages"]] == ["Halo, kami tawarkan Selasa 14:00 WIB"]
    assert "agreed_slot" in thread and "deadline_at" in thread


async def test_thr06_unknown_thread_returns_404(client: AsyncClient):
    res = await client.get(f"{THREADS}/99999999")
    assert res.status_code == 404


# THR-04 -------------------------------------------------------------------- #
async def test_thr04_status_filter_returns_only_selected_status(client: AsyncClient, make_thread):
    ids = {status: await make_thread(status) for status in STATUSES}

    for status, thread_id in ids.items():
        res = await client.get(THREADS, params={"status": status, "page_size": 100})
        assert res.status_code == 200
        items = res.json()["data"]["items"]
        assert all(t["status"] == status for t in items), status
        assert str(thread_id) in {t["id"] for t in items}, status

    all_items = (await client.get(THREADS, params={"page_size": 100})).json()["data"]["items"]
    assert {str(i) for i in ids.values()} <= {t["id"] for t in all_items}, "'All Status' must include every status"


# THR-07 -------------------------------------------------------------------- #
async def test_thr07_escalates_after_three_rejections_and_stops_proposing(
    client: AsyncClient, test_session: AsyncSession, make_thread
):
    thread_id = await make_thread()
    body = {"thread_id": thread_id, "sender_role": "CANDIDATE", "channel": "whatsapp", "reply_text": "Cannot make that time"}

    for _ in range(3):
        res = await client.post(REPLY, json=body)
        assert res.status_code == 200, res.text
    plans_after_three = await _plan_count(test_session)
    fourth = await client.post(REPLY, json=body)

    assert fourth.status_code == 200
    assert fourth.json()["data"]["status"] == "DEADLOCK_ESCALATED"
    thread = await _get(client, thread_id)
    assert thread["status"] == "DEADLOCK_ESCALATED"
    assert thread["escalation_reason"]
    assert await _plan_count(test_session) == plans_after_three, "no new proposal after escalation"


# THR-08 -------------------------------------------------------------------- #
@pytest.mark.parametrize("text", ["Can we discuss my salary expectation first?", "Boleh bahas gaji dulu?"])
async def test_thr08_out_of_scope_request_is_escalated_without_a_proposal(
    client: AsyncClient, test_session: AsyncSession, make_thread, text: str
):
    thread_id = await make_thread()
    plans_before = await _plan_count(test_session)
    escalations_before = await _audit_count(test_session, "DEADLOCK_ESCALATED")

    res = await client.post(
        REPLY, json={"thread_id": thread_id, "sender_role": "CANDIDATE", "channel": "email", "reply_text": text}
    )

    assert res.json()["data"]["status"] == "DEADLOCK_ESCALATED"
    assert (await _get(client, thread_id))["status"] == "DEADLOCK_ESCALATED"
    assert await _plan_count(test_session) == plans_before
    assert await _audit_count(test_session, "DEADLOCK_ESCALATED") == escalations_before + 1
    messages = (await _get(client, thread_id))["messages"]
    assert any(m["sender_role"] == "CANDIDATE" and m["content"] == text for m in messages)
    assert all(m["sender_role"] != "AI_ORCHESTRATOR" for m in messages), "AI must not answer on its own"


# THR-09 -------------------------------------------------------------------- #
async def test_thr09_hr_manual_message_appears_in_timeline_and_audit(
    client: AsyncClient, test_session: AsyncSession, make_thread
):
    thread_id = await make_thread()
    audits_before = await _audit_count(test_session, "THREAD_REPLY_SENT")

    res = await client.post(f"{THREADS}/{thread_id}/reply", params={"content": "We can offer Tuesday 14:00 WIB"})

    assert res.status_code == 200
    assert res.json()["data"]["sender_role"] == "HR_ADMIN"
    messages = (await _get(client, thread_id))["messages"]
    assert [m["content"] for m in messages] == ["We can offer Tuesday 14:00 WIB"]
    assert await _audit_count(test_session, "THREAD_REPLY_SENT") == audits_before + 1


async def test_thr09_reply_to_unknown_thread_returns_404(client: AsyncClient):
    res = await client.post(f"{THREADS}/99999999/reply", params={"content": "x"})
    assert res.status_code == 404


# THR-11 -------------------------------------------------------------------- #
async def test_thr11_candidate_confirmation_marks_thread_scheduled(
    client: AsyncClient, test_session: AsyncSession, make_thread
):
    thread_id = await make_thread()
    executed_before = await _audit_count(test_session, "ACTION_EXECUTED")

    res = await client.post(
        REPLY,
        json={"thread_id": thread_id, "sender_role": "CANDIDATE", "channel": "whatsapp", "reply_text": "Yes, that time works"},
    )

    assert res.json()["data"]["status"] == "CONFIRMED"
    assert (await _get(client, thread_id))["status"] == "SCHEDULED"
    assert await _audit_count(test_session, "ACTION_EXECUTED") == executed_before + 1


# Security observation relevant to THR-01 / 06 / 09 -------------------------- #
@pytest.mark.xfail(
    strict=False,
    reason="KNOWN GAP: the negotiation-thread endpoints declare no authentication. Anyone can list threads (with "
    "candidate email/phone), open details and post HR messages without a token.",
)
@pytest.mark.parametrize(
    ("method", "path"),
    [("get", "/api/v1/negotiationThreads"), ("get", "/api/v1/negotiationThreads/{thread_id}"),
     ("post", "/api/v1/negotiationThreads/{thread_id}/reply")],
)
def test_thr_endpoints_require_authentication(method: str, path: str):
    spec = app.openapi()
    assert "security" in spec["paths"]["/api/v1/auditLogs"]["get"], "control: a protected endpoint is marked secured"
    assert "security" in spec["paths"][path][method]