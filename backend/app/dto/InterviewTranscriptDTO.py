from typing import Literal

from pydantic import Field

from app.dto.BaseDTO import BaseDTO


class TranscriptSegmentDTO(BaseDTO):
    id: str
    segment_no: int
    start_ms: int
    end_ms: int
    timestamp_formatted: str
    speaker_label: str
    speaker_type: Literal["CANDIDATE", "INTERVIEWER", "UNKNOWN"]
    speaker_name: str
    text: str
    confidence: float
    is_uncertain: bool


class SummaryEvidenceDTO(BaseDTO):
    id: str
    transcript_segment_id: str
    quote_text: str
    timestamp_formatted: str
    start_ms: int
    relevance_score: float


class CompetencySummaryPointDTO(BaseDTO):
    id: str
    competency_code: str
    competency_name: str
    coverage_status: Literal["COVERED", "PARTIAL", "NOT_DISCUSSED"]
    content: str
    verification_status: Literal["VERIFIED", "UNVERIFIED", "NOT_APPLICABLE"]
    evidences: list[SummaryEvidenceDTO] = Field(default_factory=list)
