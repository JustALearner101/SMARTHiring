from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.InterviewTranscriptDTO import TranscriptSegmentDTO
from app.exception.CustomException import ForbiddenException
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
                speaker_type="CANDIDATE" if "CANDIDATE" in (s.vspeaker_label or s.vspeaker_type).upper() else "INTERVIEWER",
                speaker_name=(
                    cand_name
                    if "CANDIDATE" in (s.vspeaker_label or s.vspeaker_type).upper()
                    else interviewer_name
                ),
                text=s.vtext,
                confidence=float(getattr(s, "fconfidence", 0.95) or 0.95),
                is_uncertain=(float(getattr(s, "fconfidence", 1.0) or 1.0) < 0.8),
            )
            for s in segments
        ]
