import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


# ------------------ Authentication Endpoints ------------------ #
async def test_auth_login_success(client: AsyncClient):
    # 1. Login as HR Lead
    res = await client.post(
        "/api/v1/auth/login",
        json={"username": "hr.admin", "password": "password123"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert "access_token" in body["data"]
    assert body["data"]["user"]["role"] == "HR"
    assert body["data"]["user"]["username"] == "hr.admin"

    token = body["data"]["access_token"]

    # 2. Check /auth/me with Bearer token
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["data"]["role"] == "HR"


async def test_auth_login_invalid_password(client: AsyncClient):
    res = await client.post(
        "/api/v1/auth/login",
        json={"username": "hr.admin", "password": "wrongpassword"},
    )
    assert res.status_code == 401
    assert res.json()["success"] is False


async def test_auth_list_demo_users(client: AsyncClient):
    res = await client.get("/api/v1/auth/users")
    assert res.status_code == 200
    users = res.json()["data"]
    roles = [u["role"] for u in users]
    assert "HR" in roles
    assert "INTERVIEWER" in roles
    assert "ADMIN" in roles


# ------------------ Salary Masking (Permissions Pillar) ------------------ #
async def test_salary_masking_for_interviewer_vs_hr(client: AsyncClient):
    # 1. Access candidates as HR -> Salary MUST be exposed
    hr_res = await client.get(
        "/api/v1/candidates?query=CAND-2026-001",
        headers={"X-Demo-Role": "HR"},
    )
    assert hr_res.status_code == 200
    hr_items = hr_res.json()["data"]["items"]
    rina_hr = next((c for c in hr_items if c["candidate_code"] == "CAND-2026-001"), None)
    assert rina_hr is not None
    assert rina_hr["current_salary"] == 22_000_000
    assert rina_hr["expected_salary"] == 28_000_000

    # 2. Access candidates as ADMIN -> Salary MUST be exposed
    admin_res = await client.get(
        "/api/v1/candidates?query=CAND-2026-001",
        headers={"X-Demo-Role": "ADMIN"},
    )
    assert admin_res.status_code == 200
    admin_items = admin_res.json()["data"]["items"]
    rina_admin = next((c for c in admin_items if c["candidate_code"] == "CAND-2026-001"), None)
    assert rina_admin is not None
    assert rina_admin["current_salary"] == 22_000_000

    # 3. Access candidates as Interviewer -> Salary MUST be masked (None)
    interviewer_res = await client.get(
        "/api/v1/candidates?query=CAND-2026-001",
        headers={"X-Demo-Role": "INTERVIEWER"},
    )
    assert interviewer_res.status_code == 200
    interviewer_items = interviewer_res.json()["data"]["items"]
    rina_intv = next((c for c in interviewer_items if c["candidate_code"] == "CAND-2026-001"), None)
    assert rina_intv is not None
    assert rina_intv["current_salary"] is None
    assert rina_intv["expected_salary"] is None


# ------------------ Approval Gate Enforcement & 3-Role RBAC ------------------ #
async def test_action_plan_approval_gate_rbac(client: AsyncClient):
    # Trigger plan creation with explicit candidate and interviewer
    await client.post(
        "/api/v1/orchestrator/command",
        json={"command": "Jadwalkan technical interview untuk Rina Kusuma dengan Budi Santoso hari Kamis"},
    )
    curr_res = await client.get("/api/v1/actionPlans/current")
    assert curr_res.status_code == 200
    plan_id = curr_res.json()["data"]["id"]

    # 1. Interviewer attempts approval -> 403 Forbidden
    forbidden_res = await client.post(
        f"/api/v1/actionPlans/{plan_id}/approve",
        json={"approved_by": "Budi Santoso"},
        headers={"X-Demo-Role": "INTERVIEWER"},
    )
    assert forbidden_res.status_code == 403
    assert forbidden_res.json()["success"] is False

    # 2. HR approves -> 200 Success
    hr_res = await client.post(
        f"/api/v1/actionPlans/{plan_id}/approve",
        json={"approved_by": "Siti Rahma"},
        headers={"X-Demo-Role": "HR"},
    )
    assert hr_res.status_code == 200
    assert hr_res.json()["data"]["status"] == "UNDO_WINDOW"


async def test_rbac_master_write_and_audit_log_guards(client: AsyncClient):
    # Interviewer blocked from writing Master Candidates, Contacts, Holidays, and reading Audit Logs
    cand_block = await client.post(
        "/api/v1/candidates",
        json={
            "name": "Unauthorized Cand",
            "email": "unauth.cand@example.com",
            "phone": "+62811111111",
            "preferred_channel": "email",
            "applied_position": "Backend Engineer",
            "timezone": "WIB",
        },
        headers={"X-Demo-Role": "INTERVIEWER"},
    )
    assert cand_block.status_code == 403

    audit_block = await client.get(
        "/api/v1/auditLogs",
        headers={"X-Demo-Role": "INTERVIEWER"},
    )
    assert audit_block.status_code == 403

    # ADMIN has full access to Audit Logs
    audit_admin = await client.get(
        "/api/v1/auditLogs",
        headers={"X-Demo-Role": "ADMIN"},
    )
    assert audit_admin.status_code == 200
