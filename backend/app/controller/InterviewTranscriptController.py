from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.AppSecurity import require_roles
from app.db.DatabaseSession import get_db
from app.dto.BaseDTO import ApiResponse
from app.dto.InterviewSessionDTO import InterviewSessionDTO
from app.dto.InterviewTranscriptDTO import TranscriptSegmentDTO
from app.model.UserModel import User
from app.service.InterviewTranscriptService import InterviewTranscriptService

router = APIRouter(prefix="/interviews/transcripts", tags=["InterviewTranscripts"])


@router.get("/{interview_id}", response_model=ApiResponse[list[TranscriptSegmentDTO]])
async def get_interview_transcripts(
    interview_id: str,
    current_user: User = Depends(require_roles(["HR", "ADMIN", "INTERVIEWER"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[TranscriptSegmentDTO]]:
    service = InterviewTranscriptService(db)
    transcripts = await service.get_transcripts(interview_id, current_user=current_user)
    return ApiResponse(data=transcripts, message="Interview transcripts retrieved successfully")


@router.post("/{interview_id}/swap-speakers", response_model=ApiResponse[InterviewSessionDTO])
async def swap_interview_speakers(
    interview_id: str,
    current_user: User = Depends(require_roles(["HR", "ADMIN", "INTERVIEWER"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[InterviewSessionDTO]:
    service = InterviewTranscriptService(db)
    updated_session = await service.swap_session_speakers(interview_id, current_user=current_user)
    return ApiResponse(data=updated_session, message="Speaker roles successfully swapped and re-evaluated")


@router.post("/{interview_id}/re-evaluate", response_model=ApiResponse[InterviewSessionDTO])
async def re_evaluate_interview_session(
    interview_id: str,
    current_user: User = Depends(require_roles(["HR", "ADMIN", "INTERVIEWER"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[InterviewSessionDTO]:
    service = InterviewTranscriptService(db)
    updated_session = await service.re_evaluate_session(interview_id, current_user=current_user)
    return ApiResponse(data=updated_session, message="Interview session successfully re-evaluated from transcript")
