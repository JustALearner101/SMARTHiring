from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.DatabaseSession import get_db
from app.dto.BaseDTO import ApiResponse
from app.dto.RubricDTO import RubricProfileDTO
from app.service.RubricService import RubricService

router = APIRouter(prefix="/rubrics", tags=["AssessmentRubrics"])


@router.get("", response_model=ApiResponse[list[RubricProfileDTO]])
async def list_rubrics(
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[RubricProfileDTO]]:
    service = RubricService(db)
    rubrics = await service.list_rubric_profiles()
    return ApiResponse(data=rubrics, message="Berhasil mengambil daftar profil rubrik penilaian")
