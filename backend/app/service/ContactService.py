from collections.abc import Sequence

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.AppSecurity import get_password_hash
from app.dto.ContactDTO import (
    InterviewerContactDTO,
    InterviewerCreateDTO,
    InterviewerUpdateDTO,
)
from app.exception.CustomException import (
    BusinessRuleException,
    ConflictException,
    NotFoundException,
)
from app.model.UserModel import User
from app.repository.ContactRepository import ContactRepository
from app.service.AuditLogService import AuditLogService


class ContactService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.contact_repo = ContactRepository(session)
        self.audit_service = AuditLogService(session)

    @staticmethod
    def _to_interviewer_dto(user: User) -> InterviewerContactDTO:
        words = user.vname.split()
        initials = "".join([w[0].upper() for w in words[:2]]) if words else "U"
        sys_role = user.vrole if user.vrole in ("HR", "ADMIN", "INTERVIEWER") else "INTERVIEWER"
        return InterviewerContactDTO(
            id=str(user.nid),
            employee_id=user.vuserid,
            name=user.vname,
            username=user.vusername,
            system_role=sys_role,  # type: ignore[arg-type]
            email=user.vemail,
            phone=user.vphone_number or "+6281200000000",
            department=user.vdepartment or "Engineering",
            role=user.vposition or user.vrole,
            timezone=user.vtimezone,  # type: ignore[arg-type]
            working_hours=user.vworking_hours or "09:00 - 17:00",
            avatar_initials=initials,
        )

    async def list_interviewers(self, department: str | None = None) -> list[InterviewerContactDTO]:
        interviewers = await self.contact_repo.list_interviewers(department=department)
        return [self._to_interviewer_dto(u) for u in interviewers]

    async def create_interviewer(self, dto: InterviewerCreateDTO) -> InterviewerContactDTO:
        resolved_username = (dto.username or dto.email.split("@")[0]).strip()
        resolved_password = dto.password or "password123"
        resolved_email = dto.email.strip()
        resolved_emp_id = dto.employee_id.strip()

        dup_stmt = select(User).where(
            or_(
                User.vusername == resolved_username,
                User.vemail == resolved_email,
                User.vuserid == resolved_emp_id,
            )
        )
        existing = (await self.session.execute(dup_stmt)).scalars().first()
        if existing:
            raise ConflictException(
                "Employee ID, Username, atau Email sudah digunakan oleh akun lain di sistem."
            )

        user_data = {
            "vuserid": resolved_emp_id,
            "vname": dto.name.strip(),
            "vusername": resolved_username,
            "vemail": resolved_email,
            "vpassword_hash": get_password_hash(resolved_password),
            "vphone_number": dto.phone,
            "vdepartment": dto.department,
            "vposition": dto.role,
            "vrole": dto.system_role,
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
        updates: dict[str, str] = {}
        if dto.name is not None:
            updates["vname"] = dto.name.strip()
        if dto.username is not None and dto.username.strip() != user.vusername:
            new_uname = dto.username.strip()
            dup = (
                await self.session.execute(
                    select(User).where(User.vusername == new_uname, User.nid != user.nid)
                )
            ).scalars().first()
            if dup:
                raise ConflictException(f"Username '{new_uname}' sudah digunakan.")
            updates["vusername"] = new_uname
        if dto.password:
            updates["vpassword_hash"] = get_password_hash(dto.password)
        if dto.system_role is not None:
            updates["vrole"] = dto.system_role
        if dto.email is not None and dto.email.strip() != user.vemail:
            new_email = dto.email.strip()
            dup_email = (
                await self.session.execute(
                    select(User).where(User.vemail == new_email, User.nid != user.nid)
                )
            ).scalars().first()
            if dup_email:
                raise ConflictException(f"Email '{new_email}' sudah digunakan.")
            updates["vemail"] = new_email
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

    async def delete_interviewer(self, user_id: str, current_user: User) -> None:
        user = await self.contact_repo.get_by_id(user_id)
        if not user or user.vstatus != "ACTIVE":
            raise NotFoundException("Kontak pengguna tidak ditemukan")
        if user.nid == current_user.nid:
            raise BusinessRuleException("Anda tidak dapat menonaktifkan/menghapus akun Anda sendiri yang sedang login.")

        await self.contact_repo.update(user, {"vstatus": "INACTIVE"})
        await self.audit_service.log_event(
            event_type="USER_DEACTIVATED",
            actor=current_user.vname,
            actor_type="HUMAN",
            title=f"User Account Deactivated ({user.vusername})",
            description=f"Akun {user.vname} ({user.vrole}) dinonaktifkan dari direktori aktif dengan tetap menjaga integritas riwayat audit.",
            metadata={"deactivated_user_id": user.nid, "username": user.vusername},
        )

    async def find_ambiguous_names(self, first_name: str) -> Sequence[User]:
        return await self.contact_repo.find_ambiguous_names(first_name)
