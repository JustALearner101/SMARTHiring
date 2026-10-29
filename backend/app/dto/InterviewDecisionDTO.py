from datetime import datetime
from typing import Literal

from app.dto.BaseDTO import BaseDTO
from app.dto.CandidateDTO import ApplicationStatus

HrDecisionType = Literal["ADVANCE", "HOLD", "REJECT"]
AdvanceNextStage = Literal["NEXT_INTERVIEW", "TECHNICAL_TEST", "OFFERED"]
DecisionActorRole = Literal["INTERVIEWER", "HR"]
DecisionWorkflowStatus = Literal["PENDING_HR_FOLLOWUP", "FINALIZED"]


class HrDecisionDTO(BaseDTO):
    decision: HrDecisionType
    next_stage: AdvanceNextStage | None = None
    resulting_candidate_status: ApplicationStatus | None = None
    actor_role: DecisionActorRole = "HR"
    workflow_status: DecisionWorkflowStatus = "FINALIZED"
    notes: str
    decided_at: datetime | str
    decided_by: str
    decided_by_user_id: str | None = None


class HrDecisionRequestDTO(BaseDTO):
    decision: HrDecisionType
    next_stage: AdvanceNextStage | None = None
    notes: str
    decided_by: str | None = None
