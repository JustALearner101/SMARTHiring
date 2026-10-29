from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.JobModel import Job, TranscriptSegment
from app.model.SummaryModel import SummaryEvidence, SummaryPoint
from app.service.InterviewSessionService import InterviewSessionService
from app.service.SpeechToTextService import SpeechToTextService


@pytest.mark.asyncio
async def test_speech_to_text_speaker_assignment():
    service = SpeechToTextService()
    raw_segments = [
        {"segment_no": 1, "text": "Selamat datang di sesi wawancara, apakah Anda siap?", "start_ms": 0, "end_ms": 5000},
        {"segment_no": 2, "text": "Siap pak, saya sangat antusias mengikuti proses ini.", "start_ms": 6000, "end_ms": 12000},
        {"segment_no": 3, "text": "Bagaimana pengalaman Anda menggunakan arsitektur microservices?", "start_ms": 13000, "end_ms": 18000},
        {"segment_no": 4, "text": "Kami mendesain service independen menggunakan Docker dan Kubernetes.", "start_ms": 19000, "end_ms": 30000},
    ]

    assigned = service._assign_speakers(raw_segments, candidate_name="Rina Kusuma")
    assert assigned[0]["speaker"] == "INTERVIEWER"
    assert assigned[1]["speaker"] == "CANDIDATE"
    assert assigned[2]["speaker"] == "INTERVIEWER"
    assert assigned[3]["speaker"] == "CANDIDATE"


@pytest.mark.asyncio
async def test_speech_to_text_groq_mock_transcription():
    service = SpeechToTextService()
    service.groq_api_key = "mock-groq-key"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "segments": [
            {"id": 0, "start": 1.5, "end": 6.2, "text": "Bisa jelaskan proyek terakhir Anda?", "avg_logprob": -0.05},
            {"id": 1, "start": 7.0, "end": 15.5, "text": "Saya memimpin migrasi frontend ke Next.js 16.", "avg_logprob": -0.02},
        ]
    }

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        segments = await service.transcribe_audio(
            file_path_or_bytes=b"\xFF\xFB\x90\x44" + b"\x00" * 200,  # Valid MP3 binary
            filename="interview.mp3",
        )

        assert len(segments) == 2
        assert segments[0]["start_ms"] == 1500
        assert segments[0]["end_ms"] == 6200
        assert segments[0]["speaker"] == "INTERVIEWER"
        assert segments[1]["start_ms"] == 7000
        assert segments[1]["end_ms"] == 15500
        assert segments[1]["speaker"] == "CANDIDATE"
        assert segments[1]["confidence"] >= 0.8


@pytest.mark.asyncio
async def test_interview_file_upload_and_evidence_pipeline(test_session: AsyncSession):
    service = InterviewSessionService(test_session)

    # Valid MP3 header (0xFF, 0xFB) + padding
    mp3_content = b"\xFF\xFB\x90\x44\x00" + b"\x00" * 300

    session_dto = await service.upload_interview_file(
        filename="technical_interview.mp3",
        content=mp3_content,
        candidate_id="1",
        profile_id="1",
        consent_status="GRANTED",
        notes="Kandidat menguasai Next.js dan Tailwind v4.",
    )

    assert session_dto.id is not None
    assert session_dto.candidate_name == "Rina Kusuma"
    assert session_dto.job_status == "COMPLETED"
    assert len(session_dto.competency_points) > 0

    # Verify real TranscriptSegment created in DB
    seg_stmt = (
        select(TranscriptSegment)
        .join(Job, Job.nid == TranscriptSegment.nid_job)
        .where(TranscriptSegment.nid_job != None)
        .order_by(TranscriptSegment.nid.desc())
    )
    segments = (await test_session.execute(seg_stmt)).scalars().all()
    assert len(segments) > 0
    seg_ids = {s.nid for s in segments}

    # Verify SummaryEvidence points to a real transcript segment
    ev_stmt = (
        select(SummaryEvidence)
        .join(SummaryPoint, SummaryPoint.nid == SummaryEvidence.nid_summary_point)
        .order_by(SummaryEvidence.nid.desc())
    )
    evidences = (await test_session.execute(ev_stmt)).scalars().all()
    assert len(evidences) > 0
    for ev in evidences:
        assert ev.nid_transcript in seg_ids
        assert ev.vquote is not None
        assert len(ev.vquote) > 0


@pytest.mark.asyncio
async def test_hr_decision_recording_api(client: AsyncClient):
    # 1. Fetch available session
    list_res = await client.get("/api/v1/interviews/sessions")
    assert list_res.status_code == 200
    items = list_res.json()["data"]["items"]
    assert len(items) > 0
    interview_id = items[0]["id"]

    # 2. Record HR decision
    dec_res = await client.post(
        f"/api/v1/interviews/decisions/{interview_id}",
        json={
            "decision": "ADVANCE",
            "notes": "Rekomendasi kuat ADVANCE: Keterampilan teknis dan bukti wawancara sangat solid.",
            "decided_by": "VP of Engineering Budi Santoso",
        },
        headers={"X-Bypass-Rate-Limit": "1"},
    )
    assert dec_res.status_code == 200
    data = dec_res.json()["data"]
    assert data["decision"] == "ADVANCE"
    assert "ADVANCE" in data["notes"]
