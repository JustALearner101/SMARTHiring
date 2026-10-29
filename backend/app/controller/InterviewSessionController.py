from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.DatabaseSession import get_db
from app.dto.BaseDTO import ApiResponse, PaginatedResponse, PaginationParams
from app.dto.InterviewSessionDTO import (
    ConsentStatus,
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


@router.get("/{interview_id}/status", response_model=ApiResponse[InterviewSessionDTO])
async def get_interview_session_status(
    interview_id: str,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[InterviewSessionDTO]:
    service = InterviewSessionService(db)
    session = await service.get_session_detail(interview_id)
    if not session:
        raise NotFoundException("Sesi wawancara tidak ditemukan")
    return ApiResponse(data=session, message="Berhasil mengambil status progres pemrosesan wawancara")


@router.post("/upload", response_model=ApiResponse[InterviewSessionDTO], status_code=status.HTTP_201_CREATED)
async def upload_interview(
    dto: InterviewUploadRequestDTO,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[InterviewSessionDTO]:
    service = InterviewSessionService(db)
    created = await service.upload_interview(dto)
    return ApiResponse(data=created, message="File rekaman wawancara berhasil diunggah")


@router.post("/upload-file", response_model=ApiResponse[InterviewSessionDTO], status_code=status.HTTP_201_CREATED)
async def upload_interview_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Binary audio/video file (MP3, WAV, M4A, MP4, etc.)"),
    candidate_id: str = Form("1"),
    profile_id: str = Form("1"),
    consent_status: ConsentStatus = Form("GRANTED"),
    notes: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[InterviewSessionDTO]:
    content = await file.read()
    service = InterviewSessionService(db)
    created = await service.upload_interview_file(
        filename=file.filename or "recording.mp3",
        content=content,
        candidate_id=candidate_id,
        profile_id=profile_id,
        consent_status=consent_status,
        notes=notes,
        background_tasks=background_tasks,
    )
    return ApiResponse(data=created, message="File rekaman berhasil divalidasi dan diunggah untuk pemrosesan asinkron")
