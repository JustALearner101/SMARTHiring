from typing import Any

from app.dto.BaseDTO import BaseDTO


class NotificationDTO(BaseDTO):
    id: str
    category: str
    title: str
    message: str
    timestamp: str
    link: str
    badge_variant: str = "info"
    metadata: dict[str, Any] | None = None
