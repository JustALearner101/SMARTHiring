from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.AppSecurity import require_roles
from app.db.DatabaseSession import get_db
from app.dto.BaseDTO import ApiResponse
from app.dto.HolidayDTO import NationalHolidayCreateDTO, NationalHolidayDTO
from app.model.UserModel import User
from app.service.HolidayService import HolidayService

router = APIRouter(prefix="/holidays", tags=["NationalHolidays"])


@router.get("", response_model=ApiResponse[list[NationalHolidayDTO]])
async def list_holidays(
    year: int | None = Query(None, description="Filter by year"),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[NationalHolidayDTO]]:
    service = HolidayService(db)
    holidays = await service.list_holidays(year=year)
    return ApiResponse(data=holidays, message="Berhasil mengambil daftar hari libur")


@router.post("", response_model=ApiResponse[NationalHolidayDTO], status_code=status.HTTP_201_CREATED)
async def create_holiday(
    dto: NationalHolidayCreateDTO,
    _current_user: User = Depends(require_roles(["HR", "ADMIN"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[NationalHolidayDTO]:
    service = HolidayService(db)
    created = await service.create_holiday(dto)
    return ApiResponse(data=created, message="Hari libur berhasil ditambahkan")


@router.delete("/{holiday_id}", response_model=ApiResponse[dict[str, str]])
async def delete_holiday(
    holiday_id: str,
    _current_user: User = Depends(require_roles(["HR", "ADMIN"])),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict[str, str]]:
    service = HolidayService(db)
    await service.delete_holiday(holiday_id)
    return ApiResponse(data={"deleted_id": holiday_id}, message="Hari libur berhasil dihapus")
