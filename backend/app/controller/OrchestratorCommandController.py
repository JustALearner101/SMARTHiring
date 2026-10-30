from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.DatabaseSession import get_db
from app.dto.ActionPlanDTO import ActionPlanDTO
from app.dto.BaseDTO import ApiResponse
from app.dto.OrchestratorCommandDTO import (
    CommandRequestDTO,
    InboundReplyRequestDTO,
    PresetScenarioDTO,
)
from app.service.OrchestratorCommandService import OrchestratorCommandService

router = APIRouter(prefix="/orchestrator", tags=["OrchestratorCommands"])


@router.get("/scenarios", response_model=ApiResponse[list[PresetScenarioDTO]])
async def list_scenarios(
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[PresetScenarioDTO]]:
    service = OrchestratorCommandService(db)
    scenarios = await service.list_preset_scenarios()
    return ApiResponse(data=scenarios, message="Preset scenarios retrieved successfully")


@router.post("/command", response_model=ApiResponse[ActionPlanDTO | dict[str, Any]])
async def process_command(
    request: CommandRequestDTO,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ActionPlanDTO | dict[str, Any]]:
    service = OrchestratorCommandService(db)
    result = await service.execute_command(request)
    return ApiResponse(data=result, message="Natural language command processed successfully")


@router.post("/inbound-reply", response_model=ApiResponse[ActionPlanDTO | dict[str, Any]])
async def handle_inbound_reply(
    request: InboundReplyRequestDTO,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ActionPlanDTO | dict[str, Any]]:
    service = OrchestratorCommandService(db)
    result = await service.handle_inbound_reply(request)
    return ApiResponse(data=result, message="Candidate/interviewer reply processed successfully")
