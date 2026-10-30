import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.InterviewAnalyzerGraph import run_interview_analyzer_pipeline
from app.dto.BaseDTO import PaginatedResponse, PaginationParams
from app.dto.InterviewDecisionDTO import HrDecisionDTO
from app.dto.InterviewSessionDTO import (
    ConsentStatus,
    InterviewScopeFilter,
    InterviewSessionDTO,
    InterviewUploadRequestDTO,
)
from app.dto.InterviewTranscriptDTO import (
    CompetencySummaryPointDTO,
    SummaryEvidenceDTO,
)
from app.exception.CustomException import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.model.AuditModel import AuditLog
from app.model.FollowupModel import FollowupPlan
from app.model.InterviewModel import Interview, SourceFile
from app.model.JobModel import Job, TranscriptSegment
from app.model.SummaryModel import Flag, SummaryEvidence, SummaryPoint
from app.model.UserModel import User
from app.repository.CandidateRepository import CandidateRepository
from app.repository.InterviewSessionRepository import InterviewSessionRepository
from app.repository.RubricRepository import RubricRepository
from app.service.AuditLogService import AuditLogService
from app.service.ObjectStorageService import ObjectStorageService
from app.service.SpeechToTextService import SpeechToTextService
from app.util.FileValidator import validate_audio_video_upload

logger = logging.getLogger(__name__)


class InterviewSessionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.interview_repo = InterviewSessionRepository(session)
        self.candidate_repo = CandidateRepository(session)
        self.rubric_repo = RubricRepository(session)
        self.audit_service = AuditLogService(session)
        self.storage_service = ObjectStorageService()

    @staticmethod
    def _format_time_ms(ms: int) -> str:
        total_seconds = ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def _to_session_dto(self, interview: Interview) -> InterviewSessionDTO:
        candidate_name = interview.candidate.vname if interview.candidate else f"Candidate #{interview.nid_candidate}"
        candidate_code = interview.candidate.vcandidate_code if interview.candidate else f"CAND-{interview.nid_candidate}"
        position = interview.candidate.vjob_position if interview.candidate else "General Candidate"
        round_name = interview.profile.vname if interview.profile else "Technical Assessment Round"

        interviewer_name = interview.interviewer.vname if getattr(interview, "interviewer", None) else "Pewawancara Utama"
        interviewer_role = interview.interviewer.vrole if getattr(interview, "interviewer", None) else "INTERVIEWER"
        interviewer_id_str = str(interview.nid_interviewer) if interview.nid_interviewer else None

        job_status = "RECEIVED"
        progress_percentage = 100
        current_step = "Selesai"
        audio_url: str | None = None
        audio_duration: str | None = None
        asr_engine: str | None = None
        competency_points_dto: list[CompetencySummaryPointDTO] = []
        hr_decision_dto: HrDecisionDTO | None = None

        if getattr(interview, "source_files", None) and interview.source_files:
            sf = interview.source_files[0]
            audio_url = sf.vurl
            audio_duration = sf.vduration

            if getattr(sf, "jobs", None) and sf.jobs:
                latest_job = sf.jobs[-1]
                asr_engine = latest_job.vasr_engine

                status_map = {
                    1: ("RECEIVED", 15, "Menunggu antrean pemrosesan"),
                    2: ("ACCESS_CHECKED", 35, "Memproses ASR dan transkripsi audio"),
                    3: ("TRANSCRIBED", 60, "Memindai instruksi dan audit guardrail"),
                    4: ("SUMMARIZED", 85, "Mengekstrak bukti kompetensi rubrik"),
                    10: ("COMPLETED", 100, "Pemrosesan selesai"),
                    90: ("REJECTED_NO_CONSENT", 100, "Ditolak: Kandidat tidak memberikan persetujuan consent"),
                }
                meta = status_map.get(
                    latest_job.nstatus,
                    ("IN_REVIEW", 90, "Menunggu tinjauan evaluasi"),
                )
                job_status, progress_percentage, current_step = meta

                for sp in getattr(latest_job, "summary_points", []):
                    evidences_dto = [
                        SummaryEvidenceDTO(
                            id=str(ev.nid),
                            transcript_segment_id=str(ev.nid_transcript),
                            quote_text=ev.vquote,
                            timestamp_formatted=(
                                self._format_time_ms(ev.transcript.nstart_ms)
                                if getattr(ev, "transcript", None)
                                else "00:00"
                            ),
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
                    sorted_decisions = sorted(
                        latest_job.hr_decisions,
                        key=lambda item: (item.ddecided_at, item.nid),
                    )
                    d = sorted_decisions[-1]
                    decider_name = d.decided_by.vname if getattr(d, "decided_by", None) else "HR Admin"
                    wf_status = (
                        "PENDING_HR_FOLLOWUP"
                        if getattr(d, "vworkflow_status", "FINALIZED") == "PENDING_HR_FOLLOWUP"
                        else "FINALIZED"
                    )
                    if wf_status == "PENDING_HR_FOLLOWUP":
                        current_step = "Rekomendasi Pewawancara tercatat. Menunggu tindak lanjut final HR."
                    hr_decision_dto = HrDecisionDTO(
                        decision="ADVANCE" if d.vdecision == "PROCEED" else d.vdecision,  # type: ignore[arg-type]
                        next_stage=getattr(d, "vnext_stage", None),  # type: ignore[arg-type]
                        resulting_candidate_status=(
                            interview.candidate.vstatus if interview.candidate else None  # type: ignore[arg-type]
                        ),
                        actor_role="INTERVIEWER" if getattr(d, "vactor_role", "HR") == "INTERVIEWER" else "HR",
                        workflow_status=wf_status,  # type: ignore[arg-type]
                        notes=d.vnote or "",
                        decided_at=d.ddecided_at.isoformat(),
                        decided_by=decider_name,
                        decided_by_user_id=str(d.nid_decided_by) if d.nid_decided_by else None,
                    )

        return InterviewSessionDTO(
            id=str(interview.nid),
            candidate_id=str(interview.nid_candidate),
            candidate_name=candidate_name,
            candidate_code=candidate_code,
            position=position,
            profile_id=str(interview.nid_profile) if interview.nid_profile else None,
            round_name=round_name,
            interviewer_id=interviewer_id_str,
            interviewer_name=interviewer_name,
            interviewer_role=interviewer_role,
            scheduled_at=interview.dcrea.isoformat() if interview.dcrea else datetime.now(UTC).isoformat(),
            consent_status=interview.vconsent_status,  # type: ignore[arg-type]
            consent_at=interview.dconsent_at.isoformat() if interview.dconsent_at else None,
            consent_notice_version=interview.vconsent_notice_version,
            audio_url=audio_url,
            audio_stream_url=self.storage_service.resolve_audio_stream_url(audio_url, session_id=interview.nid),
            audio_duration=audio_duration,
            job_status=job_status,  # type: ignore[arg-type]
            progress_percentage=progress_percentage,
            current_step=current_step,
            asr_engine=asr_engine,
            competency_points=competency_points_dto,
            hr_decision=hr_decision_dto,
        )

    async def _resolve_interviewer_nid(
        self,
        profile_id_int: int | None,
        requested_interviewer_id: str | None,
        current_user: User | None,
    ) -> int | None:
        if current_user and current_user.vrole == "INTERVIEWER":
            return current_user.nid
        if requested_interviewer_id and requested_interviewer_id.isdigit():
            return int(requested_interviewer_id)
        if profile_id_int:
            profile = await self.rubric_repo.get_by_id(profile_id_int)
            if profile and profile.nid_owner_user:
                return profile.nid_owner_user
        if current_user:
            return current_user.nid
        return None

    async def list_sessions(
        self,
        candidate_code: str | None = None,
        scope: InterviewScopeFilter = "all",
        params: PaginationParams | None = None,
        current_user: User | None = None,
    ) -> PaginatedResponse[InterviewSessionDTO]:
        p = params or PaginationParams()
        interviewer_filter: int | None = None
        awaiting_hr_only = False

        if current_user and current_user.vrole == "INTERVIEWER":
            interviewer_filter = current_user.nid
        else:
            if scope == "mine" and current_user:
                interviewer_filter = current_user.nid
            elif scope == "awaiting_hr":
                awaiting_hr_only = True

        items, total = await self.interview_repo.list_interviews(
            candidate_code=candidate_code,
            interviewer_id=interviewer_filter,
            awaiting_hr_only=awaiting_hr_only,
            offset=p.offset,
            limit=p.limit,
        )
        return PaginatedResponse.create(
            items=[self._to_session_dto(it) for it in items],
            total=total,
            page=p.page,
            page_size=p.page_size,
        )

    async def get_session_detail(
        self,
        interview_id: str,
        current_user: User | None = None,
    ) -> InterviewSessionDTO | None:
        if not interview_id.isdigit():
            return None
        int_id = int(interview_id)
        interview = await self.interview_repo.get_interview_detail(int_id)
        if not interview:
            return None

        if current_user and current_user.vrole == "INTERVIEWER" and interview.nid_interviewer != current_user.nid:
            await self.audit_service.log_event(
                event_type="UNAUTHORIZED_INTERVIEW_ACCESS_BLOCKED",
                actor=current_user.vname,
                actor_type="HUMAN",
                title="Unauthorized Cross-Interviewer Access Blocked",
                description=(
                    f"Pewawancara '{current_user.vname}' (ID #{current_user.nid}) mencoba mengakses detail sesi "
                    f"wawancara #{int_id} milik pewawancara ID #{interview.nid_interviewer}."
                ),
                metadata={
                    "interview_id": int_id,
                    "attempted_by_user_id": current_user.nid,
                    "owner_interviewer_id": interview.nid_interviewer,
                },
            )
            raise ForbiddenException(
                "Akses ditolak: Anda hanya berwenang mengakses sesi wawancara yang ditugaskan kepada Anda."
            )

        return self._to_session_dto(interview)

    async def delete_session(
        self,
        interview_id: str,
        current_user: User,
    ) -> None:
        if not interview_id.isdigit():
            raise NotFoundException("Sesi wawancara tidak ditemukan.")
        int_id = int(interview_id)
        interview = await self.interview_repo.get_interview_detail(int_id)
        if not interview:
            raise NotFoundException("Sesi wawancara tidak ditemukan.")

        if current_user.vrole == "INTERVIEWER" and interview.nid_interviewer != current_user.nid:
            await self.audit_service.log_event(
                event_type="UNAUTHORIZED_INTERVIEW_ACCESS_BLOCKED",
                actor=current_user.vname,
                actor_type="HUMAN",
                title="Unauthorized Interview Deletion Blocked",
                description=(
                    f"Pewawancara '{current_user.vname}' mencoba menghapus sesi wawancara #{int_id} milik pengguna lain."
                ),
                metadata={"interview_id": int_id, "attempted_by_user_id": current_user.nid},
            )
            raise ForbiddenException("Akses ditolak: Anda tidak berwenang menghapus sesi wawancara milik pengguna lain.")

        has_decisions = any(
            bool(getattr(j, "hr_decisions", []))
            for sf in (interview.source_files or [])
            for j in (sf.jobs or [])
        )
        if has_decisions:
            raise ConflictException(
                "Sesi wawancara yang sudah memiliki keputusan evaluasi tidak dapat dihapus demi menjaga integritas jejak audit."
            )

        sf_ids = [sf.nid for sf in (interview.source_files or [])]
        job_ids = [j.nid for sf in (interview.source_files or []) for j in (sf.jobs or [])]
        sp_ids = [
            sp.nid
            for sf in (interview.source_files or [])
            for j in (sf.jobs or [])
            for sp in (j.summary_points or [])
        ]

        if job_ids:
            # Detach nullable audit & followup FKs so immutable hash-chained audit logs remain intact
            await self.session.execute(
                update(AuditLog).where(AuditLog.nid_job.in_(job_ids)).values(nid_job=None)
            )
            await self.session.execute(
                update(FollowupPlan).where(FollowupPlan.nid_job.in_(job_ids)).values(nid_job=None)
            )
            if sp_ids:
                await self.session.execute(
                    delete(SummaryEvidence).where(SummaryEvidence.nid_summary_point.in_(sp_ids))
                )
                await self.session.execute(delete(SummaryPoint).where(SummaryPoint.nid.in_(sp_ids)))
            await self.session.execute(delete(Flag).where(Flag.nid_job.in_(job_ids)))
            await self.session.execute(
                delete(TranscriptSegment).where(TranscriptSegment.nid_job.in_(job_ids))
            )
            await self.session.execute(delete(Job).where(Job.nid.in_(job_ids)))

        if sf_ids:
            await self.session.execute(delete(SourceFile).where(SourceFile.nid.in_(sf_ids)))

        cand_name = interview.candidate.vname if interview.candidate else f"#{interview.nid_candidate}"
        await self.session.execute(delete(Interview).where(Interview.nid == int_id))
        await self.session.commit()

        await self.audit_service.log_event(
            event_type="INTERVIEW_SESSION_DELETED",
            actor=current_user.vname,
            actor_type="HUMAN",
            title=f"Undecided Interview Session Deleted (#{int_id})",
            description=f"Sesi wawancara #{int_id} ({cand_name}) yang belum memiliki keputusan dihapus oleh {current_user.vname}.",
            metadata={"interview_id": int_id},
        )

    async def upload_interview(
        self,
        dto: InterviewUploadRequestDTO,
        current_user: User | None = None,
        pre_transcribed_segments: list[dict[str, Any]] | None = None,
    ) -> InterviewSessionDTO:
        cand_id = int(dto.candidate_id) if dto.candidate_id.isdigit() else 1
        prof_id = int(dto.profile_id) if dto.profile_id and dto.profile_id.isdigit() else None
        resolved_interviewer_nid = await self._resolve_interviewer_nid(
            profile_id_int=prof_id,
            requested_interviewer_id=dto.interviewer_id,
            current_user=current_user,
        )

        existing_profile = await self.rubric_repo.get_by_id(prof_id) if prof_id else None
        if not existing_profile:
            profile = await self.rubric_repo.get_or_create_candidate_profile(
                candidate_id=cand_id,
                owner_user_id=resolved_interviewer_nid,
                target_role="INTERVIEWER" if current_user and current_user.vrole == "INTERVIEWER" else "HR",
            )
            prof_id = profile.nid

        interview = Interview(
            nid_candidate=cand_id,
            nid_profile=prof_id,
            nid_interviewer=resolved_interviewer_nid,
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
        profile_id: str | None = None,
        interviewer_id: str | None = None,
        consent_status: ConsentStatus = "GRANTED",
        notes: str | None = None,
        background_tasks: BackgroundTasks | None = None,
        current_user: User | None = None,
    ) -> InterviewSessionDTO:
        """Validates payload and creates records, triggering background ASR and analysis if background_tasks provided."""
        validate_audio_video_upload(filename=filename, content=content)

        storage_dir = Path("storage/recordings")
        storage_dir.mkdir(parents=True, exist_ok=True)
        safe_filename = f"{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{filename.replace(' ', '_')}"
        file_path = storage_dir / safe_filename
        file_path.write_bytes(content)

        ext = filename.split(".")[-1].lower() if "." in filename else "mp3"
        mime_type = "audio/mpeg" if ext in ("mp3", "mp4") else f"audio/{ext}"
        storage_url, mode = await self.storage_service.upload_audio_file(
            content=content,
            filename=filename,
            content_type=mime_type,
        )
        saved_vurl = storage_url if mode == "SUPABASE" else str(file_path.as_posix())

        cand_id_int = int(candidate_id) if candidate_id.isdigit() else 1
        prof_id_int = int(profile_id) if profile_id and profile_id.isdigit() else None
        resolved_interviewer_nid = await self._resolve_interviewer_nid(
            profile_id_int=prof_id_int,
            requested_interviewer_id=interviewer_id,
            current_user=current_user,
        )

        existing_profile = await self.rubric_repo.get_by_id(prof_id_int) if prof_id_int else None
        if not existing_profile:
            profile = await self.rubric_repo.get_or_create_candidate_profile(
                candidate_id=cand_id_int,
                owner_user_id=resolved_interviewer_nid,
                target_role="INTERVIEWER" if current_user and current_user.vrole == "INTERVIEWER" else "HR",
            )
            prof_id_int = profile.nid

        interview = Interview(
            nid_candidate=cand_id_int,
            nid_profile=prof_id_int,
            nid_interviewer=resolved_interviewer_nid,
            vconsent_status=consent_status,
            dconsent_at=datetime.now(UTC),
            vconsent_notice_version="v2.1",
        )
        self.session.add(interview)
        await self.session.flush()

        sf = SourceFile(
            nid_interview=interview.nid,
            vtype="AUDIO",
            vurl=saved_vurl,
            vduration="00:00",
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

        if consent_status != "GRANTED":
            detail = await self.interview_repo.get_interview_detail(interview.nid)
            return self._to_session_dto(detail or interview)

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
            detail = await self.interview_repo.get_interview_detail(interview.nid)
            return self._to_session_dto(detail or interview)

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

    async def get_audio_response(
        self,
        interview_id: str,
        current_user: User | None = None,
    ) -> Any:
        """Returns audio file stream with HTTP 206 Partial Content or redirect to Supabase Presigned URL."""
        if not interview_id.isdigit():
            raise NotFoundException("Sesi wawancara tidak ditemukan")
        int_id = int(interview_id)
        interview = await self.interview_repo.get_interview_detail(int_id)
        if not interview or not interview.source_files:
            raise NotFoundException("File rekaman audio tidak ditemukan untuk sesi ini")

        sf = interview.source_files[0]
        vurl = sf.vurl or ""
        if vurl.startswith(("http://", "https://")):
            from starlette.responses import RedirectResponse
            return RedirectResponse(url=vurl, status_code=307)

        file_path = Path(vurl)
        if not file_path.exists():
            rec_path = Path("storage/recordings") / file_path.name
            if rec_path.exists():
                file_path = rec_path
            else:
                raise NotFoundException("File audio fisik tidak ditemukan di server")

        ext = file_path.suffix.lower().lstrip(".")
        media_type = "audio/mpeg"
        if ext in ("wav", "wave"):
            media_type = "audio/wav"
        elif ext in ("m4a", "mp4"):
            media_type = "audio/mp4"
        elif ext in ("ogg", "oga"):
            media_type = "audio/ogg"
        elif ext == "webm":
            media_type = "audio/webm"

        from starlette.responses import FileResponse
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=file_path.name,
        )

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
        job = (await session.execute(select(Job).where(Job.nid == job_id))).scalars().first()
        if not job:
            logger.error("Job %d not found for processing", job_id)
            return
        job.nstatus = 2
        await session.commit()

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

        max_end_ms = max([seg.get("end_ms", 0) for seg in segments], default=0)
        if max_end_ms > 0:
            total_sec = max_end_ms // 1000
            actual_duration = f"{total_sec // 60:02d}:{total_sec % 60:02d}"
        else:
            actual_duration = "00:00"

        sf_row = (await session.execute(select(SourceFile).where(SourceFile.nid_interview == interview_id))).scalars().first()
        if sf_row:
            sf_row.vduration = actual_duration
            await session.flush()

        await run_interview_analyzer_pipeline(
            session=session,
            interview_id=interview_id,
            candidate_id=candidate_id,
            profile_id=profile_id,
            consent_status="GRANTED",
            notes=notes,
            audio_url=sf_row.vurl if sf_row else str(file_path.as_posix()),
            audio_duration=actual_duration,
            job_id=job_id,
        )

        job = (await session.execute(select(Job).where(Job.nid == job_id))).scalars().first()
        interview_row = (await session.execute(select(Interview).where(Interview.nid == interview_id))).scalars().first()
        if interview_row:
            interview_row.dmodi = datetime.now(UTC)
            session.add(interview_row)
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
