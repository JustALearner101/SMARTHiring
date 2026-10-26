from typing import Any


class AppException(Exception):
    """Base application exception for standardized error envelopes."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        data: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.data = data


class NotFoundException(AppException):
    """HTTP 404 Not Found."""

    def __init__(self, message: str = "Data tidak ditemukan", data: Any = None) -> None:
        super().__init__(message=message, status_code=404, data=data)


class ForbiddenException(AppException):
    """HTTP 403 Forbidden."""

    def __init__(self, message: str = "Akses ditolak", data: Any = None) -> None:
        super().__init__(message=message, status_code=403, data=data)


class UnauthorizedException(AppException):
    """HTTP 401 Unauthorized."""

    def __init__(self, message: str = "Autentikasi diperlukan", data: Any = None) -> None:
        super().__init__(message=message, status_code=401, data=data)


class ConflictException(AppException):
    """HTTP 409 Conflict."""

    def __init__(self, message: str = "Terjadi konflik data", data: Any = None) -> None:
        super().__init__(message=message, status_code=409, data=data)


class BadRequestException(AppException):
    """HTTP 400 Bad Request."""

    def __init__(self, message: str = "Permintaan tidak valid", data: Any = None) -> None:
        super().__init__(message=message, status_code=400, data=data)


class BusinessRuleException(AppException):
    """HTTP 422 Business Rule / Operational Policy Violation."""

    def __init__(self, message: str = "Melanggar aturan operasional bisnis", data: Any = None) -> None:
        super().__init__(message=message, status_code=422, data=data)
