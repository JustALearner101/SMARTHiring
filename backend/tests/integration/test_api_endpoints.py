import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


# ------------------ OpenAPI & Schema Verification ------------------ #
async def test_openapi_schema_contains_all_tags(client: AsyncClient):
    response = await client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    tags = [t["name"] for t in schema.get("tags", [])]

    # Verify all 16 domains are present in tags
    expected_tags = [
        "CandidateManagement",
        "ContactsDirectory",
        "NationalHolidays",
        "OperationalPolicies",
        "AssessmentRubrics",
        "OrchestratorCommands",
        "ActionPlans",
        "NegotiationThreads",
        "SimulatorEmail",
        "SimulatorWhatsApp",
        "InterviewSessions",
        "InterviewTranscripts",
        "InterviewDecisions",
        "CalendarMatrix",
        "SlotConflictChecker",
        "AuditLogs",
    ]
    for tag in expected_tags:
        assert tag in tags, f"Tag {tag} missing from OpenAPI tags"

    paths = schema.get("paths", {})
    assert "/api/v1/candidates" in paths
    assert "/api/v1/contacts" in paths
    assert "/api/v1/holidays" in paths
    assert "/api/v1/operationalRules" in paths
    assert "/api/v1/rubrics" in paths
    assert "/api/v1/orchestrator/command" in paths
    assert "/api/v1/actionPlans/current" in paths
    assert "/api/v1/negotiationThreads" in paths
    assert "/api/v1/simulator/email/inbox" in paths
    assert "/api/v1/simulator/whatsapp/messages" in paths
    assert "/api/v1/interviews/sessions" in paths
    assert "/api/v1/interviews/transcripts/{interview_id}" in paths
    assert "/api/v1/interviews/decisions/{interview_id}" in paths
    assert "/api/v1/calendarMatrix/events" in paths
    assert "/api/v1/slotConflictChecker/check" in paths
    assert "/api/v1/auditLogs" in paths


# ------------------ Candidate Endpoints ------------------ #
async def test_candidate_crud_flow(client: AsyncClient):
    suffix = uuid.uuid4().hex[:6]
    # 1. Create candidate
    payload = {
        "name": f"Ahmad Fauzi {suffix}",
        "email": f"ahmad.{suffix}@example.com",
        "phone": "+6281299998888",
        "preferred_channel": "whatsapp",
        "applied_position": "Backend Engineer",
        "status": "SCREENING",
        "timezone": "WIB",
        "resume_url": "https://storage.smarthiring.ai/resumes/ahmad.pdf",
        "notes": "Strong Python and FastAPI experience",
    }
    create_res = await client.post("/api/v1/candidates", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()["data"]
    cand_id = created_data["id"]
    assert created_data["name"] == f"Ahmad Fauzi {suffix}"
    assert "CAND-2026-" in created_data["candidate_code"]

    # 2. List candidates
    list_res = await client.get("/api/v1/candidates")
    assert list_res.status_code == 200
    list_data = list_res.json()["data"]
    assert list_data["total"] >= 1
    assert any(c["id"] == cand_id for c in list_data["items"])

    # 3. Get candidate detail
    get_res = await client.get(f"/api/v1/candidates/{cand_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["email"] == f"ahmad.{suffix}@example.com"

    # 4. Patch candidate
    patch_res = await client.patch(f"/api/v1/candidates/{cand_id}", json={"status": "INTERVIEW_SCHEDULED"})
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["status"] == "INTERVIEW_SCHEDULED"


# ------------------ Contact Endpoints ------------------ #
async def test_contact_crud_flow(client: AsyncClient):
    suffix = uuid.uuid4().hex[:6]
    # 1. Create contact
    payload = {
        "employee_id": f"EMP-ENG-{suffix}",
        "name": "Bambang Setiawan",
        "email": f"bambang.{suffix}@company.com",
        "phone": "+6281234500000",
        "department": "Engineering",
        "role": "Staff Backend Engineer",
        "timezone": "WIB",
        "working_hours": "09:00 - 17:00",
    }
    create_res = await client.post("/api/v1/contacts", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()["data"]
    user_id = created_data["id"]
    assert created_data["avatar_initials"] == "BS"

    # 2. List contacts
    list_res = await client.get("/api/v1/contacts?department=Engineering")
    assert list_res.status_code == 200
    contacts = list_res.json()["data"]
    assert any(c["id"] == user_id for c in contacts)

    # 3. Patch contact
    patch_res = await client.patch(f"/api/v1/contacts/{user_id}", json={"working_hours": "08:30 - 17:30"})
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["working_hours"] == "08:30 - 17:30"


# ------------------ Holiday Endpoints ------------------ #
async def test_holiday_endpoints(client: AsyncClient):
    # Check if holiday exists first
    list_before = await client.get("/api/v1/holidays?year=2026")
    existing_dates = [h["date"] for h in list_before.json()["data"]]

    test_date = "2026-08-17"
    if test_date not in existing_dates:
        payload = {
            "date": test_date,
            "name": "Hari Kemerdekaan RI",
            "is_joint_leave": False,
        }
        res = await client.post("/api/v1/holidays", json=payload)
        assert res.status_code == 201
        assert res.json()["data"]["name"] == "Hari Kemerdekaan RI"

    # List holidays
    list_res = await client.get("/api/v1/holidays?year=2026")
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) >= 1


# ------------------ Operational Policy Endpoints ------------------ #
async def test_operational_policy_endpoints(client: AsyncClient):
    # 1. Get policy
    get_res = await client.get("/api/v1/operationalRules")
    assert get_res.status_code == 200
    policy = get_res.json()["data"]
    assert policy["work_start_time"] == "09:00"
    assert policy["max_negotiation_rounds"] == 3

    # 2. Update policy
    policy["buffer_minutes"] = 20
    put_res = await client.put("/api/v1/operationalRules", json=policy)
    assert put_res.status_code == 200
    assert put_res.json()["data"]["buffer_minutes"] == 20


# ------------------ Rubrics Endpoint ------------------ #
async def test_rubrics_endpoint(client: AsyncClient):
    res = await client.get("/api/v1/rubrics")
    assert res.status_code == 200
    assert isinstance(res.json()["data"], list)


# ------------------ Orchestrator Command Endpoints ------------------ #
async def test_orchestrator_command_endpoints(client: AsyncClient):
    # 1. List scenarios
    scen_res = await client.get("/api/v1/orchestrator/scenarios")
    assert scen_res.status_code == 200
    scenarios = scen_res.json()["data"]
    assert len(scenarios) >= 4

    # 2. Post command
    cmd_payload = {"command": "Jadwalkan technical interview untuk Rina Kusuma hari Rabu depan."}
    cmd_res = await client.post("/api/v1/orchestrator/command", json=cmd_payload)
    assert cmd_res.status_code == 200
    plan_data = cmd_res.json()["data"]
    assert plan_data["status"] == "PENDING_APPROVAL"
    assert len(plan_data["items"]) == 3


# ------------------ Action Plan Endpoints ------------------ #
async def test_action_plan_lifecycle_endpoints(client: AsyncClient):
    # 1. Trigger plan creation via command
    await client.post("/api/v1/orchestrator/command", json={"command": "Buat interview plan untuk Rina."})

    # 2. Get current plan
    curr_res = await client.get("/api/v1/actionPlans/current")
    assert curr_res.status_code == 200
    plan = curr_res.json()["data"]
    plan_id = plan["id"]

    # 3. Approve plan -> enter undo window
    approve_res = await client.post(f"/api/v1/actionPlans/{plan_id}/approve", json={"approved_by": "HR Manager"})
    assert approve_res.status_code == 200
    assert approve_res.json()["data"]["status"] == "UNDO_WINDOW"

    # 4. Undo plan within window
    undo_res = await client.post(f"/api/v1/actionPlans/{plan_id}/undo", json={"reason": "Candidate requested reschedule"})
    assert undo_res.status_code == 200
    assert undo_res.json()["data"]["status"] == "UNDONE"


# ------------------ Negotiation Threads Endpoints ------------------ #
async def test_negotiation_threads_endpoint(client: AsyncClient):
    # 1. List threads
    res = await client.get("/api/v1/negotiationThreads")
    assert res.status_code == 200
    data = res.json()["data"]
    assert "items" in data
    assert "total" in data

    # 2. Get thread detail
    if data["items"]:
        thread_id = data["items"][0]["id"]
        detail_res = await client.get(f"/api/v1/negotiationThreads/{thread_id}")
        assert detail_res.status_code == 200
        assert detail_res.json()["data"]["id"] == thread_id


# ------------------ Simulator Endpoints ------------------ #
async def test_simulator_endpoints(client: AsyncClient):
    # 1. Email inbox
    email_res = await client.get("/api/v1/simulator/email/inbox")
    assert email_res.status_code == 200
    assert len(email_res.json()["data"]) >= 1

    # 2. WhatsApp messages
    wa_res = await client.get("/api/v1/simulator/whatsapp/messages")
    assert wa_res.status_code == 200
    assert len(wa_res.json()["data"]) >= 1

    # 3. Send WhatsApp message
    send_res = await client.post("/api/v1/simulator/whatsapp/send?thread_id=th-001&text=Saya+bisa+hadir&sender=candidate")
    assert send_res.status_code == 200
    assert send_res.json()["data"]["text"] == "Saya bisa hadir"

    # 4. Quick presets
    qp_res = await client.get("/api/v1/simulator/whatsapp/quickPresets")
    assert qp_res.status_code == 200
    assert len(qp_res.json()["data"]) == 4

    # 5. Notifications
    notif_res = await client.get("/api/v1/simulator/whatsapp/notifications")
    assert notif_res.status_code == 200
    assert len(notif_res.json()["data"]) >= 1


# ------------------ Interview Sessions & Sub-resources ------------------ #
async def test_interview_sessions_and_upload(client: AsyncClient):
    # 1. List sessions
    res = await client.get("/api/v1/interviews/sessions")
    assert res.status_code == 200
    assert "items" in res.json()["data"]

    # 2. Upload interview session
    upload_payload = {
        "candidate_id": "1",
        "profile_id": "1",
        "consent_status": "GRANTED",
        "audio_url": "https://storage.smarthiring.ai/interviews/sample.mp3",
        "audio_duration": "30:00",
        "notes": "Full session recording",
    }
    upload_res = await client.post("/api/v1/interviews/sessions/upload", json=upload_payload)
    assert upload_res.status_code == 201
    session_data = upload_res.json()["data"]
    session_id = session_data["id"]
    assert session_data["consent_status"] == "GRANTED"

    # 3. Get session detail
    detail_res = await client.get(f"/api/v1/interviews/sessions/{session_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["data"]["id"] == session_id

    # 4. Get transcripts for this session
    transcript_res = await client.get(f"/api/v1/interviews/transcripts/{session_id}")
    assert transcript_res.status_code == 200
    assert isinstance(transcript_res.json()["data"], list)

    # 5. Submit HR decision for this session
    decision_payload = {
        "decision": "ADVANCE",
        "notes": "Strong candidate performance",
        "decided_by": "HR Director",
    }
    decision_res = await client.post(f"/api/v1/interviews/decisions/{session_id}", json=decision_payload)
    assert decision_res.status_code == 200
    assert decision_res.json()["data"]["decision"] == "ADVANCE"


# ------------------ Calendar Matrix Endpoints ------------------ #
async def test_calendar_matrix_endpoints(client: AsyncClient):
    res = await client.get("/api/v1/calendarMatrix/events?start_date=2026-10-01&end_date=2026-10-31")
    assert res.status_code == 200
    assert isinstance(res.json()["data"], list)


# ------------------ Slot Conflict Checker Endpoints ------------------ #
async def test_slot_conflict_checker_endpoint(client: AsyncClient):
    # Test valid slot on a Monday
    valid_payload = {
        "interviewer_id": "1",
        "date": "2026-10-26",
        "time": "10:00",
        "duration_minutes": 60,
        "timezone": "WIB",
    }
    res = await client.post("/api/v1/slotConflictChecker/check", json=valid_payload)
    assert res.status_code == 200
    assert res.json()["data"]["is_available"] is True

    # Test Friday prayer blackout (11:30 - 13:00)
    friday_payload = {
        "interviewer_id": "1",
        "date": "2026-10-30",
        "time": "12:00",
        "duration_minutes": 60,
        "timezone": "WIB",
    }
    friday_res = await client.post("/api/v1/slotConflictChecker/check", json=friday_payload)
    assert friday_res.status_code == 200
    assert friday_res.json()["data"]["is_available"] is False
    assert friday_res.json()["data"]["status"] == "BLOCKED_FRIDAY_PRAYER"


# ------------------ Audit Log Endpoints ------------------ #
async def test_audit_logs_endpoint(client: AsyncClient):
    res = await client.get("/api/v1/auditLogs")
    assert res.status_code == 200
    assert "items" in res.json()["data"]
    assert "total" in res.json()["data"]
