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

from app.core.AppSecurity import require_roles
from app.db.DatabaseSession import get_db
from app.dto.BaseDTO import ApiResponse, PaginatedResponse, PaginationParams
from app.dto.InterviewSessionDTO import (
    ConsentStatus,
    InterviewScopeFilter,
    InterviewSessionDTO,
    InterviewUploadRequestDTO,
)
from app.exception.CustomException import NotFoundException
from app.model.UserModel import User
from app.service.InterviewSessionService import InterviewSessionService

router = APIRouter(prefix="/interviews/sessions", tags=["InterviewSessions"])


@router.get("", response_model=ApiResponse[PaginatedResponse[InterviewSessionDTO]])
async def list_interview_sessions(
    candidate_code: str | None = Query(None, description="Filter by candidate pseudonym code e.g. K-014"),
    scope: InterviewScopeFilter = Query(
        "all",
        description="Filter scope: 'mine' (logged-in interviewer/HR), 'awaiting_hr' (pending HR follow-up), or 'all'",
    ),
    params: PaginationParams = Depends(),
    current_user: User = Depends(require_roles(["HR", "ADMIN", "INTERVIEWER"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedResponse[InterviewSessionDTO]]:
    service = InterviewSessionService(db)
    result = await service.list_sessions(
        candidate_code=candidate_code,
        scope=scope,
        params=params,
        current_user=current_user,
    )
    return ApiResponse(data=result, message="Interview sessions retrieved successfully")


@router.get("/{interview_id}", response_model=ApiResponse[InterviewSessionDTO])
async def get_interview_session(
    interview_id: str,
    current_user: User = Depends(require_roles(["HR", "ADMIN", "INTERVIEWER"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[InterviewSessionDTO]:
    service = InterviewSessionService(db)
    session = await service.get_session_detail(interview_id, current_user=current_user)
    if not session:
        raise NotFoundException("Interview session not found")
    return ApiResponse(data=session, message="Interview session details retrieved successfully")


@router.get("/{interview_id}/status", response_model=ApiResponse[InterviewSessionDTO])
async def get_interview_session_status(
    interview_id: str,
    current_user: User = Depends(require_roles(["HR", "ADMIN", "INTERVIEWER"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[InterviewSessionDTO]:
    service = InterviewSessionService(db)
    session = await service.get_session_detail(interview_id, current_user=current_user)
    if not session:
        raise NotFoundException("Interview session not found")
    return ApiResponse(data=session, message="Interview processing status retrieved successfully")


@router.post("/upload", response_model=ApiResponse[InterviewSessionDTO], status_code=status.HTTP_201_CREATED)
async def upload_interview(
    dto: InterviewUploadRequestDTO,
    current_user: User = Depends(require_roles(["HR", "ADMIN", "INTERVIEWER"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[InterviewSessionDTO]:
    service = InterviewSessionService(db)
    created = await service.upload_interview(dto=dto, current_user=current_user)
    return ApiResponse(data=created, message="Interview recording uploaded successfully")


@router.post("/upload-file", response_model=ApiResponse[InterviewSessionDTO], status_code=status.HTTP_201_CREATED)
async def upload_interview_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Binary audio/video file (MP3, WAV, M4A, MP4, etc.)"),
    candidate_id: str = Form("1"),
    profile_id: str = Form("1"),
    interviewer_id: str | None = Form(None),
    consent_status: ConsentStatus = Form("GRANTED"),
    notes: str | None = Form(None),
    current_user: User = Depends(require_roles(["HR", "ADMIN", "INTERVIEWER"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[InterviewSessionDTO]:
    content = await file.read()
    service = InterviewSessionService(db)
    created = await service.upload_interview_file(
        filename=file.filename or "recording.mp3",
        content=content,
        candidate_id=candidate_id,
        profile_id=profile_id,
        interviewer_id=interviewer_id,
        consent_status=consent_status,
        notes=notes,
        background_tasks=background_tasks,
        current_user=current_user,
    )
    return ApiResponse(data=created, message="Recording file validated and uploaded for asynchronous processing")


@router.delete("/{interview_id}", response_model=ApiResponse[dict[str, str]])
async def delete_interview_session(
    interview_id: str,
    current_user: User = Depends(require_roles(["HR", "ADMIN", "INTERVIEWER"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict[str, str]]:
    service = InterviewSessionService(db)
    await service.delete_session(interview_id=interview_id, current_user=current_user)
    return ApiResponse(data={"id": interview_id}, message="Interview session deleted successfully")
