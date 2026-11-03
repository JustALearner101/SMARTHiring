import asyncio
import random
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.DatabaseSession import AsyncSessionLocal
from app.dto.ActionPlanDTO import PlanApprovalRequestDTO, PlanRejectRequestDTO
from app.exception.CustomException import (
    ConflictException,
    PayloadTooLargeException,
    UnsupportedMediaTypeException,
)
from app.middleware.RateLimiterMiddleware import (
    SlidingWindowRateLimiter,
    rate_limiter_instance,
)
from app.repository.ActionPlanRepository import ActionPlanRepository
from app.repository.CalendarMatrixRepository import CalendarMatrixRepository
from app.service.ActionPlanService import ActionPlanService
from app.util.FileValidator import (
    detect_audio_video_mime,
    validate_audio_video_upload,
)

# =====================================================================
# 1. In-Memory Sliding Window Rate Limiter Tests
# =====================================================================

def test_sliding_window_rate_limiter_core():
    limiter = SlidingWindowRateLimiter()
    key = "test-client-1"

    # Limit = 3 requests per 10 seconds
    allowed, remaining, _ = limiter.is_allowed(key, limit=3, window_seconds=10)
    assert allowed is True
    assert remaining == 2

    allowed, remaining, _ = limiter.is_allowed(key, limit=3, window_seconds=10)
    assert allowed is True
    assert remaining == 1

    allowed, remaining, _ = limiter.is_allowed(key, limit=3, window_seconds=10)
    assert allowed is True
    assert remaining == 0

    # 4th request must be blocked
    allowed, remaining, retry_after = limiter.is_allowed(key, limit=3, window_seconds=10)
    assert allowed is False
    assert remaining == 0
    assert retry_after > 0

    # Test reset
    limiter.reset()
    allowed, remaining, _ = limiter.is_allowed(key, limit=3, window_seconds=10)
    assert allowed is True
    assert remaining == 2


async def test_rate_limiter_http_middleware_blocks(client: AsyncClient):
    rate_limiter_instance.reset()

    # /api/v1/auth tier has limit = 5 per 60s
    for i in range(5):
        res = await client.get("/api/v1/auth/users")
        assert res.status_code == 200
        assert "X-RateLimit-Limit" in res.headers
        assert res.headers["X-RateLimit-Remaining"] == str(4 - i)

    # 6th request must trigger HTTP 429
    blocked_res = await client.get("/api/v1/auth/users")
    assert blocked_res.status_code == 429
    body = blocked_res.json()
    assert body["success"] is False
    assert "Rate limit exceeded" in body["message"]
    assert "Retry-After" in blocked_res.headers
    assert blocked_res.headers["X-RateLimit-Remaining"] == "0"

    # Bypass header works
    bypass_res = await client.get("/api/v1/auth/users", headers={"X-Bypass-Rate-Limit": "1"})
    assert bypass_res.status_code == 200

    rate_limiter_instance.reset()


# =====================================================================
# 2. Race Condition & Concurrency Locking Tests
# =====================================================================

async def test_concurrent_plan_approvals():
    """Verifies atomic conditional UPDATE prevents double-approval race conditions."""
    now = datetime.now(UTC)

    # Setup test plan with its own initial session
    async with AsyncSessionLocal() as init_session:
        plan_repo = ActionPlanRepository(init_session)
        plan = await plan_repo.create_action_plan({
            "vplan": "Concurrent Approval Test Plan",
            "vaction_type": "CALENDAR",
            "dscheduled_start_utc": now,
            "dscheduled_end_utc": now + timedelta(hours=1),
            "vapproval_status": "AWAITING_APPROVAL",
            "vimpact_level": "NORMAL",
            "vagent_metadata": {
                "candidate_id": "1",
                "interviewer_id": "1",
                "items": [],
            },
        })
        plan_id = str(plan.nid)

    approval_dto = PlanApprovalRequestDTO(
        approved_by="HR Lead (Race Tester)",
        send_immediately=False,
    )

    # Launch 5 concurrent approval attempts, each using its own isolated DB session
    async def try_approve():
        async with AsyncSessionLocal() as session:
            service = ActionPlanService(session)
            try:
                return await service.approve_plan(plan_id, approval_dto)
            except ConflictException as e:
                return e

    results = await asyncio.gather(*[try_approve() for _ in range(5)])

    # Exactly 1 request must succeed (return ActionPlanDTO), 4 must raise ConflictException
    successes = [r for r in results if not isinstance(r, Exception)]
    conflicts = [r for r in results if isinstance(r, ConflictException)]

    assert len(successes) == 1
    assert len(conflicts) == 4
    assert successes[0].status == "UNDO_WINDOW"


async def test_calendar_atomic_double_booking_prevention(test_session: AsyncSession):
    """Verifies SELECT ... FOR UPDATE interval check blocks overlapping calendar slots."""
    cal_repo = CalendarMatrixRepository(test_session)
    now = datetime.now(UTC)
    # Pick a random unique future day to avoid collisions with prior test runs
    offset_days = 200 + random.randint(1, 10000)
    start1 = now + timedelta(days=offset_days, hours=10)
    end1 = start1 + timedelta(hours=1)

    # 1. Book first slot successfully
    event1 = await cal_repo.book_slot_atomic(
        user_id=1,
        title="First Reserved Interview",
        start_utc=start1,
        end_utc=end1,
        candidate_name="Kandidat A",
    )
    assert event1.nid is not None

    # 2. Attempt to book overlapping slot (starts 30 mins before end1)
    start2 = start1 + timedelta(minutes=30)
    end2 = start2 + timedelta(hours=1)

    with pytest.raises(ConflictException) as exc_info:
        await cal_repo.book_slot_atomic(
            user_id=1,
            title="Overlapping Double Booking Attempt",
            start_utc=start2,
            end_utc=end2,
            candidate_name="Kandidat B",
        )

    assert "conflicts with another scheduled event" in str(exc_info.value.message)


# =====================================================================
# 3. File Upload & Binary Magic Byte Validation Tests
# =====================================================================

def test_file_validator_magic_bytes_detection():
    # MP3 ID3 header
    mp3_data = b"ID3" + b"\x00" * 50
    assert detect_audio_video_mime(mp3_data) == "audio/mpeg"
    assert validate_audio_video_upload("rec.mp3", mp3_data) == "audio/mpeg"

    # WAV RIFF header
    wav_data = b"RIFF\x24\x00\x00\x00WAVEfmt " + b"\x00" * 30
    assert detect_audio_video_mime(wav_data) == "audio/wav"
    assert validate_audio_video_upload("interview.wav", wav_data) == "audio/wav"

    # OGG header
    ogg_data = b"OggS\x00\x02" + b"\x00" * 40
    assert detect_audio_video_mime(ogg_data) == "audio/ogg"

    # M4A / MP4 container
    m4a_data = b"\x00\x00\x00\x18ftypM4A " + b"\x00" * 30
    assert detect_audio_video_mime(m4a_data) == "audio/mp4"

    mp4_data = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 30
    assert detect_audio_video_mime(mp4_data) == "video/mp4"

    # WebM header
    webm_data = b"\x1a\x45\xdf\xa3" + b"\x00" * 40
    assert detect_audio_video_mime(webm_data) == "video/webm"


def test_file_validator_rejects_unsupported_or_spoofed_file():
    # Executable disguised as mp3
    fake_mp3 = b"MZ\x90\x00\x03\x00\x00\x00" + b"\x00" * 30
    with pytest.raises(UnsupportedMediaTypeException) as exc_info:
        validate_audio_video_upload("malware.mp3", fake_mp3)
    assert "is not a valid audio/video recording format" in exc_info.value.message


def test_file_validator_rejects_oversized_payload():
    tiny_header = b"ID3" + b"\x00" * 20
    # Test with custom small max_size
    with pytest.raises(PayloadTooLargeException) as exc_info:
        validate_audio_video_upload("big.mp3", tiny_header, max_size=10)
    assert "exceeds maximum limit" in exc_info.value.message


async def test_upload_file_endpoint_rejects_invalid_file(client: AsyncClient):
    fake_file_content = b"This is plain text pretending to be audio."
    files = {"file": ("recording.mp3", fake_file_content, "audio/mpeg")}
    data = {"candidate_id": "1", "profile_id": "1"}

    res = await client.post(
        "/api/v1/interviews/sessions/upload-file",
        files=files,
        data=data,
        headers={"X-Bypass-Rate-Limit": "1"},
    )
    assert res.status_code == 415
    assert res.json()["success"] is False
    assert "is not a valid audio/video recording format" in res.json()["message"]


async def test_upload_file_endpoint_accepts_valid_audio(client: AsyncClient):
    valid_wav_content = b"RIFF\x24\x00\x00\x00WAVEfmt " + b"\x00" * 100
    files = {"file": ("real_interview.wav", valid_wav_content, "audio/wav")}
    data = {"candidate_id": "1", "profile_id": "1"}

    res = await client.post(
        "/api/v1/interviews/sessions/upload-file",
        files=files,
        data=data,
        headers={"X-Bypass-Rate-Limit": "1"},
    )
    assert res.status_code == 201
    assert res.json()["success"] is True
    assert res.json()["data"]["id"] is not None


# =====================================================================
# 5. Action Plan Reject & Pre-Execution Secondary Validator Tests
# =====================================================================

async def test_action_plan_reject_gate():
    """Verifies atomic rejection updates status to REJECTED and prevents double-rejection/approval."""
    now = datetime.now(UTC)
    async with AsyncSessionLocal() as session:
        plan_repo = ActionPlanRepository(session)
        plan = await plan_repo.create_action_plan({
            "vplan": "Test Rejection Plan",
            "vaction_type": "CALENDAR",
            "dscheduled_start_utc": now,
            "dscheduled_end_utc": now + timedelta(hours=1),
            "vapproval_status": "AWAITING_APPROVAL",
            "vimpact_level": "NORMAL",
            "vagent_metadata": {"candidate_id": "1", "interviewer_id": "1"},
        })
        plan_id = str(plan.nid)

    async with AsyncSessionLocal() as session:
        service = ActionPlanService(session)
        reject_req = PlanRejectRequestDTO(rejected_by="HR Lead", reason="Not a good fit for interviewer")
        rejected_dto = await service.reject_plan(plan_id, reject_req)
        assert rejected_dto.status == "REJECTED"

        # Subsequent attempt to reject must raise ConflictException
        with pytest.raises(ConflictException):
            await service.reject_plan(plan_id, reject_req)


async def test_secondary_validator_blocks_friday_prayer_at_approval():
    """Verifies that Secondary Validator blocks approval if slot is on Friday 11:30 - 13:00 WIB (TC-CHB-21)."""
    # 2026-10-30 is a Friday. 04:45 UTC = 11:45 WIB (inside blackout)
    friday_blackout_utc = datetime(2026, 10, 30, 4, 45, tzinfo=UTC)
    async with AsyncSessionLocal() as session:
        plan_repo = ActionPlanRepository(session)
        plan = await plan_repo.create_action_plan({
            "vplan": "Test Friday Blackout Slot",
            "vaction_type": "CALENDAR",
            "dscheduled_start_utc": friday_blackout_utc,
            "dscheduled_end_utc": friday_blackout_utc + timedelta(hours=1),
            "vapproval_status": "AWAITING_APPROVAL",
            "vimpact_level": "NORMAL",
            "vagent_metadata": {
                "candidate_id": "1",
                "interviewer_id": "1",
                "proposed_slot": {
                    "start_utc": friday_blackout_utc.isoformat(),
                    "duration_minutes": 60,
                },
            },
        })
        plan_id = str(plan.nid)

    async with AsyncSessionLocal() as session:
        service = ActionPlanService(session)
        approval_req = PlanApprovalRequestDTO(approved_by="HR Admin", send_immediately=True)
        with pytest.raises(ConflictException) as exc_info:
            await service.approve_plan(plan_id, approval_req)
        assert "sholat Jumat" in str(exc_info.value) or "rule-jumatan" in str(exc_info.value)

