from app.dto.BaseDTO import ApiResponse, PaginatedResponse
from app.dto.CandidateDTO import CandidateDTO
from app.dto.ContactDTO import InterviewerContactDTO


def test_candidate_dto_serialization():
    cand = CandidateDTO(
        id="1",
        candidate_code="CAND-2026-001",
        name="Rina Kusuma",
        email="rina.kusuma@example.com",
        phone="+6281234567890",
        preferred_channel="whatsapp",
        applied_position="Senior Frontend Engineer",
        status="ESCALATED",
        timezone="WIB",
        created_at="2026-10-24T10:00:00Z",
    )
    data = cand.model_dump()
    assert data["candidate_code"] == "CAND-2026-001"
    assert data["preferred_channel"] == "whatsapp"
    assert data["timezone"] == "WIB"


def test_interviewer_contact_dto_serialization():
    interviewer = InterviewerContactDTO(
        id="1",
        employee_id="EMP-ENG-001",
        name="Budi Santoso",
        username="budi.santoso",
        email="budi.santoso@company.com",
        phone="+6281211112222",
        department="Engineering",
        role="VP of Engineering",
        timezone="WIB",
        working_hours="09:00 - 17:00",
        avatar_initials="BS",
    )
    assert interviewer.avatar_initials == "BS"
    assert interviewer.department == "Engineering"


def test_api_response_envelope():
    resp = ApiResponse[str](success=True, message="Success", data="test_payload")
    dump = resp.model_dump()
    assert dump["success"] is True
    assert dump["data"] == "test_payload"


def test_paginated_response():
    resp = PaginatedResponse[int](items=[1, 2, 3], total=10, page=1, page_size=3)
    assert len(resp.items) == 3
    assert resp.total == 10
