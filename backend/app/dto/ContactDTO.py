from typing import Literal

from pydantic import Field

from app.dto.BaseDTO import BaseDTO

Timezone = Literal["WIB", "WITA", "WIT"]
SystemRole = Literal["HR", "ADMIN", "INTERVIEWER"]
Department = str


class InterviewerContactDTO(BaseDTO):
    id: str
    employee_id: str
    name: str
    username: str
    system_role: SystemRole = "INTERVIEWER"
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
    username: str | None = Field(default=None, min_length=3, max_length=100)
    password: str | None = Field(default=None, min_length=6, max_length=128)
    system_role: SystemRole = "INTERVIEWER"
    email: str
    phone: str
    department: Department
    role: str
    timezone: Timezone = "WIB"
    working_hours: str = "09:00 - 17:00"


class InterviewerUpdateDTO(BaseDTO):
    name: str | None = None
    username: str | None = Field(default=None, min_length=3, max_length=100)
    password: str | None = Field(default=None, min_length=6, max_length=128)
    system_role: SystemRole | None = None
    email: str | None = None
    phone: str | None = None
    department: Department | None = None
    role: str | None = None
    timezone: Timezone | None = None
    working_hours: str | None = None
