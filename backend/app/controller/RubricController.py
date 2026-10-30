from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.AppSecurity import get_optional_current_user, require_roles
from app.db.DatabaseSession import get_db
from app.dto.BaseDTO import ApiResponse
from app.dto.RubricDTO import (
    CompetencyCreateDTO,
    CompetencyItemDTO,
    CompetencyUpdateDTO,
    RubricProfileCreateDTO,
    RubricProfileDTO,
)
from app.model.UserModel import User
from app.service.RubricService import RubricService

router = APIRouter(prefix="/rubrics", tags=["AssessmentRubrics"])


@router.get("", response_model=ApiResponse[list[RubricProfileDTO]])
async def list_rubrics(
    for_interviewer_id: str | None = Query(
        None,
        description="Optional interviewer user ID to load rubrics owned by that interviewer",
    ),
    candidate_id: str | None = Query(
        None,
        description="Optional candidate ID to filter rubrics for a specific candidate",
    ),
    current_user: User | None = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[RubricProfileDTO]]:
    service = RubricService(db)
    rubrics = await service.list_rubric_profiles(
        current_user=current_user,
        for_interviewer_id=for_interviewer_id,
        candidate_id=candidate_id,
    )
    return ApiResponse(data=rubrics, message="Rubric profiles retrieved successfully")


@router.post(
    "",
    response_model=ApiResponse[RubricProfileDTO],
    status_code=status.HTTP_201_CREATED,
)
async def create_rubric_profile(
    dto: RubricProfileCreateDTO,
    current_user: User = Depends(require_roles(["HR", "ADMIN", "INTERVIEWER"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[RubricProfileDTO]:
    service = RubricService(db)
    created = await service.create_rubric_profile(dto=dto, current_user=current_user)
    return ApiResponse(data=created, message="Rubric profile created successfully")


@router.post(
    "/{profile_id}/re-evaluate",
    response_model=ApiResponse[RubricProfileDTO],
)
async def re_evaluate_rubric(
    profile_id: str,
    current_user: User = Depends(require_roles(["HR", "ADMIN", "INTERVIEWER"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[RubricProfileDTO]:
    service = RubricService(db)
    evaluated = await service.re_evaluate_rubric(profile_id=profile_id, current_user=current_user)
    return ApiResponse(data=evaluated, message="Penilaian rubrik berhasil dievaluasi ulang dari transkrip")


@router.delete("/{profile_id}", response_model=ApiResponse[dict[str, str]])
async def delete_rubric_profile(
    profile_id: str,
    current_user: User = Depends(require_roles(["HR", "ADMIN", "INTERVIEWER"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict[str, str]]:
    service = RubricService(db)
    await service.delete_rubric_profile(profile_id=profile_id, current_user=current_user)
    return ApiResponse(data={"id": profile_id}, message="Rubric profile deleted successfully")


@router.post(
    "/{profile_id}/competencies",
    response_model=ApiResponse[CompetencyItemDTO],
    status_code=status.HTTP_201_CREATED,
)
async def add_competency_to_rubric(
    profile_id: str,
    dto: CompetencyCreateDTO,
    current_user: User = Depends(require_roles(["HR", "ADMIN", "INTERVIEWER"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CompetencyItemDTO]:
    service = RubricService(db)
    created = await service.add_competency(
        profile_id=profile_id,
        dto=dto,
        current_user=current_user,
    )
    return ApiResponse(data=created, message="Competency indicator added successfully")


@router.patch(
    "/{profile_id}/competencies/{competency_id}",
    response_model=ApiResponse[CompetencyItemDTO],
)
async def update_competency_in_rubric(
    profile_id: str,
    competency_id: str,
    dto: CompetencyUpdateDTO,
    current_user: User = Depends(require_roles(["HR", "ADMIN", "INTERVIEWER"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CompetencyItemDTO]:
    service = RubricService(db)
    updated = await service.update_competency(
        profile_id=profile_id,
        competency_id=competency_id,
        dto=dto,
        current_user=current_user,
    )
    return ApiResponse(data=updated, message="Competency indicator updated successfully")


@router.delete(
    "/{profile_id}/competencies/{competency_id}",
    response_model=ApiResponse[dict[str, str]],
)
async def delete_competency_from_rubric(
    profile_id: str,
    competency_id: str,
    current_user: User = Depends(require_roles(["HR", "ADMIN", "INTERVIEWER"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict[str, str]]:
    service = RubricService(db)
    await service.delete_competency(
        profile_id=profile_id,
        competency_id=competency_id,
        current_user=current_user,
    )
    return ApiResponse(data={"id": competency_id}, message="Competency indicator deleted successfully")
