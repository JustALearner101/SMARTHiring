from app.dto.BaseDTO import BaseDTO


class NationalHolidayDTO(BaseDTO):
    id: str
    date: str
    name: str
    is_joint_leave: bool = False


class NationalHolidayCreateDTO(BaseDTO):
    date: str
    name: str
    is_joint_leave: bool = False
