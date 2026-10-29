import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.InterviewAnalyzerGraph import run_interview_analyzer_pipeline
from app.dto.BaseDTO import PaginatedResponse, PaginationParams
from app.dto.InterviewDecisionDTO import HrDecisionDTO
from app.dto.InterviewSessionDTO import (
    ConsentStatus,
    InterviewSessionDTO,
    InterviewUploadRequestDTO,
)
from app.dto.InterviewTranscriptDTO import (
    CompetencySummaryPointDTO,
    SummaryEvidenceDTO,
)
from app.model.InterviewModel import Interview, SourceFile
from app.model.JobModel import Job, TranscriptSegment
from app.repository.CandidateRepository import CandidateRepository
from app.repository.InterviewSessionRepository import InterviewSessionRepository
from app.repository.RubricRepository import RubricRepository
from app.service.SpeechToTextService import SpeechToTextService
from app.util.FileValidator import validate_audio_video_upload

logger = logging.getLogger(__name__)


class InterviewSessionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.interview_repo = InterviewSessionRepository(session)
        self.candidate_repo = CandidateRepository(session)
        self.rubric_repo = RubricRepository(session)

    @staticmethod
    def _format_time_ms(ms: int) -> str:
        seconds = ms // 1000
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"

    def _to_session_dto(self, interview: Interview) -> InterviewSessionDTO:
        candidate_name = interview.candidate.vname if interview.candidate else "Kandidat"
        candidate_code = interview.candidate.vcandidate_code if interview.candidate else "CAND-000"
        position = interview.candidate.vjob_position if interview.candidate else "General Role"
        round_name = interview.profile.vname if interview.profile else "Interview Session"

        job_status = "RECEIVED"
        progress_percentage = 15
        current_step = "File rekaman diunggah, menunggu antrean pemrosesan..."
        audio_url = None
        audio_duration = None
        competency_points_dto = []
        hr_decision_dto = None
        asr_engine = None

        if interview.vconsent_status != "GRANTED":
            job_status = "REJECTED_NO_CONSENT"
            progress_percentage = 0
            current_step = "Ditolak: Kandidat tidak memberikan persetujuan perekaman (Consent Rejected)."

        if interview.source_files:
            latest_sf = interview.source_files[-1]
            audio_url = latest_sf.vurl
            audio_duration = latest_sf.vduration

            if latest_sf.jobs:
                latest_job = latest_sf.jobs[-1]
                asr_engine = latest_job.vasr_engine

                if interview.vconsent_status == "GRANTED":
                    status_code = latest_job.nstatus
                    if status_code == 1:
                        job_status = "RECEIVED"
                        progress_percentage = 15
                        current_step = "File rekaman diunggah, antrean pemrosesan aktif..."
                    elif status_code == 2:
                        job_status = "ACCESS_CHECKED"
                        progress_percentage = 30
                        current_step = "Validasi persetujuan kandidat & izin akses rekaman..."
                    elif status_code == 3:
                        job_status = "TRANSCRIBED"
                        progress_percentage = 60
                        engine_label = latest_job.vasr_engine or "ElevenLabs Scribe"
                        current_step = f"Transkripsi audio & speaker diarization ({engine_label}) selesai..."
                    elif status_code == 4:
                        job_status = "SUMMARIZED"
                        progress_percentage = 85
                        current_step = "Ekstraksi rubrik kompetensi & penelusuran bukti kutipan..."
                    elif status_code == 5:
                        job_status = "AUDITED"
                        progress_percentage = 95
                        current_step = "Audit verifikasi bukti kutipan & pendeteksian flag..."
                    elif status_code in (6, 10):
                        job_status = "COMPLETED" if status_code == 10 else "IN_REVIEW"
                        progress_percentage = 100
                        current_step = "Pemrosesan selesai. Siap ditinjau oleh HR."
                    elif status_code == 90:
                        job_status = "REJECTED_NO_CONSENT"
                        progress_percentage = 0
                        current_step = "Ditolak: Kandidat tidak memberikan persetujuan perekaman."
                    else:
                        job_status = "IN_REVIEW"
                        progress_percentage = 100
                        current_step = "Selesai"

                for sp in getattr(latest_job, "summary_points", []):
                    evidences_dto = [
                        SummaryEvidenceDTO(
                            id=str(ev.nid),
                            transcript_segment_id=str(ev.nid_transcript),
                            quote_text=ev.vquote,
                            timestamp_formatted=self._format_time_ms(ev.transcript.nstart_ms) if getattr(ev, "transcript", None) else "00:00",
                            start_ms=ev.transcript.nstart_ms if getattr(ev, "transcript", None) else 0,
                            relevance_score=0.95,
                        )
                        for ev in getattr(sp, "evidences", [])
                    ]
                    competency_points_dto.append(
                        CompetencySummaryPointDTO(
                            id=str(sp.nid),
                            competency_code=sp.competency.vcode if getattr(sp, "competency", None) else "C1",
                            competency_name=sp.competency.vname if getattr(sp, "competency", None) else "Competency",
                            coverage_status=sp.vcoverage_status,  # type: ignore[arg-type]
                            content=sp.vcontent,
                            verification_status=sp.vverification_status,  # type: ignore[arg-type]
                            evidences=evidences_dto,
                        )
                    )

                if getattr(latest_job, "hr_decisions", None):
                    d = latest_job.hr_decisions[-1]
                    decider_name = d.decided_by.vname if getattr(d, "decided_by", None) else "HR Admin"
                    hr_decision_dto = HrDecisionDTO(
                        decision="ADVANCE" if d.vdecision == "PROCEED" else d.vdecision,  # type: ignore[arg-type]
                        notes=d.vnote or "",
                        decided_at=d.ddecided_at.isoformat(),
                        decided_by=decider_name,
                    )

        return InterviewSessionDTO(
            id=str(interview.nid),
            candidate_id=str(interview.nid_candidate),
            candidate_name=candidate_name,
            candidate_code=candidate_code,
            position=position,
            round_name=round_name,
            interviewer_name="Budi Santoso",
            interviewer_role="VP of Engineering",
            scheduled_at=interview.dcrea.isoformat() if interview.dcrea else datetime.now(UTC).isoformat(),
            consent_status=interview.vconsent_status,  # type: ignore[arg-type]
            consent_at=interview.dconsent_at.isoformat() if interview.dconsent_at else None,
            consent_notice_version=interview.vconsent_notice_version,
            audio_url=audio_url,
            audio_duration=audio_duration,
            job_status=job_status,  # type: ignore[arg-type]
            progress_percentage=progress_percentage,
            current_step=current_step,
            asr_engine=asr_engine,
            competency_points=competency_points_dto,
            hr_decision=hr_decision_dto,
        )

    async def list_sessions(
        self,
        candidate_code: str | None = None,
        params: PaginationParams | None = None,
    ) -> PaginatedResponse[InterviewSessionDTO]:
        p = params or PaginationParams()
        items, total = await self.interview_repo.list_interviews(candidate_code=candidate_code, offset=p.offset, limit=p.limit)
        return PaginatedResponse.create(
            items=[self._to_session_dto(it) for it in items],
            total=total,
            page=p.page,
            page_size=p.page_size,
        )

    async def get_session_detail(self, interview_id: str) -> InterviewSessionDTO | None:
        int_id = int(interview_id) if interview_id.isdigit() else 1
        interview = await self.interview_repo.get_interview_detail(int_id)
        return self._to_session_dto(interview) if interview else None

    async def upload_interview(
        self,
        dto: InterviewUploadRequestDTO,
        pre_transcribed_segments: list[dict[str, Any]] | None = None,
    ) -> InterviewSessionDTO:
        cand_id = int(dto.candidate_id) if dto.candidate_id.isdigit() else 1
        prof_id = int(dto.profile_id) if dto.profile_id.isdigit() else 1

        interview = Interview(
            nid_candidate=cand_id,
            nid_profile=prof_id,
            vconsent_status=dto.consent_status,
            dconsent_at=datetime.now(UTC),
            vconsent_notice_version="v2.1",
        )
        self.session.add(interview)
        await self.session.flush()

        sf = SourceFile(
            nid_interview=interview.nid,
            vtype="AUDIO",
            vurl=dto.audio_url or "https://storage.smarthiring.ai/interviews/rec-001.mp3",
            vduration=dto.audio_duration or "45:20",
        )
        self.session.add(sf)
        await self.session.flush()

        job = Job(
            nid_source=sf.nid,
            nstatus=10 if dto.consent_status == "GRANTED" else 90,
            vasr_engine="ElevenLabs Scribe" if dto.consent_status == "GRANTED" else None,
            vasr_model_version="scribe_v1" if dto.consent_status == "GRANTED" else None,
        )
        self.session.add(job)
        await self.session.flush()

        # If ASR segments provided, persist them into tblt_transcript_segment
        if pre_transcribed_segments and dto.consent_status == "GRANTED":
            for seg in pre_transcribed_segments:
                seg_obj = TranscriptSegment(
                    nid_job=job.nid,
                    nsegment_no=seg["segment_no"],
                    nstart_ms=seg["start_ms"],
                    nend_ms=seg["end_ms"],
                    vspeaker_label=seg.get("speaker_label", seg.get("speaker", "CANDIDATE")),
                    vspeaker_type=seg.get("speaker", "CANDIDATE"),
                    vtext=seg["text"],
                    fconfidence=seg.get("confidence", 0.95),
                    nis_uncertain=1 if seg.get("confidence", 1.0) < 0.8 else 0,
                )
                self.session.add(seg_obj)

        await self.session.commit()

        # Run Pipeline 2: Post-Interview Transcript & Rubric Analyzer
        if dto.consent_status == "GRANTED":
            await run_interview_analyzer_pipeline(
                session=self.session,
                interview_id=interview.nid,
                candidate_id=cand_id,
                profile_id=prof_id,
                consent_status=dto.consent_status,
                notes=dto.notes,
                audio_url=sf.vurl,
                audio_duration=sf.vduration,
                job_id=job.nid,
            )

        detail = await self.interview_repo.get_interview_detail(interview.nid)
        return self._to_session_dto(detail or interview)

    async def upload_interview_file(
        self,
        filename: str,
        content: bytes,
        candidate_id: str,
        profile_id: str,
        consent_status: ConsentStatus = "GRANTED",
        notes: str | None = None,
        background_tasks: BackgroundTasks | None = None,
    ) -> InterviewSessionDTO:
        """Validates payload and creates records, triggering background ASR and analysis if background_tasks provided."""
        validate_audio_video_upload(filename=filename, content=content)

        storage_dir = Path("storage/recordings")
        storage_dir.mkdir(parents=True, exist_ok=True)
        safe_filename = f"{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{filename.replace(' ', '_')}"
        file_path = storage_dir / safe_filename
        file_path.write_bytes(content)

        cand_id_int = int(candidate_id) if candidate_id.isdigit() else 1
        prof_id_int = int(profile_id) if profile_id.isdigit() else 1

        interview = Interview(
            nid_candidate=cand_id_int,
            nid_profile=prof_id_int,
            vconsent_status=consent_status,
            dconsent_at=datetime.now(UTC),
            vconsent_notice_version="v2.1",
        )
        self.session.add(interview)
        await self.session.flush()

        sf = SourceFile(
            nid_interview=interview.nid,
            vtype="AUDIO",
            vurl=str(file_path.as_posix()),
            vduration="45:20",
        )
        self.session.add(sf)
        await self.session.flush()

        initial_status = 1 if consent_status == "GRANTED" else 90
        job = Job(
            nid_source=sf.nid,
            nstatus=initial_status,
            vasr_engine="ElevenLabs Scribe",
            vasr_model_version="scribe_v1",
        )
        self.session.add(job)
        await self.session.commit()

        # If consent is NOT granted, stop here
        if consent_status != "GRANTED":
            detail = await self.interview_repo.get_interview_detail(interview.nid)
            return self._to_session_dto(detail or interview)

        # If background_tasks is supplied, delegate to async background worker
        if background_tasks:
            background_tasks.add_task(
                InterviewSessionService.process_interview_job_async,
                interview_id=interview.nid,
                job_id=job.nid,
                file_path=file_path,
                filename=filename,
                candidate_id=cand_id_int,
                profile_id=prof_id_int,
                notes=notes,
            )
            # Return initial RECEIVED state (15% progress)
            detail = await self.interview_repo.get_interview_detail(interview.nid)
            return self._to_session_dto(detail or interview)

        # Synchronous fallback: process within self.session for unit test execution
        await self._process_job_with_session(
            session=self.session,
            interview_id=interview.nid,
            job_id=job.nid,
            file_path=file_path,
            filename=filename,
            candidate_id=cand_id_int,
            profile_id=prof_id_int,
            notes=notes,
        )
        detail = await self.interview_repo.get_interview_detail(interview.nid)
        return self._to_session_dto(detail or interview)

    @staticmethod
    async def _process_job_with_session(
        session: AsyncSession,
        interview_id: int,
        job_id: int,
        file_path: Path,
        filename: str,
        candidate_id: int,
        profile_id: int,
        notes: str | None = None,
    ) -> None:
        """Core execution pipeline logic shared by synchronous and asynchronous background modes."""
        # 1. Advance to ACCESS_CHECKED (2)
        job = (await session.execute(select(Job).where(Job.nid == job_id))).scalars().first()
        if not job:
            logger.error("Job %d not found for processing", job_id)
            return
        job.nstatus = 2
        await session.commit()

        # 2. Transcribe via SpeechToTextService (ElevenLabs Scribe -> Groq -> OpenAI -> Mock)
        cand_repo = CandidateRepository(session)
        candidate = await cand_repo.get_by_id(candidate_id)
        cand_name = candidate.vname if candidate else "Rina Kusuma"
        cand_role = candidate.vjob_position if candidate else "Senior Frontend Engineer"

        stt_service = SpeechToTextService()
        segments, engine_name, model_ver = await stt_service.transcribe_with_metadata(
            file_path_or_bytes=file_path,
            filename=filename,
            candidate_name=cand_name,
            candidate_role=cand_role,
            session_notes=notes,
        )

        # Persist segments & advance to TRANSCRIBED (3)
        job = (await session.execute(select(Job).where(Job.nid == job_id))).scalars().first()
        if job:
            job.vasr_engine = engine_name
            job.vasr_model_version = model_ver
            job.nstatus = 3
            for seg in segments:
                seg_obj = TranscriptSegment(
                    nid_job=job.nid,
                    nsegment_no=seg["segment_no"],
                    nstart_ms=seg["start_ms"],
                    nend_ms=seg["end_ms"],
                    vspeaker_label=seg.get("speaker_label", seg.get("speaker", "CANDIDATE")),
                    vspeaker_type=seg.get("speaker", "CANDIDATE"),
                    vtext=seg["text"],
                    fconfidence=seg.get("confidence", 0.95),
                    nis_uncertain=1 if seg.get("confidence", 1.0) < 0.8 else 0,
                )
                session.add(seg_obj)
            await session.commit()

        # 3. Run Rubric Analyzer LLM Graph
        await run_interview_analyzer_pipeline(
            session=session,
            interview_id=interview_id,
            candidate_id=candidate_id,
            profile_id=profile_id,
            consent_status="GRANTED",
            notes=notes,
            audio_url=str(file_path.as_posix()),
            audio_duration="45:20",
            job_id=job_id,
        )

        # 4. Finalize job status to COMPLETED (10)
        job = (await session.execute(select(Job).where(Job.nid == job_id))).scalars().first()
        if job and job.nstatus < 10:
            job.nstatus = 10
            await session.commit()
        logger.info("Successfully completed interview processing for job %d", job_id)

    @staticmethod
    async def process_interview_job_async(
        interview_id: int,
        job_id: int,
        file_path: Path,
        filename: str,
        candidate_id: int,
        profile_id: int,
        notes: str | None = None,
    ) -> None:
        """Asynchronous background entrypoint that opens dedicated AsyncSessionLocal."""
        from app.db.DatabaseSession import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            try:
                await InterviewSessionService._process_job_with_session(
                    session=session,
                    interview_id=interview_id,
                    job_id=job_id,
                    file_path=file_path,
                    filename=filename,
                    candidate_id=candidate_id,
                    profile_id=profile_id,
                    notes=notes,
                )
            except Exception:
                logger.exception("Failed during async background interview processing for job %d", job_id)
