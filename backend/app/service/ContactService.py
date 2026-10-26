from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.ContactDTO import (
    InterviewerContactDTO,
    InterviewerCreateDTO,
    InterviewerUpdateDTO,
)
from app.model.UserModel import User
from app.repository.ContactRepository import ContactRepository


class ContactService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.contact_repo = ContactRepository(session)

    @staticmethod
    def _to_interviewer_dto(user: User) -> InterviewerContactDTO:
        words = user.vname.split()
        initials = "".join([w[0].upper() for w in words[:2]]) if words else "U"
        return InterviewerContactDTO(
            id=str(user.nid),
            employee_id=user.vuserid,
            name=user.vname,
            email=user.vemail,
            phone=user.vphone_number or "+6281200000000",
            department=user.vdepartment or "Engineering",  # type: ignore[arg-type]
            role=user.vposition or user.vrole,
            timezone=user.vtimezone,  # type: ignore[arg-type]
            working_hours=user.vworking_hours or "09:00 - 17:00",
            avatar_initials=initials,
        )

    async def list_interviewers(self, department: str | None = None) -> list[InterviewerContactDTO]:
        interviewers = await self.contact_repo.list_interviewers(department=department)
        return [self._to_interviewer_dto(u) for u in interviewers]

    async def create_interviewer(self, dto: InterviewerCreateDTO) -> InterviewerContactDTO:
        user_data = {
            "vuserid": dto.employee_id,
            "vname": dto.name,
            "vusername": dto.email.split("@")[0],
            "vemail": dto.email,
            "vpassword_hash": "placeholder_argon2_hash",
            "vphone_number": dto.phone,
            "vdepartment": dto.department,
            "vposition": dto.role,
            "vrole": "USER_INTERVIEWER",
            "vtimezone": dto.timezone,
            "vworking_hours": dto.working_hours,
            "vstatus": "ACTIVE",
        }
        user = await self.contact_repo.create(user_data)
        return self._to_interviewer_dto(user)

    async def update_interviewer(self, user_id: str, dto: InterviewerUpdateDTO) -> InterviewerContactDTO | None:
        user = await self.contact_repo.get_by_id(user_id)
        if not user:
            return None
        updates = {}
        if dto.name is not None:
            updates["vname"] = dto.name
        if dto.email is not None:
            updates["vemail"] = dto.email
        if dto.phone is not None:
            updates["vphone_number"] = dto.phone
        if dto.department is not None:
            updates["vdepartment"] = dto.department
        if dto.role is not None:
            updates["vposition"] = dto.role
        if dto.timezone is not None:
            updates["vtimezone"] = dto.timezone
        if dto.working_hours is not None:
            updates["vworking_hours"] = dto.working_hours

        updated = await self.contact_repo.update(user, updates)
        return self._to_interviewer_dto(updated)

    async def find_ambiguous_names(self, first_name: str) -> Sequence[User]:
        return await self.contact_repo.find_ambiguous_names(first_name)
