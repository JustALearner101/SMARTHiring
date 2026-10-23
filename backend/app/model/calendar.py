from datetime import date, time

from sqlalchemy import CheckConstraint, Date, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.model.base import TableBaseModel


class WorkCalendar(TableBaseModel):
    """Office work calendar, working hours, and Friday prayer blackout blocks (tblm_work_calendar)."""

    __tablename__ = "tblm_work_calendar"
    __table_args__ = (
        CheckConstraint(
            "vtimezone IN ('WIB', 'WITA', 'WIT')",
            name="ck_tblm_work_calendar_vtimezone",
        ),
    )

    voffice_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    vtimezone: Mapped[str] = mapped_column(String(10), nullable=False, default="WIB")
    twork_start: Mapped[time] = mapped_column(Time, nullable=False, default=time(8, 0))
    twork_end: Mapped[time] = mapped_column(Time, nullable=False, default=time(17, 0))
    tfriday_prayer_start: Mapped[time] = mapped_column(Time, nullable=False, default=time(11, 30))
    tfriday_prayer_end: Mapped[time] = mapped_column(Time, nullable=False, default=time(13, 0))


class Holiday(TableBaseModel):
    """National holidays and collective leaves (tblm_holiday)."""

    __tablename__ = "tblm_holiday"
    __table_args__ = (
        CheckConstraint(
            "vtype IN ('NATIONAL_HOLIDAY', 'COLLECTIVE_LEAVE')",
            name="ck_tblm_holiday_vtype",
        ),
    )

    dholiday_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False, index=True)
    vname: Mapped[str] = mapped_column(String(255), nullable=False)
    vtype: Mapped[str] = mapped_column(String(50), nullable=False, default="NATIONAL_HOLIDAY")
