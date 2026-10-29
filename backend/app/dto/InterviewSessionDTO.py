from typing import Literal

from pydantic import Field

from app.dto.BaseDTO import BaseDTO
from app.dto.InterviewDecisionDTO import HrDecisionDTO
from app.dto.InterviewTranscriptDTO import CompetencySummaryPointDTO

ConsentStatus = Literal["GRANTED", "NOT_GRANTED", "WITHDRAWN"]
InterviewScopeFilter = Literal["mine", "awaiting_hr", "all"]
JobStatus = Literal[
    "RECEIVED",
    "ACCESS_CHECKED",
    "TRANSCRIBED",
    "SUMMARIZED",
    "AUDITED",
    "IN_REVIEW",
    "COMPLETED",
    "REJECTED_NO_CONSENT",
]


class InterviewSessionDTO(BaseDTO):
    id: str
    candidate_id: str
    candidate_name: str
    candidate_code: str
    position: str
    profile_id: str | None = None
    round_name: str
    interviewer_id: str | None = None
    interviewer_name: str
    interviewer_role: str
    scheduled_at: str
    consent_status: ConsentStatus
    consent_at: str | None = None
    consent_notice_version: str | None = None
    audio_url: str | None = None
    audio_duration: str | None = None
    job_status: JobStatus
    progress_percentage: int = 100
    current_step: str = ""
    asr_engine: str | None = None
    competency_points: list[CompetencySummaryPointDTO] = Field(default_factory=list)
    hr_decision: HrDecisionDTO | None = None


class InterviewUploadRequestDTO(BaseDTO):
    candidate_id: str
    profile_id: str
    interviewer_id: str | None = None
    consent_status: ConsentStatus = "GRANTED"
    audio_url: str | None = None
    audio_duration: str | None = None
    notes: str | None = None
