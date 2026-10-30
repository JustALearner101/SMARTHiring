from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.AppSecurity import require_roles
from app.db.DatabaseSession import get_db
from app.dto.BaseDTO import ApiResponse
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
