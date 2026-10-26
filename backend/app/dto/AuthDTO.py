from pydantic import Field

from app.dto.BaseDTO import BaseDTO


class LoginRequestDTO(BaseDTO):
    """Payload for user authentication."""

    username: str = Field(..., description="Username sistem (misal: hr.admin, budi.santoso, auditor.it)")
    password: str = Field(..., description="Password akun pengguna")


class UserDTO(BaseDTO):
    """Public profile for system users."""

    id: str
    employee_id: str
    name: str
    username: str
    email: str
    role: str
    department: str | None = None
    position: str | None = None
    timezone: str = "WIB"
    working_hours: str | None = "09:00 - 17:00"
    status: str = "ACTIVE"


class LoginResponseDTO(BaseDTO):
    """Successful authentication response with JWT access token."""

    access_token: str
    token_type: str = "bearer"
    user: UserDTO
