from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.DatabaseSession import get_db
from app.dto.BaseDTO import ApiResponse
from app.dto.InterviewDecisionDTO import HrDecisionDTO, HrDecisionRequestDTO
from app.exception.CustomException import NotFoundException
from app.service.InterviewDecisionService import InterviewDecisionService

router = APIRouter(prefix="/interviews/decisions", tags=["InterviewDecisions"])


@router.post("/{interview_id}", response_model=ApiResponse[HrDecisionDTO])
async def save_hr_decision(
    interview_id: str,
    dto: HrDecisionRequestDTO,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[HrDecisionDTO]:
    service = InterviewDecisionService(db)
    try:
        saved = await service.save_hr_decision(interview_id, dto)
        return ApiResponse(data=saved, message="Keputusan HR berhasil dicatat secara permanen")
    except ValueError as e:
        raise NotFoundException(str(e)) from e
