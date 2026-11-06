import asyncio
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

    # 5. Block duplicate active application for same email + same position
    dup_res = await client.post("/api/v1/candidates", json=payload)
    assert dup_res.status_code == 409

    # 6. Once REJECTED, allow 1-click Re-apply (creates Cycle #2 at SCREENING while keeping Cycle #1 REJECTED)
    rej_res = await client.patch(f"/api/v1/candidates/{cand_id}", json={"status": "REJECTED"})
    assert rej_res.status_code == 200
    reapply_res = await client.post(
        f"/api/v1/candidates/{cand_id}/reapply",
        json={"notes": "Re-applying after 6 months upskilling"},
    )
    assert reapply_res.status_code == 201
    reapplied = reapply_res.json()["data"]
    assert reapplied["status"] == "SCREENING"
    assert reapplied["application_cycle"] == 2
    assert reapplied["previous_application_id"] == cand_id
    assert reapplied["id"] != cand_id

    # Original rejected cycle remains untouched for immutable audit history
    orig_res = await client.get(f"/api/v1/candidates/{cand_id}")
    assert orig_res.json()["data"]["status"] == "REJECTED"

    # Clean up test candidates so database remains clean
    await client.delete(f"/api/v1/candidates/{reapplied['id']}", headers={"X-Demo-Role": "HR"})
    await client.delete(f"/api/v1/candidates/{cand_id}", headers={"X-Demo-Role": "HR"})


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

    # 4. Clean up test contact so tblm_user stays clean
    del_res = await client.delete(f"/api/v1/contacts/{user_id}", headers={"X-Demo-Role": "ADMIN"})
    assert del_res.status_code == 200


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

    # 2. Update policy (restore the original value afterwards so the shared dev DB
    #    does not keep a mutated buffer that contradicts the documented default).
    original_buffer = policy["buffer_minutes"]
    policy["buffer_minutes"] = 20
    put_res = await client.put("/api/v1/operationalRules", json=policy)
    assert put_res.status_code == 200
    assert put_res.json()["data"]["buffer_minutes"] == 20

    policy["buffer_minutes"] = original_buffer
    restore_res = await client.put("/api/v1/operationalRules", json=policy)
    assert restore_res.status_code == 200
    assert restore_res.json()["data"]["buffer_minutes"] == original_buffer


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
    assert plan_data["status"] == "PENDING APPROVAL"
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

    # 2. Upload interview session (owned by default HR actor)
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

    # 5. Submit 1-time immutable HR decision (ADVANCE -> NEXT_INTERVIEW -> ESCALATED)
    decision_payload = {
        "decision": "ADVANCE",
        "next_stage": "NEXT_INTERVIEW",
        "notes": "Strong candidate performance in HR round",
    }
    decision_res = await client.post(f"/api/v1/interviews/decisions/{session_id}", json=decision_payload)
    assert decision_res.status_code == 200
    assert decision_res.json()["data"]["decision"] == "ADVANCE"
    assert decision_res.json()["data"]["next_stage"] == "NEXT_INTERVIEW"
    assert decision_res.json()["data"]["workflow_status"] == "FINALIZED"
    assert decision_res.json()["data"]["resulting_candidate_status"] == "ESCALATED"

    cand_after_next = await client.get("/api/v1/candidates/1")
    assert cand_after_next.json()["data"]["status"] == "ESCALATED"

    # 6. Attempting to overwrite an already FINALIZED decision MUST be rejected with 403 Forbidden
    overwrite_res = await client.post(
        f"/api/v1/interviews/decisions/{session_id}",
        json={"decision": "REJECT", "notes": "Attempted illegal overwrite"},
    )
    assert overwrite_res.status_code == 403

    # 7. Fresh session for Technical Test transition (ADVANCE -> TECHNICAL_TEST)
    s2 = await client.post("/api/v1/interviews/sessions/upload", json=upload_payload)
    assert s2.status_code == 201
    s2_id = s2.json()["data"]["id"]
    tech_test_res = await client.post(
        f"/api/v1/interviews/decisions/{s2_id}",
        json={"decision": "ADVANCE", "next_stage": "TECHNICAL_TEST", "notes": "Proceed to take-home test"},
    )
    assert tech_test_res.status_code == 200
    assert tech_test_res.json()["data"]["resulting_candidate_status"] == "TECHNICAL_TEST"

    # 8. Fresh session for Final Offering transition (ADVANCE -> OFFERED)
    s3 = await client.post("/api/v1/interviews/sessions/upload", json=upload_payload)
    assert s3.status_code == 201
    s3_id = s3.json()["data"]["id"]
    offer_res = await client.post(
        f"/api/v1/interviews/decisions/{s3_id}",
        json={"decision": "ADVANCE", "next_stage": "OFFERED", "notes": "Passed all stages, extend offer"},
    )
    assert offer_res.status_code == 200
    assert offer_res.json()["data"]["resulting_candidate_status"] == "OFFERED"


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


# ------------------ Latest Activity First Sorting Verification ------------------ #
async def test_latest_activity_first_sorting(client: AsyncClient):
    uid_a = uuid.uuid4().hex[:6]
    uid_b = uuid.uuid4().hex[:6]

    res_a = await client.post(
        "/api/v1/candidates",
        json={
            "name": f"Sort Cand A {uid_a}",
            "email": f"sort.a.{uid_a}@example.com",
            "phone": "+628110000001",
            "preferred_channel": "whatsapp",
            "applied_position": "QA Engineer",
            "timezone": "WIB",
        },
    )
    assert res_a.status_code == 201
    cand_a_id = res_a.json()["data"]["id"]

    await asyncio.sleep(0.02)

    res_b = await client.post(
        "/api/v1/candidates",
        json={
            "name": f"Sort Cand B {uid_b}",
            "email": f"sort.b.{uid_b}@example.com",
            "phone": "+628110000002",
            "preferred_channel": "email",
            "applied_position": "Backend Engineer",
            "timezone": "WIB",
        },
    )
    assert res_b.status_code == 201
    cand_b_id = res_b.json()["data"]["id"]

    # Newly added Candidate B must appear at position #1 (index 0)
    list_after_create = await client.get("/api/v1/candidates?page_size=20")
    assert list_after_create.status_code == 200
    items_after_create = list_after_create.json()["data"]["items"]
    assert items_after_create[0]["id"] == cand_b_id

    await asyncio.sleep(0.02)

    # Editing Candidate A must bump dmodi and move Candidate A to position #1 (index 0)
    patch_a = await client.patch(
        f"/api/v1/candidates/{cand_a_id}",
        json={"notes": "Updated notes so Candidate A jumps to top"},
    )
    assert patch_a.status_code == 200

    list_after_edit = await client.get("/api/v1/candidates?page_size=20")
    assert list_after_edit.status_code == 200
    items_after_edit = list_after_edit.json()["data"]["items"]
    assert items_after_edit[0]["id"] == cand_a_id

    # Clean up unreferenced test candidates via guarded DELETE endpoint
    del_a = await client.delete(f"/api/v1/candidates/{cand_a_id}")
    assert del_a.status_code == 200
    del_b = await client.delete(f"/api/v1/candidates/{cand_b_id}")
    assert del_b.status_code == 200


# ------------------ Eval #2 & #4: Contact Credentials, Login & Soft Deactivation ------------------ #
async def test_contact_credentials_and_immediate_login(client: AsyncClient):
    suffix = uuid.uuid4().hex[:6]
    username = f"interviewer.{suffix}"
    password = "SecurePass123!"

    create_res = await client.post(
        "/api/v1/contacts",
        json={
            "employee_id": f"EMP-AUTH-{suffix}",
            "name": f"Dewi Anggraini {suffix}",
            "username": username,
            "password": password,
            "system_role": "INTERVIEWER",
            "email": f"dewi.{suffix}@company.com",
            "phone": "+6281277778888",
            "department": "Data Science",
            "role": "Lead Data Scientist",
            "timezone": "WIB",
            "working_hours": "09:00 - 17:00",
        },
        headers={"X-Demo-Role": "HR"},
    )
    assert create_res.status_code == 201
    contact_data = create_res.json()["data"]
    user_id = contact_data["id"]
    assert contact_data["username"] == username
    assert contact_data["system_role"] == "INTERVIEWER"

    # Immediately login via /auth/login using newly created credentials
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert login_res.status_code == 200
    token = login_res.json()["data"]["access_token"]
    assert login_res.json()["data"]["user"]["role"] == "INTERVIEWER"

    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["data"]["username"] == username

    # Soft-deactivate via DELETE /contacts/{user_id} -> revokes login
    del_res = await client.delete(
        f"/api/v1/contacts/{user_id}",
        headers={"X-Demo-Role": "HR"},
    )
    assert del_res.status_code == 200

    relogin_res = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert relogin_res.status_code == 401


# ------------------ Eval #3 & #4: Scoped Rubrics CRUD & Ownership Isolation ------------------ #
async def test_rubrics_scoped_ownership_and_crud(client: AsyncClient):
    suffix = uuid.uuid4().hex[:6].upper()
    intv_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "budi.santoso", "password": "password123"},
    )
    assert intv_login.status_code == 200
    intv_token = intv_login.json()["data"]["access_token"]
    intv_id = intv_login.json()["data"]["user"]["id"]
    intv_headers = {"Authorization": f"Bearer {intv_token}"}

    hr_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "hr.admin", "password": "password123"},
    )
    assert hr_login.status_code == 200
    hr_headers = {"Authorization": f"Bearer {hr_login.json()['data']['access_token']}"}

    # 1. Interviewer creates custom division rubric
    create_rubric = await client.post(
        "/api/v1/rubrics",
        json={
            "code": f"PROFILE-ENG-{suffix}",
            "round_name": f"System Design Round {suffix}",
            "description": "Custom distributed systems rubric",
            "department": "Engineering",
            "target_role": "INTERVIEWER",
        },
        headers=intv_headers,
    )
    assert create_rubric.status_code == 201
    profile_id = create_rubric.json()["data"]["id"]
    assert create_rubric.json()["data"]["owner_user_id"] == intv_id

    # 2. Add, edit, and delete competency indicator on owned rubric
    add_comp = await client.post(
        f"/api/v1/rubrics/{profile_id}/competencies",
        json={
            "code": f"SYS-{suffix}",
            "name": "High Availability Design",
            "description": "Evaluates fault tolerance and failover patterns",
            "weight": 40,
            "target_level": 4,
        },
        headers=intv_headers,
    )
    assert add_comp.status_code == 201
    comp_id = add_comp.json()["data"]["id"]

    patch_comp = await client.patch(
        f"/api/v1/rubrics/{profile_id}/competencies/{comp_id}",
        json={"weight": 50, "target_level": 5},
        headers=intv_headers,
    )
    assert patch_comp.status_code == 200
    assert patch_comp.json()["data"]["weight"] == 50

    # 3. HR's default rubric list does NOT mix Interviewer's custom rubric, and HR cannot mutate it
    hr_list = await client.get("/api/v1/rubrics", headers=hr_headers)
    assert hr_list.status_code == 200
    assert all(r["id"] != profile_id for r in hr_list.json()["data"])

    hr_for_budi = await client.get(
        f"/api/v1/rubrics?for_interviewer_id={intv_id}",
        headers=hr_headers,
    )
    assert hr_for_budi.status_code == 200
    assert any(r["id"] == profile_id for r in hr_for_budi.json()["data"])

    hr_forbidden_del = await client.delete(
        f"/api/v1/rubrics/{profile_id}",
        headers=hr_headers,
    )
    assert hr_forbidden_del.status_code == 403

    # 4. ADMIN sees all rubrics across all roles
    admin_list = await client.get("/api/v1/rubrics", headers={"X-Demo-Role": "ADMIN"})
    assert admin_list.status_code == 200
    assert any(r["id"] == profile_id for r in admin_list.json()["data"])

    # 5. Interviewer deletes competency & custom rubric cleanly
    del_comp = await client.delete(
        f"/api/v1/rubrics/{profile_id}/competencies/{comp_id}",
        headers=intv_headers,
    )
    assert del_comp.status_code == 200

    del_rubric = await client.delete(
        f"/api/v1/rubrics/{profile_id}",
        headers=intv_headers,
    )
    assert del_rubric.status_code == 200


# ------------------ Eval #6: Two-Tier Decision Handoff & Zero-Trust Anti-IDOR ------------------ #
async def test_two_tier_decision_handoff_and_anti_idor(client: AsyncClient):
    login_a = await client.post(
        "/api/v1/auth/login",
        json={"username": "budi.santoso", "password": "password123"},
    )
    login_b = await client.post(
        "/api/v1/auth/login",
        json={"username": "budi.hartono", "password": "password123"},
    )
    login_hr = await client.post(
        "/api/v1/auth/login",
        json={"username": "hr.admin", "password": "password123"},
    )
    assert login_a.status_code == 200, f"login_a failed: {login_a.text}"
    assert login_b.status_code == 200, f"login_b failed: {login_b.text}"
    assert login_hr.status_code == 200, f"login_hr failed: {login_hr.text}"
    headers_a = {"Authorization": f"Bearer {login_a.json()['data']['access_token']}"}
    headers_b = {"Authorization": f"Bearer {login_b.json()['data']['access_token']}"}
    headers_hr = {"Authorization": f"Bearer {login_hr.json()['data']['access_token']}"}

    # 1. Interviewer A uploads their technical interview session
    a_rubrics = await client.get("/api/v1/rubrics", headers=headers_a)
    profile_a_id = a_rubrics.json()["data"][0]["id"]

    upload_a = await client.post(
        "/api/v1/interviews/sessions/upload",
        json={
            "candidate_id": "1",
            "profile_id": profile_a_id,
            "consent_status": "GRANTED",
            "audio_url": "https://storage.smarthiring.ai/interviews/tech_idor_test.mp3",
            "audio_duration": "42:10",
            "notes": "Technical architecture deep dive",
        },
        headers=headers_a,
    )
    assert upload_a.status_code == 201
    session_a_id = upload_a.json()["data"]["id"]

    # 2. Anti-IDOR: Interviewer B CANNOT see, fetch, or decide Interviewer A's session!
    list_b = await client.get("/api/v1/interviews/sessions?scope=all", headers=headers_b)
    assert list_b.status_code == 200
    assert all(s["id"] != session_a_id for s in list_b.json()["data"]["items"])

    detail_b = await client.get(f"/api/v1/interviews/sessions/{session_a_id}", headers=headers_b)
    assert detail_b.status_code == 403

    decide_b = await client.post(
        f"/api/v1/interviews/decisions/{session_a_id}",
        json={"decision": "REJECT", "notes": "Malicious cross-interviewer decision attempt"},
        headers=headers_b,
    )
    assert decide_b.status_code == 403

    # 3. Guard 4: HR cannot decide Interviewer A's undecided session before Interviewer A submits
    premature_hr = await client.post(
        f"/api/v1/interviews/decisions/{session_a_id}",
        json={"decision": "ADVANCE", "next_stage": "OFFERED", "notes": "Premature HR decision"},
        headers=headers_hr,
    )
    assert premature_hr.status_code == 403

    # 4. Tier 1: Interviewer A submits recommendation -> locks to PENDING_HR_FOLLOWUP & PENDING_HR_REVIEW
    rec_a = await client.post(
        f"/api/v1/interviews/decisions/{session_a_id}",
        json={
            "decision": "ADVANCE",
            "next_stage": "OFFERED",
            "notes": "Strong system design and distributed architecture mastery.",
        },
        headers=headers_a,
    )
    assert rec_a.status_code == 200
    rec_data = rec_a.json()["data"]
    assert rec_data["actor_role"] == "INTERVIEWER"
    assert rec_data["workflow_status"] == "PENDING_HR_FOLLOWUP"
    assert rec_data["resulting_candidate_status"] == "PENDING_HR_REVIEW"

    # 5. Guard 3: Interviewer A is locked and CANNOT overwrite their submitted recommendation
    overwrite_a = await client.post(
        f"/api/v1/interviews/decisions/{session_a_id}",
        json={"decision": "REJECT", "notes": "Trying to change submitted recommendation"},
        headers=headers_a,
    )
    assert overwrite_a.status_code == 403

    # 6. Decided session CANNOT be deleted (409 Conflict)
    del_decided = await client.delete(
        f"/api/v1/interviews/sessions/{session_a_id}",
        headers=headers_a,
    )
    assert del_decided.status_code == 409

    # 7. Tier 2: HR sees session in awaiting_hr scope and finalizes -> FINALIZED & OFFERED
    awaiting_res = await client.get(
        "/api/v1/interviews/sessions?scope=awaiting_hr",
        headers=headers_hr,
    )
    assert awaiting_res.status_code == 200
    assert any(s["id"] == session_a_id for s in awaiting_res.json()["data"]["items"])

    final_hr = await client.post(
        f"/api/v1/interviews/decisions/{session_a_id}",
        json={
            "decision": "ADVANCE",
            "next_stage": "OFFERED",
            "notes": "Confirmed Budi Santoso's technical recommendation. Proceeding to offering.",
        },
        headers=headers_hr,
    )
    assert final_hr.status_code == 200
    final_data = final_hr.json()["data"]
    assert final_data["actor_role"] == "HR"
    assert final_data["workflow_status"] == "FINALIZED"
    assert final_data["resulting_candidate_status"] == "OFFERED"

    # 8. Guard 2: Finalized decision is permanently locked even for HR
    final_overwrite = await client.post(
        f"/api/v1/interviews/decisions/{session_a_id}",
        json={"decision": "HOLD", "notes": "Attempted post-finalization overwrite"},
        headers=headers_hr,
    )
    assert final_overwrite.status_code == 403


# ------------------ Eval #4: Guarded DELETE Endpoints ------------------ #
async def test_guarded_delete_endpoints(client: AsyncClient):
    # 1. Create and delete a holiday
    hol_res = await client.post(
        "/api/v1/holidays",
        json={"date": "2029-12-31", "name": "Temp Year End Holiday", "is_joint_leave": True},
        headers={"X-Demo-Role": "HR"},
    )
    if hol_res.status_code == 201:
        hol_id = hol_res.json()["data"]["id"]
        del_hol = await client.delete(f"/api/v1/holidays/{hol_id}", headers={"X-Demo-Role": "HR"})
        assert del_hol.status_code == 200

    # 2. Candidate "1" has linked interviews/threads -> guarded DELETE returns 409 Conflict
    del_linked_cand = await client.delete("/api/v1/candidates/1", headers={"X-Demo-Role": "HR"})
    assert del_linked_cand.status_code == 409

    # 3. Undecided interview session CAN be deleted cleanly
    temp_sess = await client.post(
        "/api/v1/interviews/sessions/upload",
        json={
            "candidate_id": "1",
            "profile_id": "1",
            "consent_status": "GRANTED",
            "audio_url": "https://storage.smarthiring.ai/interviews/temp_undecided.mp3",
            "audio_duration": "10:00",
            "notes": "Temporary undecided upload",
        },
        headers={"X-Demo-Role": "HR"},
    )
    assert temp_sess.status_code == 201
    temp_sess_id = temp_sess.json()["data"]["id"]

    del_sess = await client.delete(
        f"/api/v1/interviews/sessions/{temp_sess_id}",
        headers={"X-Demo-Role": "HR"},
    )
    assert del_sess.status_code == 200
