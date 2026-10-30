from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.AgentState import OrchestratorAgentState
from app.agent.OrchestratorGraph import orchestrator_checkpointer
from app.agent.PlannerTriageNode import PlannerTriageNode
from app.model.OrchestrationModel import NegotiationThread
from app.repository.CalendarMatrixRepository import CalendarMatrixRepository


async def test_calendar_matrix_find_available_slots(test_session: AsyncSession):
    cal_repo = CalendarMatrixRepository(test_session)
    now = datetime.now(UTC)

    # Next Tuesday (weekday = 1)
    days_ahead = (1 - now.weekday() + 7) % 7 or 7
    target_tuesday = (now + timedelta(days=days_ahead)).date()

    slots = await cal_repo.find_available_slots(user_id=1, target_date=target_tuesday)
    assert len(slots) > 0
    for s in slots:
        assert "start_utc" in s
        assert "end_utc" in s
        assert "WIB" in s["formatted_wib"]


async def test_calendar_matrix_friday_prayer_blackout(test_session: AsyncSession):
    cal_repo = CalendarMatrixRepository(test_session)
    now = datetime.now(UTC)

    # Next Friday (weekday = 4)
    days_ahead = (4 - now.weekday() + 7) % 7 or 7
    target_friday = (now + timedelta(days=days_ahead)).date()

    slots = await cal_repo.find_available_slots(user_id=1, target_date=target_friday)
    assert len(slots) > 0
    for s in slots:
        time_str = s["time_str"]
        # No slot starting in blackout 11:30 - 13:00
        assert time_str not in ("11:30", "12:00", "12:30")


async def test_planner_llm_structured_output_with_real_slots():
    now = datetime.now(UTC)
    mock_slots = [
        {
            "start_utc": (now + timedelta(days=3, hours=3)).isoformat(),
            "end_utc": (now + timedelta(days=3, hours=4)).isoformat(),
            "time_str": "10:00",
            "formatted_wib": "Kamis, 05 Nov 2026, 10:00 WIB",
            "formatted_wita": "Kamis, 05 Nov 2026, 11:00 WITA",
        },
        {
            "start_utc": (now + timedelta(days=3, hours=7)).isoformat(),
            "end_utc": (now + timedelta(days=3, hours=8)).isoformat(),
            "time_str": "14:00",
            "formatted_wib": "Kamis, 05 Nov 2026, 14:00 WIB",
            "formatted_wita": "Kamis, 05 Nov 2026, 15:00 WITA",
        },
    ]

    state: OrchestratorAgentState = {
        "command": "Jadwalkan technical interview untuk Rina Kusuma jam 14:00 WIB",
        "candidate_name": "Rina Kusuma",
        "candidate_position": "Senior Frontend Engineer",
        "candidate_channel": "email",
        "interviewer_name": "Budi Santoso",
        "interviewer_role": "VP of Engineering",
        "interviewer_timezone": "WIB",
        "negotiation_round": 1,
        "max_rounds": 3,
        "available_slots": mock_slots,
    }

    updates = await PlannerTriageNode.run(state)
    assert updates["is_high_impact"] is True
    assert len(updates["sources_cited"]) == 3
    assert len(updates["items"]) == 3
    assert updates["proposed_slot"]["formatted_wib"] == "Kamis, 05 Nov 2026, 14:00 WIB"


async def test_orchestrator_inbound_confirm_api(client: AsyncClient, test_session: AsyncSession):
    # Setup thread
    thread = NegotiationThread(
        nid_candidate=1,
        nid_interviewer=1,
        ncurrent_round=1,
        nmax_rounds=3,
        vstatus="NEGOTIATING",
    )
    test_session.add(thread)
    await test_session.commit()
    await test_session.refresh(thread)

    try:
        res = await client.post(
            "/api/v1/orchestrator/inbound-reply",
            json={
                "thread_id": thread.nid,
                "sender_role": "CANDIDATE",
                "channel": "whatsapp",
                "reply_text": "Halo kak, saya siap dan bisa di jadwal tersebut! Terima kasih banyak.",
            },
            headers={"X-Bypass-Rate-Limit": "1"},
        )
        assert res.status_code == 200
        body = res.json()["data"]
        assert body["status"] == "CONFIRMED"
    finally:
        await test_session.delete(thread)
        await test_session.commit()


async def test_orchestrator_inbound_out_of_scope_api(client: AsyncClient, test_session: AsyncSession):
    thread = NegotiationThread(
        nid_candidate=1,
        nid_interviewer=1,
        ncurrent_round=1,
        nmax_rounds=3,
        vstatus="NEGOTIATING",
    )
    test_session.add(thread)
    await test_session.commit()
    await test_session.refresh(thread)

    try:
        res = await client.post(
            "/api/v1/orchestrator/inbound-reply",
            json={
                "thread_id": thread.nid,
                "sender_role": "CANDIDATE",
                "channel": "whatsapp",
                "reply_text": "Bisa diskusi soal penawaran gaji pokok dan benefit asuransi sebelum kita wawancara?",
            },
            headers={"X-Bypass-Rate-Limit": "1"},
        )
        assert res.status_code == 200
        body = res.json()["data"]
        assert body["status"] == "DEADLOCK_ESCALATED"
        assert "outside the agent's authority" in body["message"]
    finally:
        await test_session.delete(thread)
        await test_session.commit()


async def test_orchestrator_inbound_round_limit_escalation_api(client: AsyncClient, test_session: AsyncSession):
    # Thread already at round 3
    thread = NegotiationThread(
        nid_candidate=1,
        nid_interviewer=1,
        ncurrent_round=3,
        nmax_rounds=3,
        vstatus="NEGOTIATING",
    )
    test_session.add(thread)
    await test_session.commit()
    await test_session.refresh(thread)

    try:
        res = await client.post(
            "/api/v1/orchestrator/inbound-reply",
            json={
                "thread_id": thread.nid,
                "sender_role": "CANDIDATE",
                "channel": "whatsapp",
                "reply_text": "Saya tetap tidak bisa di hari tersebut, apakah ada opsi minggu depannya lagi?",
            },
            headers={"X-Bypass-Rate-Limit": "1"},
        )
        assert res.status_code == 200
        body = res.json()["data"]
        assert body["status"] == "DEADLOCK_ESCALATED"
        assert "3 rounds" in body["message"]
    finally:
        await test_session.delete(thread)
        await test_session.commit()


def test_orchestrator_checkpointer_initialized():
    assert orchestrator_checkpointer is not None
