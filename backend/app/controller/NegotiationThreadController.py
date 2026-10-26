from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.DatabaseSession import get_db
from app.dto.BaseDTO import ApiResponse, PaginatedResponse, PaginationParams
from app.dto.NegotiationThreadDTO import (
    NegotiationThreadDTO,
    ThreadMessageDTO,
)
from app.exception.CustomException import NotFoundException
from app.service.NegotiationThreadService import NegotiationThreadService

router = APIRouter(prefix="/negotiationThreads", tags=["NegotiationThreads"])


@router.get("", response_model=ApiResponse[PaginatedResponse[NegotiationThreadDTO]])
async def list_threads(
    status: str | None = Query(None, description="Filter by thread status"),
    params: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PaginatedResponse[NegotiationThreadDTO]]:
    service = NegotiationThreadService(db)
    threads = await service.list_threads(status=status, params=params)
    return ApiResponse(data=threads, message="Berhasil mengambil daftar negosiasi triage")


@router.get("/{thread_id}", response_model=ApiResponse[NegotiationThreadDTO])
async def get_thread(
    thread_id: str,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[NegotiationThreadDTO]:
    service = NegotiationThreadService(db)
    thread = await service.get_thread(thread_id)
    if not thread:
        raise NotFoundException("Thread negosiasi tidak ditemukan")
    return ApiResponse(data=thread, message="Berhasil mengambil detail thread negosiasi")


@router.post("/{thread_id}/reply", response_model=ApiResponse[ThreadMessageDTO])
async def reply_thread_message(
    thread_id: str,
    content: str = Query(..., description="Message content"),
    sender_role: str = Query("HR_ADMIN", description="Sender role"),
    channel: str = Query("whatsapp", description="Communication channel"),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ThreadMessageDTO]:
    service = NegotiationThreadService(db)
    try:
        msg = await service.reply_thread_message(thread_id, content, sender_role=sender_role, channel=channel)
        return ApiResponse(data=msg, message="Balasan pesan negosiasi berhasil dicatat")
    except ValueError as e:
        raise NotFoundException(str(e)) from e
