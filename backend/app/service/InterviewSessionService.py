from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.InterviewAnalyzerGraph import run_interview_analyzer_pipeline
from app.dto.BaseDTO import PaginatedResponse, PaginationParams
from app.dto.InterviewDecisionDTO import HrDecisionDTO
from app.dto.InterviewSessionDTO import (
    InterviewSessionDTO,
    InterviewUploadRequestDTO,
)
from app.dto.InterviewTranscriptDTO import (
    CompetencySummaryPointDTO,
    SummaryEvidenceDTO,
)
from app.model.InterviewModel import Interview, SourceFile
from app.model.JobModel import Job
from app.repository.CandidateRepository import CandidateRepository
from app.repository.InterviewSessionRepository import InterviewSessionRepository
from app.repository.RubricRepository import RubricRepository


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
        audio_url = None
        audio_duration = None
        competency_points_dto = []
        hr_decision_dto = None

        if interview.vconsent_status != "GRANTED":
            job_status = "REJECTED_NO_CONSENT"

        if interview.source_files:
            latest_sf = interview.source_files[-1]
            audio_url = latest_sf.vurl
            audio_duration = latest_sf.vduration

            if latest_sf.jobs:
                latest_job = latest_sf.jobs[-1]
                if interview.vconsent_status == "GRANTED":
                    job_status = "COMPLETED" if latest_job.nstatus == 10 else "IN_REVIEW"

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

    async def upload_interview(self, dto: InterviewUploadRequestDTO) -> InterviewSessionDTO:
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
        )
        self.session.add(job)
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
