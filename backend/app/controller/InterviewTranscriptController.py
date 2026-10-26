from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.DatabaseSession import get_db
from app.dto.BaseDTO import ApiResponse
from app.dto.InterviewTranscriptDTO import TranscriptSegmentDTO
from app.service.InterviewTranscriptService import InterviewTranscriptService

router = APIRouter(prefix="/interviews/transcripts", tags=["InterviewTranscripts"])


@router.get("/{interview_id}", response_model=ApiResponse[list[TranscriptSegmentDTO]])
async def get_interview_transcripts(
    interview_id: str,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[TranscriptSegmentDTO]]:
    service = InterviewTranscriptService(db)
    transcripts = await service.get_transcripts(interview_id)
    return ApiResponse(data=transcripts, message="Berhasil mengambil transkrip wawancara")
