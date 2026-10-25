from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.DatabaseSession import get_db
from app.dto.BaseDTO import ApiResponse, PaginatedResponse, PaginationParams
from app.dto.InterviewSessionDTO import (
    InterviewSessionDTO,
    InterviewUploadRequestDTO,
)
from app.exception.CustomException import NotFoundException
from app.service.InterviewSessionService import InterviewSessionService

router = APIRouter(prefix="/interviews/sessions", tags=["InterviewSessions"])


@router.get("", response_model=ApiResponse[PaginatedResponse[InterviewSessionDTO]])
async def list_interview_sessions(
    candidate_code: str | None = Query(None, description="Filter by candidate pseudonym code e.g. K-014"),
    params: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedResponse[InterviewSessionDTO]]:
    service = InterviewSessionService(db)
    result = await service.list_sessions(candidate_code=candidate_code, params=params)
    return ApiResponse(data=result, message="Berhasil mengambil daftar sesi wawancara")


@router.get("/{interview_id}", response_model=ApiResponse[InterviewSessionDTO])
async def get_interview_session(
    interview_id: str,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[InterviewSessionDTO]:
    service = InterviewSessionService(db)
    session = await service.get_session_detail(interview_id)
    if not session:
        raise NotFoundException("Sesi wawancara tidak ditemukan")
    return ApiResponse(data=session, message="Berhasil mengambil detail sesi wawancara")


@router.post("/upload", response_model=ApiResponse[InterviewSessionDTO], status_code=status.HTTP_201_CREATED)
async def upload_interview(
    dto: InterviewUploadRequestDTO,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[InterviewSessionDTO]:
    service = InterviewSessionService(db)
    created = await service.upload_interview(dto)
    return ApiResponse(data=created, message="File rekaman wawancara berhasil diunggah")
