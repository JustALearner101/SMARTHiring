from datetime import UTC, datetime, timedelta
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dto.DashboardDTO import (
    ActiveNegotiationDTO,
    ActivityFeedDTO,
    DashboardSummaryDTO,
    MetricCardDTO,
    PendingApprovalDTO,
    PipelineStageDTO,
    RecentAuditDTO,
    TrendPointDTO,
    UpcomingInterviewDTO,
)
from app.model.AuditModel import AuditLog
from app.model.CandidateModel import Candidate
from app.model.FollowupModel import FollowupPlan
from app.model.OrchestrationModel import CalendarEvent, NegotiationThread

# ── Pipeline status display definition ──────────────────────────────────────
PIPELINE_STAGES = [
    ("SCREENING", "Screening", "#3B82F6"),
    ("ESCALATED", "Escalated", "#F59E0B"),
    ("INTERVIEW_SCHEDULED", "Interview Scheduled", "#8B5CF6"),
    ("PENDING_HR_REVIEW", "HR Review", "#EC4899"),
    ("TECHNICAL_TEST", "Technical Test", "#14B8A6"),
    ("COMPLETED", "Completed", "#10B981"),
    ("OFFERED", "Offered", "#06B6D4"),
    ("REJECTED", "Rejected", "#EF4444"),
]


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Endpoint 1: Summary ─────────────────────────────────────────────────

    async def get_summary(self) -> DashboardSummaryDTO:
        now = datetime.now(UTC)
        week_start = now - timedelta(days=now.weekday())
        week_end = week_start + timedelta(days=7)
        prev_week_start = week_start - timedelta(days=7)

        # 1. Total active candidates
        total_candidates = await self._count_active_candidates()
        prev_candidates = await self._count_active_candidates(before=week_start)

        # 2. Interviews this week
        interviews_this_week = await self._count_interviews(week_start, week_end)
        interviews_prev_week = await self._count_interviews(prev_week_start, week_start)

        # 3. Pending approvals
        pending_approvals = await self._count_pending_approvals()

        # 4. Open negotiations
        open_negotiations = await self._count_open_negotiations()

        metrics = [
            MetricCardDTO(
                key="active_candidates",
                label="Total Active Candidates",
                value=total_candidates,
                change_percent=self._calc_change(total_candidates, prev_candidates),
                trend="up" if total_candidates >= prev_candidates else "down",
            ),
            MetricCardDTO(
                key="interviews_this_week",
                label="This Week's Interview",
                value=interviews_this_week,
                change_percent=self._calc_change(interviews_this_week, interviews_prev_week),
                trend="up" if interviews_this_week >= interviews_prev_week else "down",
            ),
            MetricCardDTO(
                key="pending_approvals",
                label="Waiting Approvals",
                value=pending_approvals,
                trend="neutral",
            ),
            MetricCardDTO(
                key="active_negotiations",
                label="Active Negotiations",
                value=open_negotiations,
                trend="neutral",
            ),
        ]

        # Pipeline breakdown
        pipeline = await self._get_pipeline_breakdown()

        # Weekly trend (last 8 weeks)
        weekly_trend = await self._get_weekly_trend(weeks=8)

        return DashboardSummaryDTO(
            metrics=metrics,
            pipeline=pipeline,
            weekly_trend=weekly_trend,
        )

    # ── Endpoint 2: Upcoming Interviews ─────────────────────────────────────

    async def get_upcoming_interviews(self, limit: int = 5) -> list[UpcomingInterviewDTO]:
        now = datetime.now(UTC)
        week_ahead = now + timedelta(days=7)

        stmt = (
            select(CalendarEvent)
            .options(selectinload(CalendarEvent.user))
            .where(
                CalendarEvent.dscheduled_start_utc >= now,
                CalendarEvent.dscheduled_start_utc <= week_ahead,
                CalendarEvent.vevent_type == "SCHEDULED_INTERVIEW",
            )
            .order_by(CalendarEvent.dscheduled_start_utc.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        events = result.scalars().all()

        interviews: list[UpcomingInterviewDTO] = []
        for ev in events:
            cand_name = ev.vcandidate_name or "Candidate"
            inter_name = ev.user.vname if ev.user else "Interviewer"
            inter_dept = ev.user.vdepartment if ev.user else "Engineering"
            scheduled_at = ev.dscheduled_start_utc.isoformat() if ev.dscheduled_start_utc else ""
            formatted = self._format_wib(ev.dscheduled_start_utc)

            interviews.append(
                UpcomingInterviewDTO(
                    id=str(ev.nid),
                    candidate_name=cand_name,
                    candidate_code=f"CAN-{ev.nid:04d}",
                    position=ev.vtitle,
                    interviewer_name=inter_name,
                    interviewer_dept=inter_dept or "Engineering",
                    scheduled_at=scheduled_at,
                    formatted_time=formatted,
                    location_type="Google Meet",
                    event_type=ev.vevent_type or "SCHEDULED_INTERVIEW",
                    status="SCHEDULED",
                )
            )

        return interviews

    # ── Endpoint 3: Activity Feed ───────────────────────────────────────────

    async def get_activity_feed(self, include_audit: bool = True) -> ActivityFeedDTO:
        pending = await self._get_pending_approvals(limit=5)
        negotiations = await self._get_active_negotiations(limit=5)
        audit = await self._get_recent_audit(limit=10) if include_audit else []

        return ActivityFeedDTO(
            pending_approvals=pending,
            active_negotiations=negotiations,
            recent_audit=audit,
        )

    # ── Internal Helpers ────────────────────────────────────────────────────

    async def _count_active_candidates(self, before: datetime | None = None) -> int:
        stmt = select(func.count()).select_from(Candidate)
        excluded = ("REJECTED", "COMPLETED")
        stmt = stmt.where(Candidate.vstatus.notin_(excluded))
        if before:
            stmt = stmt.where(Candidate.dcrea < before)
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def _count_interviews(self, start: datetime, end: datetime) -> int:
        stmt = (
            select(func.count())
            .select_from(CalendarEvent)
            .where(
                CalendarEvent.vevent_type == "SCHEDULED_INTERVIEW",
                CalendarEvent.dscheduled_start_utc >= start,
                CalendarEvent.dscheduled_start_utc < end,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def _count_pending_approvals(self) -> int:
        stmt = (
            select(func.count())
            .select_from(FollowupPlan)
            .where(FollowupPlan.vapproval_status == "AWAITING_APPROVAL")
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def _count_open_negotiations(self) -> int:
        stmt = (
            select(func.count())
            .select_from(NegotiationThread)
            .where(NegotiationThread.vstatus.in_(("NEGOTIATING", "DEADLOCK_ESCALATED")))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def _get_pipeline_breakdown(self) -> list[PipelineStageDTO]:
        stmt = select(Candidate.vstatus, func.count().label("cnt")).group_by(Candidate.vstatus)
        result = await self.session.execute(stmt)
        rows = {r[0]: r[1] for r in result.all()}

        return [
            PipelineStageDTO(
                status=status,
                label=label,
                count=rows.get(status, 0),
                color=color,
            )
            for status, label, color in PIPELINE_STAGES
        ]

    async def _get_weekly_trend(self, weeks: int = 8) -> list[TrendPointDTO]:
        now = datetime.now(UTC)
        points: list[TrendPointDTO] = []

        for i in range(weeks - 1, -1, -1):
            week_start = now - timedelta(weeks=i + 1)
            week_end = now - timedelta(weeks=i)
            stmt = (
                select(func.count())
                .select_from(Candidate)
                .where(
                    Candidate.dcrea >= week_start,
                    Candidate.dcrea < week_end,
                )
            )
            result = await self.session.execute(stmt)
            count = result.scalar_one() or 0
            label = week_start.strftime("%b W") + str((week_start.day - 1) // 7 + 1)
            points.append(TrendPointDTO(week_label=label, count=count))

        return points

    async def _get_pending_approvals(self, limit: int = 5) -> list[PendingApprovalDTO]:
        stmt = (
            select(FollowupPlan)
            .where(FollowupPlan.vapproval_status.in_(("AWAITING_APPROVAL", "DRAFT")))
            .order_by(FollowupPlan.dcrea.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        plans = result.scalars().all()

        items: list[PendingApprovalDTO] = []
        for p in plans:
            meta = p.vagent_metadata or {}
            cand_name = meta.get("candidate_name", "Candidate")
            cand_pos = meta.get("candidate_position", p.vplan[:40] if p.vplan else "Interview")
            items_count = len(meta.get("items", [])) or 1
            proposed_slot = self._format_wib(p.dscheduled_start_utc)

            items.append(
                PendingApprovalDTO(
                    id=str(p.nid),
                    candidate_name=cand_name,
                    position=cand_pos,
                    proposed_slot=proposed_slot,
                    items_count=items_count,
                    created_at=p.dcrea.isoformat() if p.dcrea else "",
                    is_high_impact=p.vimpact_level == "HIGH",
                )
            )
        return items

    async def _get_active_negotiations(self, limit: int = 5) -> list[ActiveNegotiationDTO]:
        stmt = (
            select(NegotiationThread)
            .options(
                selectinload(NegotiationThread.candidate),
                selectinload(NegotiationThread.interviewer),
                selectinload(NegotiationThread.messages),
            )
            .where(NegotiationThread.vstatus.in_(("NEGOTIATING", "DEADLOCK_ESCALATED")))
            .order_by(NegotiationThread.dcrea.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        threads = result.scalars().all()

        items: list[ActiveNegotiationDTO] = []
        for t in threads:
            cand_name = t.candidate.vname if t.candidate else "Candidate"
            cand_pos = t.candidate.vjob_position if t.candidate else "General Role"
            cand_channel: Literal["whatsapp", "email"] = (
                t.candidate.vpreferred_channel if t.candidate and t.candidate.vpreferred_channel in ("whatsapp", "email") else "whatsapp"
            )
            last_preview = t.messages[-1].vcontent if t.messages else "No messages yet."
            last_activity = (
                t.dlast_activity_at.isoformat()
                if t.dlast_activity_at
                else (t.dmodi.isoformat() if t.dmodi else (t.dcrea.isoformat() if t.dcrea else ""))
            )

            items.append(
                ActiveNegotiationDTO(
                    id=str(t.nid),
                    candidate_name=cand_name,
                    position=cand_pos,
                    channel=cand_channel,
                    current_round=t.ncurrent_round,
                    max_rounds=t.nmax_rounds,
                    last_message_preview=last_preview[:80] + ("..." if len(last_preview) > 80 else ""),
                    last_activity_at=last_activity,
                    status=t.vstatus,
                )
            )
        return items

    async def _get_recent_audit(self, limit: int = 10) -> list[RecentAuditDTO]:
        stmt = select(AuditLog).order_by(AuditLog.dcrea.desc()).limit(limit)
        result = await self.session.execute(stmt)
        logs = result.scalars().all()

        items: list[RecentAuditDTO] = []
        for log in logs:
            badge: Literal["success", "warning", "error", "info"] = "info"
            ev_type = log.vevent_type or ""
            if "INJECTION" in ev_type or "BLOCKED" in ev_type or "REJECT" in ev_type or "FAIL" in ev_type:
                badge = "error"
            elif "CLARIFICATION" in ev_type or "ESCALATED" in ev_type or "PENDING" in ev_type:
                badge = "warning"
            elif "APPROVED" in ev_type or "SUCCESS" in ev_type or "EXECUTED" in ev_type or "SCHEDULED" in ev_type:
                badge = "success"

            items.append(
                RecentAuditDTO(
                    id=str(log.nid),
                    timestamp=log.dcrea.isoformat() if log.dcrea else "",
                    event_type=ev_type,
                    title=log.vmasked_detail or ev_type,
                    actor=log.vactor_id or "System",
                    badge_variant=badge,
                )
            )
        return items

    @staticmethod
    def _calc_change(current: int, previous: int) -> float:
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 1)

    @staticmethod
    def _format_wib(dt: datetime | None) -> str:
        if not dt:
            return "—"
        wib = dt + timedelta(hours=7)
        days_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        months_en = [
            "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]
        day_name = days_en[wib.weekday()]
        return f"{day_name}, {wib.day} {months_en[wib.month]} {wib.year} · {wib.strftime('%H:%M')} WIB"

