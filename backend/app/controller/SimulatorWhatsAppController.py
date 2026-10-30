from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.DatabaseSession import get_db
from app.dto.BaseDTO import ApiResponse
from app.dto.SimulatorWhatsAppDTO import (
    QuickReplyPresetDTO,
    SimulatedWhatsAppMessageDTO,
    SimulatorNotificationDTO,
)
from app.service.SimulatorWhatsAppService import SimulatorWhatsAppService

router = APIRouter(prefix="/simulator/whatsapp", tags=["SimulatorWhatsApp"])


@router.get("/messages", response_model=ApiResponse[list[SimulatedWhatsAppMessageDTO]])
async def list_whatsapp_messages(
    thread_id: str | None = Query(None, description="Filter by thread ID"),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[SimulatedWhatsAppMessageDTO]]:
    service = SimulatorWhatsAppService(db)
    messages = await service.list_whatsapp_messages(thread_id=thread_id)
    return ApiResponse(data=messages, message="Simulated WhatsApp messages retrieved successfully")


@router.post("/send", response_model=ApiResponse[SimulatedWhatsAppMessageDTO])
async def send_whatsapp_message(
    thread_id: str = Query("th-001", description="Thread ID"),
    text: str = Query(..., description="Message text"),
    sender: str = Query("candidate", description="Sender role: candidate, interviewer, or bot"),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[SimulatedWhatsAppMessageDTO]:
    service = SimulatorWhatsAppService(db)
    sent = await service.send_whatsapp_message(thread_id=thread_id, text=text, sender=sender)
    return ApiResponse(data=sent, message="Simulated message sent successfully")


@router.get("/quickPresets", response_model=ApiResponse[list[QuickReplyPresetDTO]])
async def list_quick_presets(
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[QuickReplyPresetDTO]]:
    service = SimulatorWhatsAppService(db)
    presets = await service.list_quick_presets()
    return ApiResponse(data=presets, message="Quick reply presets retrieved successfully")


@router.get("/notifications", response_model=ApiResponse[list[SimulatorNotificationDTO]])
async def list_notifications(
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[SimulatorNotificationDTO]]:
    service = SimulatorWhatsAppService(db)
    notifs = await service.list_notifications()
    return ApiResponse(data=notifs, message="Simulator notifications retrieved successfully")
