from pydantic import Field

from app.dto.BaseDTO import BaseDTO


class CompetencyItemDTO(BaseDTO):
    id: str
    code: str
    name: str
    description: str
    weight: float = 25.0
    target_score: int = 4


class RubricProfileDTO(BaseDTO):
    id: str
    code: str
    round_name: str
    description: str
    competencies: list[CompetencyItemDTO] = Field(default_factory=list)
