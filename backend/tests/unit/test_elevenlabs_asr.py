from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.InterviewModel import Interview, SourceFile
from app.model.JobModel import Job
from app.service.InterviewSessionService import InterviewSessionService
from app.service.SpeechToTextService import SpeechToTextService


@pytest.mark.asyncio
async def test_elevenlabs_word_clustering_and_diarization():
    service = SpeechToTextService()
    words = [
        {"text": "Selamat", "start": 0.1, "end": 0.5, "speaker_id": "speaker_0"},
        {"text": "pagi", "start": 0.6, "end": 0.9, "speaker_id": "speaker_0"},
        {"text": "Rina,", "start": 1.0, "end": 1.4, "speaker_id": "speaker_0"},
        {"text": "bisa", "start": 1.5, "end": 1.8, "speaker_id": "speaker_0"},
        {"text": "ceritakan", "start": 1.9, "end": 2.4, "speaker_id": "speaker_0"},
        {"text": "pengalamanmu?", "start": 2.5, "end": 3.2, "speaker_id": "speaker_0"},
        # Speaker changes to candidate
        {"text": "Tentu", "start": 4.0, "end": 4.4, "speaker_id": "speaker_1"},
        {"text": "Pak,", "start": 4.5, "end": 4.8, "speaker_id": "speaker_1"},
        {"text": "saya", "start": 5.0, "end": 5.3, "speaker_id": "speaker_1"},
        {"text": "berpengalaman", "start": 5.4, "end": 6.2, "speaker_id": "speaker_1"},
        {"text": "di", "start": 6.3, "end": 6.5, "speaker_id": "speaker_1"},
        {"text": "React", "start": 6.6, "end": 7.0, "speaker_id": "speaker_1"},
        {"text": "dan", "start": 7.1, "end": 7.3, "speaker_id": "speaker_1"},
        {"text": "Next.js.", "start": 7.4, "end": 8.1, "speaker_id": "speaker_1"},
    ]

    segments = service._cluster_elevenlabs_words(words, candidate_name="Rina Kusuma")
    assert len(segments) == 2

    # Segment 1: Interviewer
    assert segments[0]["segment_no"] == 1
    assert segments[0]["start_ms"] == 100
    assert segments[0]["end_ms"] == 3200
    assert segments[0]["speaker"] == "INTERVIEWER"
    assert segments[0]["speaker_label"] == "SPEAKER_0"
    assert "Selamat pagi Rina" in segments[0]["text"]

    # Segment 2: Candidate
    assert segments[1]["segment_no"] == 2
    assert segments[1]["start_ms"] == 4000
    assert segments[1]["end_ms"] == 8100
    assert segments[1]["speaker"] == "CANDIDATE"
    assert segments[1]["speaker_label"] == "SPEAKER_1"
    assert "Next.js" in segments[1]["text"]


@pytest.mark.asyncio
async def test_elevenlabs_transcription_with_metadata_mock():
    service = SpeechToTextService()
    service.elevenlabs_api_key = "test-elevenlabs-key"
    service.elevenlabs_model = "scribe_v1"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "text": "Selamat datang di sesi wawancara.",
        "words": [
            {"text": "Selamat", "start": 0.0, "end": 0.4, "speaker_id": "speaker_0"},
            {"text": "datang.", "start": 0.5, "end": 0.9, "speaker_id": "speaker_0"},
            {"text": "Terima", "start": 1.5, "end": 1.9, "speaker_id": "speaker_1"},
            {"text": "kasih.", "start": 2.0, "end": 2.4, "speaker_id": "speaker_1"},
        ],
    }

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        segments, engine, model = await service.transcribe_with_metadata(
            file_path_or_bytes=b"\xFF\xFB\x90\x44" + b"\x00" * 200,
            filename="interview.mp3",
        )

        assert engine == "ElevenLabs Scribe"
        assert model == "scribe_v1"
        assert len(segments) == 2
        assert segments[0]["speaker"] == "INTERVIEWER"
        assert segments[1]["speaker"] == "CANDIDATE"


@pytest.mark.asyncio
async def test_elevenlabs_fallback_on_api_error():
    service = SpeechToTextService()
    service.elevenlabs_api_key = "expired-key"
    service.groq_api_key = ""  # Force fallback to synthetic

    with patch("httpx.AsyncClient.post", side_effect=Exception("ElevenLabs API 401 Unauthorized")):
        segments, engine, model = await service.transcribe_with_metadata(
            file_path_or_bytes=b"\xFF\xFB\x90\x44" + b"\x00" * 200,
            filename="interview.mp3",
        )

        assert engine == "Synthetic Fallback ASR"
        assert model == "mock-v1"
        assert len(segments) > 0


@pytest.mark.asyncio
async def test_progress_percentage_mapping(test_session: AsyncSession):
    service = InterviewSessionService(test_session)

    # 1. Test REJECTED_NO_CONSENT
    intv_rejected = Interview(
        nid=998,
        nid_candidate=1,
        nid_profile=1,
        vconsent_status="NOT_GRANTED",
    )
    dto_rejected = service._to_session_dto(intv_rejected)
    assert dto_rejected.job_status == "REJECTED_NO_CONSENT"
    assert dto_rejected.progress_percentage == 0

    # 2. Test in-progress job (nstatus=3 TRANSCRIBED)
    intv_progress = Interview(
        nid=999,
        nid_candidate=1,
        nid_profile=1,
        vconsent_status="GRANTED",
    )
    sf = SourceFile(
        nid=999,
        nid_interview=999,
        vtype="AUDIO",
        vurl="https://storage/test.mp3",
        vduration="45:20",
    )
    job = Job(
        nid=999,
        nid_source=999,
        nstatus=3,
        vasr_engine="ElevenLabs Scribe",
        vasr_model_version="scribe_v1",
    )
    sf.jobs = [job]
    intv_progress.source_files = [sf]

    dto_progress = service._to_session_dto(intv_progress)
    assert dto_progress.job_status == "TRANSCRIBED"
    assert dto_progress.progress_percentage == 60
    assert dto_progress.asr_engine == "ElevenLabs Scribe"
    assert "ElevenLabs Scribe" in dto_progress.current_step


@pytest.mark.asyncio
async def test_async_upload_controller_endpoint(client: AsyncClient):
    mp3_header = b"\xFF\xFB\x90\x44" + b"\x00" * 500
    files = {"file": ("interview_recording.mp3", BytesIO(mp3_header), "audio/mpeg")}
    data = {
        "candidate_id": "1",
        "profile_id": "1",
        "consent_status": "GRANTED",
        "notes": "ElevenLabs Async Test",
    }

    resp = await client.post("/api/v1/interviews/sessions/upload-file", files=files, data=data)
    assert resp.status_code == 201

    payload = resp.json()
    assert payload["success"] is True
    assert payload["data"]["progress_percentage"] >= 15
    assert payload["data"]["consent_status"] == "GRANTED"

    interview_id = payload["data"]["id"]
    status_resp = await client.get(f"/api/v1/interviews/sessions/{interview_id}/status")
    assert status_resp.status_code == 200
    status_payload = status_resp.json()
    assert status_payload["success"] is True
    assert "progress_percentage" in status_payload["data"]
