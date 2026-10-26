from typing import Literal

from app.dto.BaseDTO import BaseDTO

Timezone = Literal["WIB", "WITA", "WIT"]
Department = str


class InterviewerContactDTO(BaseDTO):
    id: str
    employee_id: str
    name: str
    email: str
    phone: str
    department: Department
    role: str
    timezone: Timezone
    working_hours: str
    avatar_initials: str


class InterviewerCreateDTO(BaseDTO):
    employee_id: str
    name: str
    email: str
    phone: str
    department: Department
    role: str
    timezone: Timezone = "WIB"
    working_hours: str = "09:00 - 17:00"


class InterviewerUpdateDTO(BaseDTO):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    department: Department | None = None
    role: str | None = None
    timezone: Timezone | None = None
    working_hours: str | None = None
