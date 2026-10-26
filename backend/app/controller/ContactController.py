from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.DatabaseSession import get_db
from app.dto.BaseDTO import ApiResponse
from app.dto.ContactDTO import (
    InterviewerContactDTO,
    InterviewerCreateDTO,
    InterviewerUpdateDTO,
)
from app.exception.CustomException import NotFoundException
from app.service.ContactService import ContactService

router = APIRouter(prefix="/contacts", tags=["ContactsDirectory"])


@router.get("", response_model=ApiResponse[list[InterviewerContactDTO]])
async def list_interviewers(
    department: str | None = Query(None, description="Filter by department"),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[InterviewerContactDTO]]:
    service = ContactService(db)
    contacts = await service.list_interviewers(department=department)
    return ApiResponse(data=contacts, message="Berhasil mengambil daftar kontak pewawancara")


@router.post("", response_model=ApiResponse[InterviewerContactDTO], status_code=status.HTTP_201_CREATED)
async def create_interviewer(
    dto: InterviewerCreateDTO,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[InterviewerContactDTO]:
    service = ContactService(db)
    created = await service.create_interviewer(dto)
    return ApiResponse(data=created, message="Kontak pewawancara berhasil ditambahkan")


@router.patch("/{user_id}", response_model=ApiResponse[InterviewerContactDTO])
async def update_interviewer(
    user_id: str,
    dto: InterviewerUpdateDTO,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[InterviewerContactDTO]:
    service = ContactService(db)
    updated = await service.update_interviewer(user_id, dto)
    if not updated:
        raise NotFoundException("Kontak tidak ditemukan")
    return ApiResponse(data=updated, message="Kontak pewawancara berhasil diperbarui")
