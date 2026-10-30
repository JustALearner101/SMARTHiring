from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.AppSecurity import require_roles
from app.db.DatabaseSession import get_db
from app.dto.BaseDTO import ApiResponse
from app.dto.InterviewDecisionDTO import HrDecisionDTO, HrDecisionRequestDTO
from app.model.UserModel import User
from app.service.InterviewDecisionService import InterviewDecisionService

router = APIRouter(prefix="/interviews/decisions", tags=["InterviewDecisions"])


@router.post("/{interview_id}", response_model=ApiResponse[HrDecisionDTO])
async def save_hr_decision(
    interview_id: str,
    dto: HrDecisionRequestDTO,
    current_user: User = Depends(require_roles(["HR", "ADMIN", "INTERVIEWER"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[HrDecisionDTO]:
    service = InterviewDecisionService(db)
    saved = await service.save_hr_decision(
        interview_id=interview_id,
        dto=dto,
        current_user=current_user,
    )
    msg = (
        "Interviewer evaluation recommendation submitted to HR for followup"
        if saved.workflow_status == "PENDING_HR_FOLLOWUP"
        else "HR final decision permanently finalized"
    )
    return ApiResponse(data=saved, message=msg)
