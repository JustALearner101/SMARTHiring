from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.InterviewTranscriptDTO import TranscriptSegmentDTO
from app.exception.CustomException import ForbiddenException, NotFoundException
from app.model.UserModel import User
from app.repository.InterviewSessionRepository import InterviewSessionRepository
from app.repository.InterviewTranscriptRepository import InterviewTranscriptRepository
from app.service.AuditLogService import AuditLogService


class InterviewTranscriptService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.session_repo = InterviewSessionRepository(session)
        self.transcript_repo = InterviewTranscriptRepository(session)
        self.audit_service = AuditLogService(session)

    @staticmethod
    def _format_time_ms(ms: int) -> str:
        seconds = ms // 1000
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"

    async def get_transcripts(
        self,
        interview_id: str,
        current_user: User | None = None,
    ) -> list[TranscriptSegmentDTO]:
        if not interview_id.isdigit():
            return []
        int_id = int(interview_id)
        interview = await self.session_repo.get_interview_detail(int_id)
        if not interview:
            return []

        if current_user and current_user.vrole == "INTERVIEWER" and interview.nid_interviewer != current_user.nid:
            await self.audit_service.log_event(
                event_type="UNAUTHORIZED_INTERVIEW_ACCESS_BLOCKED",
                actor=current_user.vname,
                actor_type="HUMAN",
                title="Unauthorized Transcript Access Blocked",
                description=(
                    f"Pewawancara '{current_user.vname}' mencoba mengakses transkrip sesi wawancara #{int_id} milik pengguna lain."
                ),
                metadata={"interview_id": int_id, "attempted_by_user_id": current_user.nid},
            )
            raise ForbiddenException(
                "Akses ditolak: Anda hanya berwenang melihat transkrip wawancara yang ditugaskan kepada Anda."
            )

        if not interview.source_files or not interview.source_files[-1].jobs:
            return []

        cand_name = interview.candidate.vname if interview.candidate else "Kandidat"
        assigned_user = getattr(interview, "interviewer", None) or (
            getattr(interview.profile, "owner", None) if getattr(interview, "profile", None) else None
        )
        interviewer_name = assigned_user.vname if assigned_user else "Interviewer"

        sorted_sfs = sorted(interview.source_files, key=lambda sf: sf.nid)
        sorted_jobs = sorted(sorted_sfs[-1].jobs, key=lambda jb: jb.nid)
        job = sorted_jobs[-1]
        segments = await self.transcript_repo.list_by_job(job.nid)
        return [
            TranscriptSegmentDTO(
                id=str(s.nid),
                segment_no=s.nsegment_no,
                start_ms=s.nstart_ms,
                end_ms=s.nend_ms,
                timestamp_formatted=self._format_time_ms(s.nstart_ms),
                speaker_label=s.vspeaker_label or s.vspeaker_type,
                speaker_type="CANDIDATE" if (s.vspeaker_type or "").upper() == "CANDIDATE" else "INTERVIEWER",
                speaker_name=(
                    cand_name
                    if (s.vspeaker_type or "").upper() == "CANDIDATE"
                    else interviewer_name
                ),
                text=s.vtext,
                confidence=float(getattr(s, "fconfidence", 0.95) or 0.95),
                is_uncertain=(float(getattr(s, "fconfidence", 1.0) or 1.0) < 0.8),
            )
            for s in segments
        ]

    async def swap_session_speakers(
        self,
        interview_id: str,
        current_user: User,
    ) -> Any:
        """Inverts speaker roles (CANDIDATE <-> INTERVIEWER) on all segments and re-evaluates AI competency analysis."""
        if not interview_id.isdigit():
            raise NotFoundException("Sesi wawancara tidak ditemukan.")
        int_id = int(interview_id)
        interview = await self.session_repo.get_interview_detail(int_id)
        if not interview or not interview.source_files:
            raise NotFoundException("Data sesi wawancara tidak ditemukan.")

        sorted_sfs = sorted(interview.source_files, key=lambda sf: sf.nid)
        if not sorted_sfs or not sorted_sfs[-1].jobs:
            raise NotFoundException("Data transkrip wawancara tidak ditemukan.")

        sorted_jobs = sorted(sorted_sfs[-1].jobs, key=lambda jb: jb.nid)
        job = sorted_jobs[-1]
        segments = await self.transcript_repo.list_by_job(job.nid)
        if not segments:
            raise NotFoundException("Tidak ada segmen transkrip yang dapat ditukar.")

        for s in segments:
            current_type = (s.vspeaker_type or "CANDIDATE").upper()
            s.vspeaker_type = "INTERVIEWER" if current_type == "CANDIDATE" else "CANDIDATE"
            self.session.add(s)

        await self.session.commit()

        # Re-run analyzer pipeline to sync competencies & verbatim quotes with new candidate speech
        from app.agent.InterviewAnalyzerGraph import run_interview_analyzer_pipeline
        source_file = sorted_sfs[-1]
        await run_interview_analyzer_pipeline(
            session=self.session,
            interview_id=interview.nid,
            candidate_id=interview.nid_candidate,
            profile_id=interview.nid_profile,
            consent_status=interview.vconsent_status,
            notes=f"Speakers swapped and re-evaluated by {current_user.vname}",
            audio_url=source_file.vurl if source_file else None,
            audio_duration=source_file.vduration if source_file else None,
            job_id=job.nid,
        )

        from app.service.AuditLogService import AuditLogService
        audit_service = AuditLogService(self.session)
        await audit_service.log_event(
            event_type="INTERVIEW_SPEAKERS_SWAPPED",
            actor=current_user.vname,
            actor_type="HUMAN",
            title=f"Speakers Swapped: Sesi #{interview.nid}",
            description=f"Peran pembicara transkrip (Kandidat <-> Pewawancara) ditukar dan dievaluasi ulang oleh {current_user.vname}.",
            metadata={"interview_id": interview.nid, "job_id": job.nid},
        )

        from app.service.InterviewSessionService import InterviewSessionService
        session_svc = InterviewSessionService(self.session)
        self.session.expire_all()
        updated_detail = await self.session_repo.get_interview_detail(int_id)
        return session_svc._to_session_dto(updated_detail or interview)

    async def re_evaluate_session(
        self,
        interview_id: str,
        current_user: User,
    ) -> Any:
        """Re-runs AI competency evaluation and evidence extraction on existing transcript."""
        if not interview_id.isdigit():
            raise NotFoundException("Sesi wawancara tidak ditemukan.")
        int_id = int(interview_id)
        interview = await self.session_repo.get_interview_detail(int_id)
        if not interview or not interview.source_files:
            raise NotFoundException("Data sesi wawancara tidak ditemukan.")

        sorted_sfs = sorted(interview.source_files, key=lambda sf: sf.nid)
        if not sorted_sfs or not sorted_sfs[-1].jobs:
            raise NotFoundException("Data transkrip wawancara tidak ditemukan.")

        sorted_jobs = sorted(sorted_sfs[-1].jobs, key=lambda jb: jb.nid)
        job = sorted_jobs[-1]
        source_file = sorted_sfs[-1]

        segments = await self.transcript_repo.list_by_job(job.nid)
        if segments and source_file:
            max_end = max((s.nend_ms for s in segments), default=0)
            if max_end > 0:
                secs = max_end // 1000
                source_file.vduration = f"{secs // 60:02d}:{secs % 60:02d}"
                self.session.add(source_file)
                await self.session.commit()

        from app.agent.InterviewAnalyzerGraph import run_interview_analyzer_pipeline
        await run_interview_analyzer_pipeline(
            session=self.session,
            interview_id=interview.nid,
            candidate_id=interview.nid_candidate,
            profile_id=interview.nid_profile,
            consent_status=interview.vconsent_status,
            notes=f"Re-evaluated by {current_user.vname}",
            audio_url=source_file.vurl if source_file else None,
            audio_duration=source_file.vduration if source_file else None,
            job_id=job.nid,
        )

        from app.service.AuditLogService import AuditLogService
        audit_service = AuditLogService(self.session)
        await audit_service.log_event(
            event_type="INTERVIEW_RE_EVALUATED",
            actor=current_user.vname,
            actor_type="HUMAN",
            title=f"Session Re-Evaluated: Sesi #{interview.nid}",
            description=f"Evaluasi kompetensi wawancara dinilai ulang dari transkrip oleh {current_user.vname}.",
            metadata={"interview_id": interview.nid, "job_id": job.nid},
        )

        from app.service.InterviewSessionService import InterviewSessionService
        session_svc = InterviewSessionService(self.session)
        self.session.expire_all()
        updated_detail = await self.session_repo.get_interview_detail(int_id)
        return session_svc._to_session_dto(updated_detail or interview)
