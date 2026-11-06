import uuid
from collections.abc import AsyncGenerator, Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.AppConfig import settings
from app.middleware.RateLimiterMiddleware import rate_limiter_instance
from app.model.AuditModel import AuditLog
from app.model.CandidateModel import Candidate
from app.model.InterviewModel import Interview, SourceFile
from app.model.JobModel import Job, TranscriptSegment
from app.model.RubricModel import Profile
from app.model.SummaryModel import HrDecision
from app.model.UserModel import User
from app.service.InterviewSessionService import InterviewSessionService

API = "/api/v1"
SESSIONS = f"{API}/interviews/sessions"
TRANSCRIPTS = f"{API}/interviews/transcripts"
DECISIONS = f"{API}/interviews/decisions"
PASSWORD = "password123"

MP3 = b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\x00" * 64
WAV = b"RIFF\x24\x00\x00\x00WAVEfmt " + b"\x00" * 32
M4A = b"\x00\x00\x00\x20ftypM4A " + b"\x00" * 32
PDF = b"%PDF-1.4\n" + b"\x00" * 64


@pytest.fixture(autouse=True)
def _safe_environment(monkeypatch):
    monkeypatch.setattr(settings, "SMTP_ENABLED", False)

    async def _no_processing(*_a, **_k):  # keep the ASR/LLM pipeline out of API-level tests
        return None

    monkeypatch.setattr(InterviewSessionService, "process_interview_job_async", staticmethod(_no_processing))
    rate_limiter_instance.reset()
    yield
    rate_limiter_instance.reset()


@pytest.fixture
async def track(test_session: AsyncSession) -> AsyncGenerator[list[int], None]:
    """Interview ids created by a test; removed (with children) and candidate statuses restored afterwards."""
    originals = {c.nid: c.vstatus for c in (await test_session.execute(select(Candidate))).scalars().all()}
    ids: list[int] = []
    yield ids
    test_session.expire_all()
    if ids:
        sf_ids = (await test_session.execute(select(SourceFile.nid).where(SourceFile.nid_interview.in_(ids)))).scalars().all()
        job_ids = (await test_session.execute(select(Job.nid).where(Job.nid_source.in_(sf_ids)))).scalars().all() if sf_ids else []
        if job_ids:
            await test_session.execute(update(AuditLog).where(AuditLog.nid_job.in_(job_ids)).values(nid_job=None))
            await test_session.execute(delete(HrDecision).where(HrDecision.nid_job.in_(job_ids)))
            await test_session.execute(delete(TranscriptSegment).where(TranscriptSegment.nid_job.in_(job_ids)))
            await test_session.execute(delete(Job).where(Job.nid.in_(job_ids)))
        if sf_ids:
            await test_session.execute(delete(SourceFile).where(SourceFile.nid.in_(sf_ids)))
        await test_session.execute(delete(Interview).where(Interview.nid.in_(ids)))
    for nid, status in originals.items():
        await test_session.execute(update(Candidate).where(Candidate.nid == nid).values(vstatus=status))
    await test_session.commit()
    for f in Path("storage/recordings").glob("*qa_*"):
        f.unlink(missing_ok=True)


async def _user(session: AsyncSession, username: str) -> User:
    return (await session.execute(select(User).where(User.vusername == username))).scalars().one()


async def _headers(client: AsyncClient, username: str) -> dict:
    res = await client.post(f"{API}/auth/login", json={"username": username, "password": PASSWORD})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['data']['access_token']}"}


@pytest.fixture
async def hr(client: AsyncClient) -> dict:
    return await _headers(client, "hr.admin")


@pytest.fixture
async def santoso(client: AsyncClient) -> dict:
    return await _headers(client, "budi.santoso")


@pytest.fixture
def make_interview(test_session: AsyncSession, track: list[int]) -> Callable:
    async def _make(owner: str | None, *, consent: str = "GRANTED", job_status: int = 10, segments: bool = True) -> int:
        cand = (await test_session.execute(select(Candidate).where(Candidate.vname == "Rina Kusuma"))).scalars().one()
        prof = (await test_session.execute(select(Profile).limit(1))).scalars().one()
        owner_id = (await _user(test_session, owner)).nid if owner else None
        iv = Interview(
            nid_candidate=cand.nid, nid_profile=prof.nid, nid_interviewer=owner_id,
            vconsent_status=consent, dconsent_at=datetime.now(UTC), vconsent_notice_version="v2.1",
        )
        test_session.add(iv)
        await test_session.flush()
        sf = SourceFile(nid_interview=iv.nid, vtype="AUDIO", vurl="https://example.test/qa.mp3", vduration="10:00")
        test_session.add(sf)
        await test_session.flush()
        job = Job(nid_source=sf.nid, nstatus=job_status, vasr_engine="QA")
        test_session.add(job)
        await test_session.flush()
        if segments:
            for no, (spk, text) in enumerate([("INTERVIEWER", "Ceritakan pengalaman Anda."), ("CANDIDATE", "Saya 5 tahun di backend.")], 1):
                test_session.add(TranscriptSegment(
                    nid_job=job.nid, nsegment_no=no, nstart_ms=no * 1000, nend_ms=no * 1000 + 800,
                    vspeaker_label=spk, vspeaker_type=spk, vtext=text, fconfidence=0.95, nis_uncertain=0,
                ))
        await test_session.commit()
        track.append(iv.nid)
        return iv.nid

    return _make


async def _upload(client, headers, name, content, track, **form):
    res = await client.post(
        f"{SESSIONS}/upload-file", headers=headers,
        files={"file": (name, content, "application/octet-stream")},
        data={"candidate_id": "1", "profile_id": "1", **form},
    )
    if res.status_code == 201:
        track.append(int(res.json()["data"]["id"]))
    return res


async def _count(client, headers) -> int:
    return (await client.get(SESSIONS, headers=headers, params={"page_size": 100})).json()["data"]["total"]


def _ev(session_rows, event):  # helper for audit assertions
    return [r for r in session_rows if r.vevent_type == event]


# INT-01 -------------------------------------------------------------------- #
async def test_int01_session_list_has_expected_fields(client: AsyncClient, hr: dict):
    res = await client.get(SESSIONS, headers=hr)
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    assert items
    for key in ("candidate_name", "interviewer_name", "consent_status", "job_status"):
        assert key in items[0], key


# INT-02 -------------------------------------------------------------------- #
async def test_int02_valid_mp3_with_consent_creates_received_session(client: AsyncClient, hr: dict, track):
    res = await _upload(client, hr, "qa_interview.mp3", MP3, track)
    assert res.status_code == 201, res.text
    data = res.json()["data"]
    assert data["consent_status"] == "GRANTED"
    assert data["job_status"] == "RECEIVED"


# INT-03 -------------------------------------------------------------------- #
@pytest.mark.parametrize("name,content", [("qa_a.wav", WAV), ("qa_b.m4a", M4A)])
async def test_int03_wav_and_m4a_accepted(client: AsyncClient, hr: dict, track, name, content):
    res = await _upload(client, hr, name, content, track)
    assert res.status_code == 201, res.text
    assert res.json()["data"]["job_status"] == "RECEIVED"


# INT-04 / INT-12 ----------------------------------------------------------- #
@pytest.mark.parametrize("consent", ["NOT_GRANTED", "WITHDRAWN"])
async def test_int04_int12_no_consent_is_rejected_and_not_processed(client: AsyncClient, hr: dict, track, monkeypatch, consent):
    calls: list = []

    async def _spy(*a, **k):
        calls.append(1)

    monkeypatch.setattr(InterviewSessionService, "process_interview_job_async", staticmethod(_spy))
    res = await _upload(client, hr, "qa_noconsent.mp3", MP3, track, consent_status=consent)
    assert res.status_code == 201, res.text
    data = res.json()["data"]
    assert data["consent_status"] == consent
    assert data["job_status"] == "REJECTED_NO_CONSENT"
    assert data["progress_percentage"] == 0
    assert data["competency_points"] == []
    assert calls == []  # AI pipeline never scheduled


# INT-05 -------------------------------------------------------------------- #
async def test_int05_pdf_rejected_with_supported_formats_and_no_session(client: AsyncClient, hr: dict, track):
    before = await _count(client, hr)
    res = await _upload(client, hr, "qa_cv.pdf", PDF, track)
    assert res.status_code == 415, res.text
    for fmt in ("MP3", "WAV", "OGG", "M4A", "MP4", "WebM", "FLAC"):
        assert fmt in res.text
    assert await _count(client, hr) == before


# INT-06 -------------------------------------------------------------------- #
async def test_int06_text_renamed_to_mp3_rejected_by_signature(client: AsyncClient, hr: dict, track):
    res = await _upload(client, hr, "qa_fake.mp3", b"this is plain text, not audio at all", track)
    assert res.status_code == 415, res.text


# INT-07 / INT-08 ----------------------------------------------------------- #
async def test_int07_file_over_100mb_rejected(client: AsyncClient, hr: dict, track):
    res = await _upload(client, hr, "qa_big.mp3", MP3 + b"\x00" * (101 * 1024 * 1024), track)
    assert res.status_code == 413, res.text
    assert "100" in res.text


async def test_int08_file_just_under_limit_accepted(client: AsyncClient, hr: dict, track):
    res = await _upload(client, hr, "qa_99mb.mp3", MP3 + b"\x00" * (99 * 1024 * 1024), track)
    assert res.status_code == 201, res.text


# INT-09 -------------------------------------------------------------------- #
@pytest.mark.xfail(strict=False, reason="BUG: audio_duration is free text; 'abc' is stored instead of being rejected (expected MM:SS).")
async def test_int09_invalid_duration_is_rejected(client: AsyncClient, hr: dict, track):
    res = await client.post(
        f"{SESSIONS}/upload", headers=hr,
        json={"candidate_id": "1", "profile_id": "1", "consent_status": "NOT_GRANTED", "audio_duration": "abc"},
    )
    if res.status_code == 201:
        track.append(int(res.json()["data"]["id"]))
    assert res.status_code in (400, 422)


# INT-10 -------------------------------------------------------------------- #
async def test_int10_missing_file_is_rejected(client: AsyncClient, hr: dict):
    res = await client.post(f"{SESSIONS}/upload-file", headers=hr, data={"candidate_id": "1", "profile_id": "1"})
    assert res.status_code == 422


# INT-11 -------------------------------------------------------------------- #
async def test_int11_interviewer_sees_only_own_sessions(client: AsyncClient, hr: dict, santoso: dict, make_interview, test_session):
    hartono = (await _user(test_session, "budi.hartono")).nid
    santoso_id = (await _user(test_session, "budi.santoso")).nid
    other = await make_interview("budi.hartono")
    mine = await make_interview("budi.santoso")

    own = (await client.get(SESSIONS, headers=santoso, params={"page_size": 100})).json()["data"]["items"]
    own_ids = {i["id"] for i in own}
    assert str(mine) in own_ids and str(other) not in own_ids
    assert all(i["interviewer_id"] == str(santoso_id) for i in own)

    all_ids = {i["id"] for i in (await client.get(SESSIONS, headers=hr, params={"page_size": 100})).json()["data"]["items"]}
    assert {str(mine), str(other)} <= all_ids
    assert hartono != santoso_id


# REV-01 -------------------------------------------------------------------- #
async def test_rev01_transcript_has_speaker_labelled_segments(client: AsyncClient, hr: dict, make_interview):
    iid = await make_interview("budi.santoso")
    res = await client.get(f"{TRANSCRIPTS}/{iid}", headers=hr)
    assert res.status_code == 200
    segs = res.json()["data"]
    assert len(segs) == 2
    assert {s["speaker_type"] for s in segs} == {"INTERVIEWER", "CANDIDATE"}
    assert all(s["text"] and s["speaker_name"] for s in segs)


# REV-02 -------------------------------------------------------------------- #
async def test_rev02_seeded_competencies_have_evidence_quotes(client: AsyncClient, hr: dict):
    items = (await client.get(SESSIONS, headers=hr, params={"page_size": 100})).json()["data"]["items"]
    seeded = next((i for i in items if i["competency_points"] and any(p.get("evidences") for p in i["competency_points"])), None)
    assert seeded, "no completed session with competency points"
    for point in seeded["competency_points"]:
        if point.get("coverage_status") != "NOT_DISCUSSED":
            assert point["evidences"], point["competency_code"]
            assert all(e["quote_text"] and e["transcript_segment_id"] for e in point["evidences"])


@pytest.mark.xfail(strict=False, reason="GAP: competency points expose coverage_status only; no numeric score field (TC expects a score).")
async def test_rev02_competency_has_numeric_score(client: AsyncClient, hr: dict):
    items = (await client.get(SESSIONS, headers=hr, params={"page_size": 100})).json()["data"]["items"]
    point = next(p for i in items for p in i["competency_points"])
    assert "score" in point


# REV-03 -------------------------------------------------------------------- #
async def test_rev03_session_exposes_audio_url(client: AsyncClient, hr: dict, make_interview):
    iid = await make_interview("budi.santoso")
    data = (await client.get(f"{SESSIONS}/{iid}", headers=hr)).json()["data"]
    assert data["audio_url"] and data["audio_duration"]  # playback/seek itself is UI-only


# REV-04 / REV-05 ----------------------------------------------------------- #
async def test_rev04_hr_advance_is_saved_finalized_and_audited(client: AsyncClient, hr: dict, make_interview, test_session):
    iid = await make_interview(None)
    res = await client.post(DECISIONS + f"/{iid}", headers=hr,
                            json={"decision": "ADVANCE", "next_stage": "TECHNICAL_TEST", "notes": "Strong technical fit"})
    assert res.status_code == 200, res.text
    d = res.json()["data"]
    assert (d["decision"], d["workflow_status"], d["actor_role"]) == ("ADVANCE", "FINALIZED", "HR")
    assert d["next_stage"] == "TECHNICAL_TEST" and d["resulting_candidate_status"] == "TECHNICAL_TEST"

    shown = (await client.get(f"{SESSIONS}/{iid}", headers=hr)).json()["data"]["hr_decision"]
    assert shown["decision"] == "ADVANCE" and shown["notes"] == "Strong technical fit"

    test_session.expire_all()
    events = (await test_session.execute(select(AuditLog).where(AuditLog.vevent_type == "HR_DECISION_FINALIZED"))).scalars().all()
    assert any(f"session #{iid}" in e.vmasked_detail or str(iid) in e.vmasked_detail for e in events)


@pytest.mark.parametrize("decision,status", [("REJECT", "REJECTED"), ("HOLD", "COMPLETED")])
async def test_rev05_non_advance_needs_no_next_stage(client: AsyncClient, hr: dict, make_interview, decision, status):
    iid = await make_interview(None)
    res = await client.post(DECISIONS + f"/{iid}", headers=hr, json={"decision": decision, "notes": "Not a match for current role"})
    assert res.status_code == 200, res.text
    d = res.json()["data"]
    assert d["decision"] == decision and d["next_stage"] is None and d["resulting_candidate_status"] == status


async def test_rev05_invalid_decision_value_rejected(client: AsyncClient, hr: dict, make_interview):
    iid = await make_interview(None)
    res = await client.post(DECISIONS + f"/{iid}", headers=hr, json={"decision": "MAYBE", "notes": "x"})
    assert res.status_code == 422


# REV-06 -------------------------------------------------------------------- #
async def test_rev06_interviewer_recommendation_then_hr_finalizes(client: AsyncClient, hr: dict, santoso: dict, make_interview):
    iid = await make_interview("budi.santoso")

    # HR cannot skip the assigned interviewer
    early = await client.post(DECISIONS + f"/{iid}", headers=hr, json={"decision": "ADVANCE", "notes": "too early"})
    assert early.status_code == 403

    rec = await client.post(DECISIONS + f"/{iid}", headers=santoso, json={"decision": "ADVANCE", "notes": "Recommend proceed"})
    assert rec.status_code == 200, rec.text
    d = rec.json()["data"]
    assert (d["actor_role"], d["workflow_status"], d["resulting_candidate_status"]) == ("INTERVIEWER", "PENDING_HR_FOLLOWUP", "PENDING_HR_REVIEW")

    again = await client.post(DECISIONS + f"/{iid}", headers=santoso, json={"decision": "REJECT", "notes": "change"})
    assert again.status_code == 403  # interviewer is locked after submitting

    fin = await client.post(DECISIONS + f"/{iid}", headers=hr, json={"decision": "ADVANCE", "next_stage": "OFFERED", "notes": "Approved"})
    assert fin.status_code == 200, fin.text
    assert fin.json()["data"]["workflow_status"] == "FINALIZED"

    locked = await client.post(DECISIONS + f"/{iid}", headers=hr, json={"decision": "REJECT", "notes": "overwrite"})
    assert locked.status_code == 403  # FINALIZED is immutable


@pytest.mark.xfail(strict=False, reason="GAP: pending text is Indonesian 'Rekomendasi Pewawancara tercatat...' not 'Following up on interviewer recommendation (name): notes'.")
async def test_rev06_pending_text_matches_expected_wording(client: AsyncClient, hr: dict, santoso: dict, make_interview):
    iid = await make_interview("budi.santoso")
    await client.post(DECISIONS + f"/{iid}", headers=santoso, json={"decision": "ADVANCE", "notes": "Recommend proceed"})
    step = (await client.get(f"{SESSIONS}/{iid}", headers=hr)).json()["data"]["current_step"]
    assert "Following up on interviewer recommendation" in step and "Recommend proceed" in step


# REV-07 -------------------------------------------------------------------- #
async def test_rev07_salary_visible_to_hr_masked_for_interviewer(client: AsyncClient, hr: dict, santoso: dict):
    cands = (await client.get(f"{API}/candidates", headers=hr, params={"page_size": 100})).json()["data"]["items"]
    rina = next(c for c in cands if c["name"] == "Rina Kusuma")
    assert rina["expected_salary"]

    as_hr = (await client.get(f"{API}/candidates/{rina['id']}", headers=hr)).json()["data"]
    as_iv = (await client.get(f"{API}/candidates/{rina['id']}", headers=santoso)).json()["data"]
    assert as_hr["expected_salary"] and as_iv["expected_salary"] is None and as_iv["current_salary"] is None

    iv_list = (await client.get(f"{API}/candidates", headers=santoso, params={"page_size": 100})).json()["data"]["items"]
    assert all(c["expected_salary"] is None for c in iv_list)


# REV-08 -------------------------------------------------------------------- #
async def test_rev08_interviewer_cannot_open_or_decide_other_interviewers_session(
    client: AsyncClient, santoso: dict, make_interview, test_session
):
    other = await make_interview("budi.hartono")
    detail = await client.get(f"{SESSIONS}/{other}", headers=santoso)
    trans = await client.get(f"{TRANSCRIPTS}/{other}", headers=santoso)
    dec = await client.post(DECISIONS + f"/{other}", headers=santoso, json={"decision": "REJECT", "notes": "tamper"})
    dele = await client.delete(f"{SESSIONS}/{other}", headers=santoso)
    assert (detail.status_code, trans.status_code, dec.status_code, dele.status_code) == (403, 403, 403, 403)
    assert "Rina" not in detail.text and "Saya 5 tahun" not in trans.text

    test_session.expire_all()
    blocked = (await test_session.execute(select(AuditLog).where(AuditLog.vevent_type == "UNAUTHORIZED_INTERVIEW_ACCESS_BLOCKED"))).scalars().all()
    assert blocked


# REV-09 -------------------------------------------------------------------- #
async def test_rev09_processing_session_shows_progress_without_scores(client: AsyncClient, hr: dict, make_interview):
    iid = await make_interview("budi.santoso", job_status=2, segments=False)
    res = await client.get(f"{SESSIONS}/{iid}", headers=hr)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["job_status"] == "ACCESS_CHECKED" and data["progress_percentage"] < 100
    assert data["competency_points"] == []
    tr = await client.get(f"{TRANSCRIPTS}/{iid}", headers=hr)
    assert tr.status_code == 200 and tr.json()["data"] == []


@pytest.mark.xfail(strict=False, reason="BUG: a decision can be saved while the session is still processing (no job-status check).")
async def test_rev09_decision_blocked_while_processing(client: AsyncClient, hr: dict, make_interview):
    iid = await make_interview(None, job_status=2, segments=False)
    res = await client.post(DECISIONS + f"/{iid}", headers=hr, json={"decision": "REJECT", "notes": "premature"})
    assert res.status_code in (400, 409, 422)


# Extra guard: a session that already has a decision cannot be deleted ------- #
async def test_int_delete_session_with_decision_is_blocked(client: AsyncClient, hr: dict, make_interview):
    iid = await make_interview(None)
    await client.post(DECISIONS + f"/{iid}", headers=hr, json={"decision": "HOLD", "notes": "x"})
    assert (await client.delete(f"{SESSIONS}/{iid}", headers=hr)).status_code == 409
    assert uuid.uuid4()  # keep import used