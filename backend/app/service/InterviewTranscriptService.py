from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.InterviewTranscriptDTO import TranscriptSegmentDTO
from app.repository.InterviewSessionRepository import InterviewSessionRepository
from app.repository.InterviewTranscriptRepository import InterviewTranscriptRepository


class InterviewTranscriptService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.session_repo = InterviewSessionRepository(session)
        self.transcript_repo = InterviewTranscriptRepository(session)

    @staticmethod
    def _format_time_ms(ms: int) -> str:
        seconds = ms // 1000
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"

    async def get_transcripts(self, interview_id: str) -> list[TranscriptSegmentDTO]:
        int_id = int(interview_id) if interview_id.isdigit() else 1
        interview = await self.session_repo.get_interview_detail(int_id)
        if not interview or not interview.source_files or not interview.source_files[-1].jobs:
            return []

        job = interview.source_files[-1].jobs[-1]
        segments = await self.transcript_repo.list_by_job(job.nid)
        return [
            TranscriptSegmentDTO(
                id=str(s.nid),
                segment_no=s.nsegment_no,
                start_ms=s.nstart_ms,
                end_ms=s.nend_ms,
                timestamp_formatted=self._format_time_ms(s.nstart_ms),
                speaker_label=s.vspeaker_label,
                speaker_type="CANDIDATE" if "CANDIDATE" in s.vspeaker_label.upper() else "INTERVIEWER",
                speaker_name="Rina Kusuma" if "CANDIDATE" in s.vspeaker_label.upper() else "Budi Santoso",
                text=s.vtext,
                confidence=float(getattr(s, "fconfidence", 0.95) or 0.95),
                is_uncertain=(float(getattr(s, "fconfidence", 1.0) or 1.0) < 0.8),
            )
            for s in segments
        ]
