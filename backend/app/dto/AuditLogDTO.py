from typing import Any, Literal

from app.dto.BaseDTO import BaseDTO


class AuditEventDTO(BaseDTO):
    id: str
    timestamp: str
    event_type: str
    title: str
    description: str
    actor: str
    status_badge: Literal["success", "warning", "error", "info"]
    metadata: dict[str, Any] | None = None
