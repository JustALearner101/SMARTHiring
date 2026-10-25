from datetime import datetime
from typing import Literal

from app.dto.BaseDTO import BaseDTO

HrDecisionType = Literal["ADVANCE", "HOLD", "REJECT"]


class HrDecisionDTO(BaseDTO):
    decision: HrDecisionType
    notes: str
    decided_at: datetime | str
    decided_by: str


class HrDecisionRequestDTO(BaseDTO):
    decision: HrDecisionType
    notes: str
    decided_by: str = "HR Admin"
