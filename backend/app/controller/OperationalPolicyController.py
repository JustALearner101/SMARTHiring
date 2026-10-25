from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.DatabaseSession import get_db
from app.dto.BaseDTO import ApiResponse
from app.dto.OperationalPolicyDTO import OperationalPolicyDTO
from app.service.OperationalPolicyService import OperationalPolicyService

router = APIRouter(prefix="/operationalRules", tags=["OperationalPolicies"])


@router.get("", response_model=ApiResponse[OperationalPolicyDTO])
async def get_operational_policy(
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[OperationalPolicyDTO]:
    service = OperationalPolicyService(db)
    policy = await service.get_operational_policy()
    return ApiResponse(data=policy, message="Berhasil mengambil kebijakan operasional")


@router.put("", response_model=ApiResponse[OperationalPolicyDTO])
async def update_operational_policy(
    dto: OperationalPolicyDTO,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[OperationalPolicyDTO]:
    service = OperationalPolicyService(db)
    updated = await service.update_operational_policy(dto)
    return ApiResponse(data=updated, message="Kebijakan operasional berhasil diperbarui")
