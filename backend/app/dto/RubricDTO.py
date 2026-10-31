from typing import Literal

from pydantic import Field

from app.dto.BaseDTO import BaseDTO

RubricTargetRole = Literal["HR", "INTERVIEWER"]


class CompetencyItemDTO(BaseDTO):
    id: str
    code: str
    name: str
    description: str
    weight: float = 25.0
    target_score: int = 4
    target_level: int | None = None


class CompetencyCreateDTO(BaseDTO):
    code: str
    name: str
    description: str
    weight: float = 25.0
    target_score: int = 4
    target_level: int | None = None


class CompetencyUpdateDTO(BaseDTO):
    code: str | None = None
    name: str | None = None
    description: str | None = None
    weight: float | None = None
    target_score: int | None = None
    target_level: int | None = None


class RubricProfileDTO(BaseDTO):
    id: str
    code: str
    round_name: str
    description: str
    target_role: RubricTargetRole = "HR"
    department: str | None = None
    owner_user_id: str | None = None
    owner_name: str | None = None
    candidate_id: str | None = None
    candidate_name: str | None = None
    candidate_code: str | None = None
    applied_position: str | None = None
    competencies: list[CompetencyItemDTO] = Field(default_factory=list)


class RubricProfileCreateDTO(BaseDTO):
    code: str | None = None
    round_name: str | None = None
    description: str | None = None
    target_role: RubricTargetRole | None = None
    department: str | None = None
    candidate_id: str | None = None
