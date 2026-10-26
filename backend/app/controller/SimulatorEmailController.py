from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.DatabaseSession import get_db
from app.dto.BaseDTO import ApiResponse
from app.dto.SimulatorEmailDTO import SimulatedEmailDTO
from app.service.SimulatorEmailService import SimulatorEmailService

router = APIRouter(prefix="/simulator/email", tags=["SimulatorEmail"])


@router.get("/inbox", response_model=ApiResponse[list[SimulatedEmailDTO]])
async def list_simulated_emails(
    folder: str = Query("inbox", description="Folder: inbox, sent, or starred"),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[SimulatedEmailDTO]]:
    service = SimulatorEmailService(db)
    emails = await service.list_emails(folder=folder)
    return ApiResponse(data=emails, message="Berhasil mengambil email simulator")
