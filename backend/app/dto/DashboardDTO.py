from typing import Literal
from pydantic import Field

from app.dto.BaseDTO import BaseDTO


# ── Section 1: Summary Metrics & Charts ────────────────────────────────────

class MetricCardDTO(BaseDTO):
    """Satu kartu KPI di dashboard."""
    key: str
    label: str
    value: int
    change_percent: float = 0.0
    trend: Literal["up", "down", "neutral"] = "neutral"


class PipelineStageDTO(BaseDTO):
    """Satu stage di hiring pipeline funnel."""
    status: str
    label: str
    count: int
    color: str


class TrendPointDTO(BaseDTO):
    """Satu titik data di trend chart mingguan."""
    week_label: str
    count: int


class DashboardSummaryDTO(BaseDTO):
    """Response untuk GET /dashboard/summary."""
    metrics: list[MetricCardDTO] = Field(default_factory=list)
    pipeline: list[PipelineStageDTO] = Field(default_factory=list)
    weekly_trend: list[TrendPointDTO] = Field(default_factory=list)


# ── Section 2: Upcoming Interviews ──────────────────────────────────────────

class UpcomingInterviewDTO(BaseDTO):
    """Satu interview yang akan datang."""
    id: str
    candidate_name: str
    candidate_code: str
    position: str
    interviewer_name: str
    interviewer_dept: str
    scheduled_at: str
    formatted_time: str
    location_type: str
    event_type: str
    status: str


# ── Section 3: Activity Feed ────────────────────────────────────────────────

class PendingApprovalDTO(BaseDTO):
    """Action plan menunggu approval."""
    id: str
    candidate_name: str
    position: str
    proposed_slot: str
    items_count: int
    created_at: str
    is_high_impact: bool = False


class ActiveNegotiationDTO(BaseDTO):
    """Negotiation thread yang masih aktif."""
    id: str
    candidate_name: str
    position: str
    channel: Literal["whatsapp", "email"]
    current_round: int
    max_rounds: int
    last_message_preview: str
    last_activity_at: str
    status: str


class RecentAuditDTO(BaseDTO):
    """Event audit log terbaru."""
    id: str
    timestamp: str
    event_type: str
    title: str
    actor: str
    badge_variant: Literal["success", "warning", "error", "info"]


class ActivityFeedDTO(BaseDTO):
    """Response untuk GET /dashboard/activityFeed."""
    pending_approvals: list[PendingApprovalDTO] = Field(default_factory=list)
    active_negotiations: list[ActiveNegotiationDTO] = Field(default_factory=list)
    recent_audit: list[RecentAuditDTO] = Field(default_factory=list)

