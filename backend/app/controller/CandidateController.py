from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.DatabaseSession import get_db
from app.dto.BaseDTO import ApiResponse, PaginatedResponse, PaginationParams
from app.dto.CandidateDTO import (
    CandidateCreateDTO,
    CandidateDTO,
    CandidateUpdateDTO,
)
from app.exception.CustomException import NotFoundException
from app.service.CandidateService import CandidateService

router = APIRouter(prefix="/candidates", tags=["CandidateManagement"])


@router.get("", response_model=ApiResponse[PaginatedResponse[CandidateDTO]])
async def list_candidates(
    query: str | None = Query(None, description="Search by name, email, code, or position"),
    status: str | None = Query(None, description="Filter by candidate application status"),
    params: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedResponse[CandidateDTO]]:
    service = CandidateService(db)
    result = await service.list_candidates(query=query, status=status, params=params)
    return ApiResponse(data=result, message="Berhasil mengambil data kandidat")


@router.get("/{candidate_id}", response_model=ApiResponse[CandidateDTO])
async def get_candidate(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CandidateDTO]:
    service = CandidateService(db)
    candidate = await service.get_candidate_by_id(candidate_id)
    if not candidate:
        raise NotFoundException("Kandidat tidak ditemukan")
    return ApiResponse(data=candidate, message="Berhasil mengambil detail kandidat")


@router.post("", response_model=ApiResponse[CandidateDTO], status_code=status.HTTP_201_CREATED)
async def create_candidate(
    dto: CandidateCreateDTO,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CandidateDTO]:
    service = CandidateService(db)
    created = await service.create_candidate(dto)
    return ApiResponse(data=created, message="Kandidat berhasil ditambahkan")


@router.patch("/{candidate_id}", response_model=ApiResponse[CandidateDTO])
async def update_candidate(
    candidate_id: str,
    dto: CandidateUpdateDTO,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CandidateDTO]:
    service = CandidateService(db)
    updated = await service.update_candidate(candidate_id, dto)
    if not updated:
        raise NotFoundException("Kandidat tidak ditemukan")
    return ApiResponse(data=updated, message="Kandidat berhasil diperbarui")
