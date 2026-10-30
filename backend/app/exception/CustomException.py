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

    def __init__(self, message: str = "Data not found", data: Any = None) -> None:
        super().__init__(message=message, status_code=404, data=data)


class ForbiddenException(AppException):
    """HTTP 403 Forbidden."""

    def __init__(self, message: str = "Access denied", data: Any = None) -> None:
        super().__init__(message=message, status_code=403, data=data)


class UnauthorizedException(AppException):
    """HTTP 401 Unauthorized."""

    def __init__(self, message: str = "Authentication required", data: Any = None) -> None:
        super().__init__(message=message, status_code=401, data=data)


class ConflictException(AppException):
    """HTTP 409 Conflict."""

    def __init__(self, message: str = "Data conflict occurred", data: Any = None) -> None:
        super().__init__(message=message, status_code=409, data=data)


class BadRequestException(AppException):
    """HTTP 400 Bad Request."""

    def __init__(self, message: str = "Invalid request", data: Any = None) -> None:
        super().__init__(message=message, status_code=400, data=data)


class BusinessRuleException(AppException):
    """HTTP 422 Business Rule / Operational Policy Violation."""

    def __init__(self, message: str = "Business operational rule violation", data: Any = None) -> None:
        super().__init__(message=message, status_code=422, data=data)


class RateLimitException(AppException):
    """HTTP 429 Too Many Requests."""

    def __init__(self, message: str = "Too many requests. Please try again later.", data: Any = None) -> None:
        super().__init__(message=message, status_code=429, data=data)


class PayloadTooLargeException(AppException):
    """HTTP 413 Payload Too Large."""

    def __init__(self, message: str = "Payload size exceeds permitted limit", data: Any = None) -> None:
        super().__init__(message=message, status_code=413, data=data)


class UnsupportedMediaTypeException(AppException):
    """HTTP 415 Unsupported Media Type."""

    def __init__(self, message: str = "Unsupported media type or file format", data: Any = None) -> None:
        super().__init__(message=message, status_code=415, data=data)
