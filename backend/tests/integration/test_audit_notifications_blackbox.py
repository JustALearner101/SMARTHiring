import email
import smtplib
import sys
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import ClassVar

import pytest
from httpx import AsyncClient
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.AppConfig import settings
from app.middleware.RateLimiterMiddleware import rate_limiter_instance
from app.model.AuditModel import AuditLog
from app.model.OrchestrationModel import CalendarEvent, NegotiationThread, ThreadMessage
from app.model.UserModel import User
from app.service.EmailDispatcherService import EmailDispatcherService

API = "/api/v1"
AUDIT = f"{API}/auditLogs"
COMMAND = f"{API}/orchestrator/command"
NORMAL = "Schedule Rina Kusuma's interview with Budi Santoso next week"
PASSWORD = "password123"


@pytest.fixture(autouse=True)
def _safe_environment(monkeypatch):
    monkeypatch.setattr(settings, "SMTP_ENABLED", False)
    rate_limiter_instance.reset()
    yield
    rate_limiter_instance.reset()


@pytest.fixture
def prodlike(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.delitem(sys.modules, "pytest")


async def _auth(client: AsyncClient, username: str) -> dict:
    res = await client.post(f"{API}/auth/login", json={"username": username, "password": PASSWORD})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['data']['access_token']}"}


@pytest.fixture
async def admin(client: AsyncClient) -> dict:
    return await _auth(client, "auditor.it")


@pytest.fixture
async def hr(client: AsyncClient) -> dict:
    return await _auth(client, "hr.admin")


@pytest.fixture
async def santoso(client: AsyncClient) -> dict:
    return await _auth(client, "budi.santoso")


async def _events(client: AsyncClient, admin_headers: dict, after_id: int = 0) -> list[dict]:
    res = await client.get(AUDIT, headers=admin_headers, params={"page_size": 100})
    assert res.status_code == 200, res.text
    return [e for e in res.json()["data"]["items"] if int(e["id"]) > after_id]


async def _last_audit_id(session: AsyncSession) -> int:
    session.expire_all()
    return (await session.execute(select(func.max(AuditLog.nid)))).scalar_one() or 0


async def _new_plan(client: AsyncClient) -> str:
    res = await client.post(COMMAND, json={"command": NORMAL})
    assert res.status_code == 200, res.text
    return res.json()["data"]["id"]


@pytest.fixture
async def rollback_execution(test_session: AsyncSession) -> AsyncGenerator[None, None]:
    """Undo the DB side effects of executing a plan (threads touched, messages, calendar events)."""
    threads = {t.nid: (t.vstatus, t.vagreed_slot, t.dlast_activity_at) for t in (await test_session.execute(select(NegotiationThread))).scalars()}
    max_msg = (await test_session.execute(select(func.coalesce(func.max(ThreadMessage.nid), 0)))).scalar_one()
    max_ev = (await test_session.execute(select(func.coalesce(func.max(CalendarEvent.nid), 0)))).scalar_one()
    yield
    test_session.expire_all()
    await test_session.execute(delete(ThreadMessage).where(ThreadMessage.nid > max_msg))
    await test_session.execute(delete(CalendarEvent).where(CalendarEvent.nid > max_ev))
    await test_session.execute(delete(NegotiationThread).where(NegotiationThread.nid.not_in(list(threads))))
    for nid, (status, slot, last) in threads.items():
        await test_session.execute(
            update(NegotiationThread).where(NegotiationThread.nid == nid).values(vstatus=status, vagreed_slot=slot, dlast_activity_at=last)
        )
    await test_session.commit()


class _FakeSMTP:
    """Stands in for smtplib.SMTP_SSL: records the message instead of connecting anywhere."""

    sent: ClassVar[list[str]] = []
    fail_with: ClassVar[Exception | None] = None

    def __init__(self, *_a, **_k):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_a):
        return False

    def login(self, *_a):
        if _FakeSMTP.fail_with:
            raise _FakeSMTP.fail_with

    def starttls(self):
        pass

    def sendmail(self, _from, _to, msg):
        _FakeSMTP.sent.append(msg)


@pytest.fixture
def fake_smtp(monkeypatch):
    _FakeSMTP.sent, _FakeSMTP.fail_with = [], None
    monkeypatch.setattr(settings, "SMTP_ENABLED", True)
    monkeypatch.setattr(settings, "SMTP_USER", "qa-user")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "qa-pass")
    monkeypatch.setattr(settings, "SMTP_SSL", True)
    monkeypatch.setattr(smtplib, "SMTP_SSL", _FakeSMTP)
    return _FakeSMTP


async def _send(**over):
    args = {
        "to_email": "budi.santoso@example.test", "recipient_name": "Budi Santoso", "subject": "Interview Schedule: Rina",
        "content": "Mohon konfirmasi jadwal.", "slot_wib": "Selasa, 3 Januari 2040 10:00 WIB", "recipient_role": "Interviewer",
        "start_utc": datetime(2040, 1, 3, 3, 0, tzinfo=UTC), "end_utc": datetime(2040, 1, 3, 4, 0, tzinfo=UTC),
    }
    args.update(over)
    return await EmailDispatcherService().send_interview_email(**args)


# =========================================================================== #
# TC-AUD
# =========================================================================== #
async def test_aud01_admin_gets_security_overview(client: AsyncClient, admin: dict):
    stats = await client.get(f"{AUDIT}/stats", headers=admin)
    verify = await client.get(f"{AUDIT}/verify", headers=admin)
    assert stats.status_code == 200 and verify.status_code == 200
    data = stats.json()["data"]
    assert {"total_events", "total_system_errors", "hash_chain_valid"} <= set(data)
    assert verify.json()["data"]["is_valid"] is True and data["hash_chain_valid"] is True


async def test_aud02_list_is_newest_first_with_required_fields(client: AsyncClient, admin: dict):
    items = (await client.get(AUDIT, headers=admin, params={"page_size": 50})).json()["data"]["items"]
    assert len(items) >= 2
    ids = [int(i["id"]) for i in items]
    stamps = [i["timestamp"] for i in items]
    assert ids == sorted(ids, reverse=True) and stamps == sorted(stamps, reverse=True)
    for key in ("event_type", "actor", "title", "timestamp"):
        assert all(i[key] for i in items), key


@pytest.mark.xfail(strict=False, reason="BUG: list title is always 'Event <TYPE>'; the descriptive title written at log time is discarded.")
async def test_aud02_title_is_descriptive(client: AsyncClient, admin: dict):
    items = (await client.get(AUDIT, headers=admin, params={"page_size": 50})).json()["data"]["items"]
    assert any(i["title"] != f"Event {i['event_type']}" for i in items)


async def test_aud03_approve_and_undo_lifecycle_is_recorded_in_order(client: AsyncClient, admin: dict, hr: dict, test_session):
    base = await _last_audit_id(test_session)
    plan_id = await _new_plan(client)
    approve = await client.post(f"{API}/actionPlans/{plan_id}/approve", headers=hr, json={})
    assert approve.status_code == 200, approve.text
    undo = await client.post(f"{API}/actionPlans/{plan_id}/undo", headers=hr, json={"reason": "qa"})
    assert undo.status_code == 200, undo.text

    types = [e["event_type"] for e in reversed(await _events(client, admin, base))]
    for needed in ("PLAN_GENERATED", "HUMAN_APPROVED", "ACTION_UNDONE"):
        assert needed in types, types
    assert types.index("PLAN_GENERATED") < types.index("HUMAN_APPROVED") < types.index("ACTION_UNDONE")


@pytest.mark.xfail(strict=False, reason="GAP: no audit entry for a PASSED guardrail check (only GUARDRAIL_BLOCKED exists) and none for 'plan validated'.")
async def test_aud03_guardrail_pass_and_validation_are_recorded(client: AsyncClient, admin: dict, test_session):
    base = await _last_audit_id(test_session)
    await _new_plan(client)
    types = {e["event_type"] for e in await _events(client, admin, base)}
    assert any("GUARDRAIL" in t for t in types) and any("VALID" in t for t in types)


@pytest.mark.parametrize("method", ["PATCH", "PUT", "DELETE", "POST"])
async def test_aud04_no_edit_or_delete_operation_on_audit_log(client: AsyncClient, admin: dict, method):
    first = (await client.get(AUDIT, headers=admin, params={"page_size": 1})).json()["data"]["items"][0]["id"]
    res = await client.request(method, f"{AUDIT}/{first}", headers=admin, json={"title": "x"})
    assert res.status_code in (404, 405)


@pytest.mark.xfail(strict=False, reason="BUG: verify only checks prev-hash links; editing an entry's text/actor is not detected.")
async def test_aud04_tampering_with_a_log_entry_is_detected(client: AsyncClient, admin: dict, test_session: AsyncSession):
    row = (await test_session.execute(select(AuditLog).order_by(AuditLog.nid.desc()).limit(1))).scalars().one()
    original = row.vmasked_detail
    try:
        await test_session.execute(update(AuditLog).where(AuditLog.nid == row.nid).values(vmasked_detail="TAMPERED"))
        await test_session.commit()
        assert (await client.get(f"{AUDIT}/verify", headers=admin)).json()["data"]["is_valid"] is False
    finally:
        await test_session.execute(update(AuditLog).where(AuditLog.nid == row.nid).values(vmasked_detail=original))
        await test_session.commit()


async def test_aud05_interviewer_cannot_read_audit_logs(client: AsyncClient, santoso: dict):
    for path in (AUDIT, f"{AUDIT}/stats", f"{AUDIT}/verify"):
        assert (await client.get(path, headers=santoso)).status_code == 403, path


@pytest.mark.xfail(strict=False, reason="BUG: API lets HR read audit logs (UI hides the menu, API allows HR and ADMIN).")
async def test_aud05_hr_cannot_read_audit_logs(client: AsyncClient, hr: dict):
    assert (await client.get(AUDIT, headers=hr)).status_code == 403


@pytest.mark.xfail(strict=False, reason="BUG (High): /systemLogs needs no token and returns stack traces.")
async def test_aud05_system_logs_require_authentication(client: AsyncClient, prodlike):
    assert (await client.get(f"{API}/systemLogs")).status_code in (401, 403)


async def test_aud07_human_approved_entry_has_plan_id_timestamp_and_undo_window(client: AsyncClient, admin: dict, hr: dict, test_session):
    base = await _last_audit_id(test_session)
    plan_id = await _new_plan(client)
    await client.post(f"{API}/actionPlans/{plan_id}/approve", headers=hr, json={})
    approved = next(e for e in await _events(client, admin, base) if e["event_type"] == "HUMAN_APPROVED")
    assert f"#{plan_id}" in approved["description"] and "60-second" in approved["description"]
    assert approved["timestamp"] and approved["actor"]
    await client.post(f"{API}/actionPlans/{plan_id}/undo", headers=hr, json={"reason": "cleanup"})


@pytest.mark.xfail(strict=False, reason="BUG: audit 'actor' of approve is taken from the request body (approved_by), so it can be forged.")
async def test_aud07_approver_identity_comes_from_the_token(client: AsyncClient, admin: dict, hr: dict, test_session):
    base = await _last_audit_id(test_session)
    plan_id = await _new_plan(client)
    await client.post(f"{API}/actionPlans/{plan_id}/approve", headers=hr, json={"approved_by": "Someone Else"})
    approved = next(e for e in await _events(client, admin, base) if e["event_type"] == "HUMAN_APPROVED")
    await client.post(f"{API}/actionPlans/{plan_id}/undo", headers=hr, json={"reason": "cleanup"})
    assert approved["actor"] != "Someone Else"


@pytest.mark.xfail(strict=False, reason="BUG: undo is always logged with the fixed actor 'HR Admin', not the logged-in user.")
async def test_aud07_undo_actor_is_the_logged_in_user(client: AsyncClient, admin: dict, test_session):
    base = await _last_audit_id(test_session)
    plan_id = await _new_plan(client)
    await client.post(f"{API}/actionPlans/{plan_id}/approve", headers=admin, json={"approved_by": "Auditor IT"})
    await client.post(f"{API}/actionPlans/{plan_id}/undo", headers=admin, json={"reason": "qa"})
    undone = next(e for e in await _events(client, admin, base) if e["event_type"] == "ACTION_UNDONE")
    me = (await test_session.execute(select(User).where(User.vusername == "auditor.it"))).scalars().one()
    assert undone["actor"] == me.vname


# =========================================================================== #
# TC-NTF
# =========================================================================== #
async def test_ntf01_hr_bell_lists_plan_awaiting_approval(client: AsyncClient, hr: dict):
    plan_id = await _new_plan(client)
    res = await client.get(f"{API}/notifications", headers=hr)
    assert res.status_code == 200
    items = res.json()["data"]
    mine = next(n for n in items if n["id"] == f"plan-{plan_id}")
    assert mine["category"] == "APPROVAL" and mine["title"] and mine["timestamp"]
    stamps = [n["timestamp"] for n in items]
    assert stamps == sorted(stamps, reverse=True)


async def test_ntf01_admin_sees_security_alerts_and_interviewer_sees_own(client: AsyncClient, admin: dict, santoso: dict):
    adm = (await client.get(f"{API}/notifications", headers=admin)).json()["data"]
    assert all(n["category"] in {"SECURITY", "APPROVAL", "TRIAGE"} for n in adm)
    ivw = (await client.get(f"{API}/notifications", headers=santoso)).json()["data"]
    assert ivw and all(n["category"] == "INTERVIEW" for n in ivw)


async def test_ntf02_full_list_endpoint_works_for_every_role(client: AsyncClient, hr: dict, admin: dict, santoso: dict):
    for headers in (hr, admin, santoso):
        res = await client.get(f"{API}/notifications", headers=headers)
        assert res.status_code == 200 and isinstance(res.json()["data"], list)
        assert all({"id", "title", "message", "timestamp", "link"} <= set(n) for n in res.json()["data"])


@pytest.mark.xfail(strict=False, reason="GAP: notifications have no read/unread state, so the badge cannot reflect unread items.")
async def test_ntf01_notifications_carry_read_state(client: AsyncClient, hr: dict):
    await _new_plan(client)
    first = (await client.get(f"{API}/notifications", headers=hr)).json()["data"][0]
    assert "read" in first or "is_read" in first


async def test_ntf03_invitation_has_correct_utc_time_and_ics(fake_smtp):
    res = await _send()
    assert res["success"] is True and res["simulated"] is False and len(fake_smtp.sent) == 1
    msg = email.message_from_string(fake_smtp.sent[0])
    cal = [p for p in msg.walk() if p.get_content_type() == "text/calendar"]
    assert cal
    ics = cal[0].get_payload(decode=True).decode()
    for line in ("BEGIN:VCALENDAR", "METHOD:REQUEST", "DTSTART:20400103T030000Z", "DTEND:20400103T040000Z", "END:VEVENT"):
        assert line in ics, line
    assert "mailto:budi.santoso@example.test" in ics
    attachment = next(p for p in msg.walk() if p.get_filename() == "invite.ics")
    assert attachment is not None
    html = next(p for p in msg.walk() if p.get_content_type() == "text/html").get_payload(decode=True).decode()
    assert "10:00 WIB" in html


@pytest.mark.xfail(strict=False, reason="BUG: executor never passes start_utc/end_utc, so the .ics time is 'now + 2 days 3h', not the agreed slot.")
async def test_ntf03_executed_plan_passes_real_slot_time_to_ics(client: AsyncClient, hr: dict, monkeypatch, rollback_execution):
    seen: list[dict] = []

    async def _spy(self, **kwargs):
        seen.append(kwargs)
        return {"success": True, "simulated": True, "message_id": "x", "recipient": kwargs["to_email"], "error": None}

    monkeypatch.setattr(EmailDispatcherService, "send_interview_email", _spy)
    plan_id = await _new_plan(client)
    res = await client.post(f"{API}/actionPlans/{plan_id}/approve", headers=hr, json={"send_immediately": True})
    assert res.status_code == 200, res.text
    assert seen and all(k.get("start_utc") is not None for k in seen)


async def test_ntf04_email_has_required_headers_footer_and_text_alternative(fake_smtp):
    await _send()
    msg = email.message_from_string(fake_smtp.sent[0])
    for header in ("From", "To", "Subject", "Date", "Message-ID", "Reply-To", "List-Unsubscribe", "Auto-Submitted"):
        assert msg[header], header
    types = {p.get_content_type() for p in msg.walk()}
    assert {"text/plain", "text/html", "text/calendar"} <= types
    html = next(p for p in msg.walk() if p.get_content_type() == "text/html").get_payload(decode=True).decode()
    assert "Unsubscribe" in html and "Jakarta" in html and "Privacy Policy" in html


async def test_ntf05_smtp_disabled_runs_in_simulation_mode(client: AsyncClient, hr: dict, admin: dict, monkeypatch, test_session, rollback_execution):
    def _boom(*_a, **_k):
        raise AssertionError("real SMTP connection attempted while SMTP_ENABLED=false")

    monkeypatch.setattr(smtplib, "SMTP_SSL", _boom)
    monkeypatch.setattr(smtplib, "SMTP", _boom)
    base = await _last_audit_id(test_session)
    plan_id = await _new_plan(client)
    res = await client.post(f"{API}/actionPlans/{plan_id}/approve", headers=hr, json={"send_immediately": True})
    assert res.status_code == 200, res.text

    events = await _events(client, admin, base)
    types = [e["event_type"] for e in events]
    assert "ACTION_EXECUTED" in types and "EMAIL_DISPATCHED" in types and "EMAIL_DISPATCH_FAILED" not in types


async def test_ntf06_smtp_failure_is_logged_and_does_not_crash(client: AsyncClient, hr: dict, admin: dict, fake_smtp, test_session, rollback_execution):
    fake_smtp.fail_with = smtplib.SMTPAuthenticationError(535, b"bad credentials")
    base = await _last_audit_id(test_session)
    plan_id = await _new_plan(client)
    res = await client.post(f"{API}/actionPlans/{plan_id}/approve", headers=hr, json={"send_immediately": True})
    assert res.status_code == 200, res.text

    failed = [e for e in await _events(client, admin, base) if e["event_type"] == "EMAIL_DISPATCH_FAILED"]
    assert failed and ("bad credentials" in failed[0]["description"] or "535" in failed[0]["description"])
    assert fake_smtp.sent == []


@pytest.mark.xfail(strict=False, reason="BUG: after e-mail delivery fails the plan is still reported as EXECUTED; the API response hides the failure.")
async def test_ntf06_failed_delivery_is_not_reported_as_executed(client: AsyncClient, hr: dict, fake_smtp, rollback_execution):
    fake_smtp.fail_with = smtplib.SMTPAuthenticationError(535, b"bad credentials")
    plan_id = await _new_plan(client)
    res = await client.post(f"{API}/actionPlans/{plan_id}/approve", headers=hr, json={"send_immediately": True})
    body = res.json()
    assert res.status_code >= 400 or body["data"]["status"] != "EXECUTED"


async def test_ntf_dispatcher_failure_result_is_returned_not_raised(fake_smtp):
    fake_smtp.fail_with = smtplib.SMTPAuthenticationError(535, b"bad credentials")
    res = await _send()
    assert res["success"] is False and res["simulated"] is False and "535" in res["error"]