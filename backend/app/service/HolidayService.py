from datetime import date as dt_date

from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.HolidayDTO import NationalHolidayCreateDTO, NationalHolidayDTO
from app.exception.CustomException import NotFoundException
from app.model.CalendarModel import Holiday
from app.repository.HolidayRepository import HolidayRepository


class HolidayService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.holiday_repo = HolidayRepository(session)

    async def list_holidays(self, year: int | None = None) -> list[NationalHolidayDTO]:
        holidays = await self.holiday_repo.list_holidays(year=year)
        return [
            NationalHolidayDTO(
                id=str(h.nid),
                date=h.dholiday_date.strftime("%Y-%m-%d"),
                name=h.vname,
                is_joint_leave=(h.vtype == "COLLECTIVE_LEAVE"),
            )
            for h in holidays
        ]

    async def create_holiday(self, dto: NationalHolidayCreateDTO) -> NationalHolidayDTO:
        d_obj = dt_date.fromisoformat(dto.date)
        h_data = {
            "dholiday_date": d_obj,
            "vname": dto.name,
            "vtype": "COLLECTIVE_LEAVE" if dto.is_joint_leave else "NATIONAL_HOLIDAY",
        }
        holiday = Holiday(**h_data)
        self.session.add(holiday)
        await self.session.commit()
        await self.session.refresh(holiday)
        return NationalHolidayDTO(
            id=str(holiday.nid),
            date=holiday.dholiday_date.strftime("%Y-%m-%d"),
            name=holiday.vname,
            is_joint_leave=(holiday.vtype == "COLLECTIVE_LEAVE"),
        )

    async def delete_holiday(self, holiday_id: str) -> None:
        holiday = await self.holiday_repo.get_by_id(holiday_id)
        if not holiday:
            raise NotFoundException("Hari libur tidak ditemukan")
        await self.holiday_repo.delete(holiday)

    async def is_holiday(self, target_date: dt_date) -> Holiday | None:
        return await self.holiday_repo.is_holiday(target_date)
