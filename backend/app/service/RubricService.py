from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.RubricDTO import CompetencyItemDTO, RubricProfileDTO
from app.repository.RubricRepository import RubricRepository


class RubricService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.rubric_repo = RubricRepository(session)

    async def list_rubric_profiles(self) -> list[RubricProfileDTO]:
        profiles = await self.rubric_repo.list_profiles_with_competencies()
        dtos = []
        for p in profiles:
            competencies = [
                CompetencyItemDTO(
                    id=str(c.nid),
                    code=c.vcode,
                    name=c.vname,
                    description=c.vreference_question or f"Evaluasi kompetensi {c.vname}",
                    weight=25.0,
                    target_score=4,
                )
                for c in p.competencies
            ]
            dtos.append(
                RubricProfileDTO(
                    id=str(p.nid),
                    code=p.vcode,
                    round_name=p.vname,
                    description=f"Rubrik standar ronde wawancara {p.vname} (v{p.vversion_no})",
                    competencies=competencies,
                )
            )
        return dtos
