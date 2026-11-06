import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.CandidateModel import Candidate
from app.service.InterviewSessionService import InterviewSessionService
from app.service.RubricService import RubricService


@pytest.mark.asyncio
async def test_auto_generate_candidate_rubric_from_transcript(test_session: AsyncSession):
    suffix = uuid.uuid4().hex[:6]
    # 1. Create unique test candidate
    cand = Candidate(
        vcandidate_code=f"CAND-RUBRIC-{suffix.upper()}",
        vname=f"Budi Pratama {suffix}",
        vemail=f"budi.{suffix}@example.com",
        vphone_number="+6281234567890",
        vpreferred_channel="whatsapp",
        vjob_position="Senior Backend Engineer",
        vstatus="INTERVIEW_SCHEDULED",
        vtimezone="WIB",
    )
    test_session.add(cand)
    await test_session.commit()
    await test_session.refresh(cand)

    # 2. Upload interview audio WITHOUT specifying profile_id
    service = InterviewSessionService(test_session)
    mp3_content = b"\xFF\xFB\x90\x44\x00" + b"\x00" * 300

    session_dto = await service.upload_interview_file(
        filename="budi_interview.mp3",
        content=mp3_content,
        candidate_id=str(cand.nid),
        profile_id=None,  # No profile selected! Auto-generate candidate rubric!
        consent_status="GRANTED",
        notes="Fokus arsitektur distributed systems dan microservices.",
    )

    assert session_dto.id is not None
    assert session_dto.candidate_id == str(cand.nid)
    assert session_dto.profile_id is not None
    assert session_dto.job_status == "COMPLETED"
    assert len(session_dto.competency_points) > 0

    # 3. Verify RubricProfile was created and tied to this candidate
    rubric_service = RubricService(test_session)
    profiles = await rubric_service.list_rubric_profiles(candidate_id=str(cand.nid))
    assert len(profiles) > 0
    candidate_profile = profiles[0]
    assert candidate_profile.candidate_id == str(cand.nid)
    assert candidate_profile.candidate_name == f"Budi Pratama {suffix}"
    # Auto-generated 4 competencies from transcript in Indonesian
    assert len(candidate_profile.competencies) >= 4
    comp_codes = [c.code for c in candidate_profile.competencies]
    assert "C1" in comp_codes

    # Done


@pytest.mark.asyncio
async def test_re_evaluate_rubric_from_transcript_api(client: AsyncClient):
    suffix = uuid.uuid4().hex[:6]
    # 1. Create test candidate via API
    cand_res = await client.post(
        "/api/v1/candidates",
        json={
            "name": f"Siti Rahayu {suffix}",
            "email": f"siti.{suffix}@example.com",
            "phone": "+6281234567891",
            "preferred_channel": "whatsapp",
            "applied_position": "Lead QA Automation",
            "timezone": "WIB",
        },
        headers={"X-Demo-Role": "HR"},
    )
    assert cand_res.status_code == 201
    cand_id = cand_res.json()["data"]["id"]

    # 2. Upload session via API without profile_id
    upload_res = await client.post(
        "/api/v1/interviews/sessions/upload",
        json={
            "candidate_id": cand_id,
            "profile_id": None,
            "consent_status": "GRANTED",
            "audio_url": "https://storage.smarthiring.ai/interviews/siti_interview.mp3",
            "audio_duration": "30:00",
            "notes": "Pengujian automated end-to-end framework.",
        },
        headers={"X-Demo-Role": "HR"},
    )
    assert upload_res.status_code == 201
    created_session = upload_res.json()["data"]
    profile_id = created_session["profile_id"]
    assert profile_id is not None

    # 3. Trigger re-evaluation endpoint
    re_eval_res = await client.post(
        f"/api/v1/rubrics/{profile_id}/re-evaluate",
        headers={"X-Demo-Role": "HR"},
    )
    assert re_eval_res.status_code == 200
    re_eval_data = re_eval_res.json()["data"]
    assert re_eval_data["id"] == str(profile_id)
    assert len(re_eval_data["competencies"]) >= 4

    # Done
