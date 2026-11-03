from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dto.NotificationDTO import NotificationDTO
from app.model.AuditModel import AuditLog
from app.model.FollowupModel import FollowupPlan
from app.model.InterviewModel import Interview, SourceFile
from app.model.JobModel import Job
from app.model.OrchestrationModel import NegotiationThread
from app.model.SummaryModel import HrDecision
from app.model.UserModel import User


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_notifications(self, current_user: User) -> list[NotificationDTO]:
        notifications: list[NotificationDTO] = []
        user_role = current_user.vrole
        user_name = current_user.vname

        if user_role in ("HR", "ADMIN"):
            plan_stmt = (
                select(FollowupPlan)
                .where(FollowupPlan.vapproval_status == "AWAITING_APPROVAL")
                .order_by(FollowupPlan.nid.desc())
                .limit(5)
            )
            pending_plans = (await self.session.execute(plan_stmt)).scalars().all()
            for plan in pending_plans:
                meta: dict[str, Any] = plan.vagent_metadata or {}
                cand_name = meta.get("candidate_name", "Candidate")
                position = meta.get("candidate_position", "New Position")
                notifications.append(
                    NotificationDTO(
                        id=f"plan-{plan.nid}",
                        category="APPROVAL",
                        title="Action Plan Awaiting Approval",
                        message=f"AI Orchestrator drafted a schedule for {cand_name} ({position}). Requires your full review.",
                        timestamp=plan.dcrea.isoformat(),
                        link=f"/orchestration/scheduling?planId={plan.nid}",
                        badge_variant="warning",
                        metadata={"plan_id": plan.nid, "candidate_name": cand_name},
                    )
                )

            # Surface recently rejected/canceled action plans for HR accountability
            rejected_stmt = (
                select(FollowupPlan)
                .where(FollowupPlan.vapproval_status == "REJECTED")
                .order_by(FollowupPlan.dmodi.desc().nullslast(), FollowupPlan.nid.desc())
                .limit(5)
            )
            rejected_plans = (await self.session.execute(rejected_stmt)).scalars().all()
            for r_plan in rejected_plans:
                meta_r: dict[str, Any] = r_plan.vagent_metadata or {}
                cand_name = meta_r.get("candidate_name", "Candidate")
                position = meta_r.get("candidate_position", "Position")
                notifications.append(
                    NotificationDTO(
                        id=f"plan-rejected-{r_plan.nid}",
                        category="APPROVAL",
                        title="Action Plan Rejected",
                        message=f"Interview scheduling for {cand_name} ({position}) was rejected/canceled. No external actions taken.",
                        timestamp=(r_plan.dmodi or r_plan.dcrea).isoformat(),
                        link=f"/orchestration/scheduling?planId={r_plan.nid}",
                        badge_variant="error",
                        metadata={"plan_id": r_plan.nid, "candidate_name": cand_name, "status": "REJECTED"},
                    )
                )

            thread_stmt = (
                select(NegotiationThread)
                .where(NegotiationThread.vstatus.in_(["DEADLOCK_ESCALATED", "NEGOTIATING"]))
                .order_by(NegotiationThread.nid.desc())
                .limit(5)
            )
            threads = (await self.session.execute(thread_stmt)).scalars().all()
            for th in threads:
                if th.vstatus == "DEADLOCK_ESCALATED" or th.ncurrent_round >= 3:
                    notifications.append(
                        NotificationDTO(
                            id=f"thread-{th.nid}",
                            category="TRIAGE",
                            title="Candidate Reschedule Deadlock",
                            message=f"Schedule negotiation on Thread #{th.nid} reached round {th.ncurrent_round}. Requires HR assistance.",
                            timestamp=(th.dlast_activity_at or th.dcrea).isoformat(),
                            link="/simulator/whatsapp",
                            badge_variant="error",
                            metadata={"thread_id": th.nid},
                        )
                    )

            pending_subq = (
                select(HrDecision.nid)
                .join(Job, HrDecision.nid_job == Job.nid)
                .join(SourceFile, Job.nid_source == SourceFile.nid)
                .where(
                    SourceFile.nid_interview == Interview.nid,
                    HrDecision.vworkflow_status == "PENDING_HR_FOLLOWUP",
                )
            )
            finalized_subq = (
                select(HrDecision.nid)
                .join(Job, HrDecision.nid_job == Job.nid)
                .join(SourceFile, Job.nid_source == SourceFile.nid)
                .where(
                    SourceFile.nid_interview == Interview.nid,
                    HrDecision.vworkflow_status == "FINALIZED",
                )
            )
            followup_iv_stmt = (
                select(Interview)
                .options(
                    selectinload(Interview.candidate),
                    selectinload(Interview.interviewer),
                )
                .where(pending_subq.exists(), ~finalized_subq.exists())
                .order_by(Interview.nid.desc())
                .limit(5)
            )
            pending_interviews = (await self.session.execute(followup_iv_stmt)).scalars().all()
            for iv in pending_interviews:
                cand_name = iv.candidate.vname if iv.candidate else "Candidate"
                intv_name = iv.interviewer.vname if iv.interviewer else "Interviewer"
                notifications.append(
                    NotificationDTO(
                        id=f"interview-followup-{iv.nid}",
                        category="APPROVAL",
                        title="Pending HR Follow-Up Decision",
                        message=(
                            f"Interviewer {intv_name} submitted evaluation results for {cand_name}. "
                            "Awaiting HR final followup."
                        ),
                        timestamp=(iv.dmodi or iv.dcrea).isoformat(),
                        link=f"/interviews/review?id={iv.nid}",
                        badge_variant="warning",
                        metadata={"interview_id": iv.nid, "candidate_name": cand_name},
                    )
                )

        if user_role == "ADMIN":
            audit_stmt = (
                select(AuditLog)
                .where(AuditLog.vevent_type.ilike("%INJECTION%") | AuditLog.vevent_type.ilike("%BLOCKED%"))
                .order_by(AuditLog.nid.desc())
                .limit(5)
            )
            security_logs = (await self.session.execute(audit_stmt)).scalars().all()
            for log in security_logs:
                notifications.append(
                    NotificationDTO(
                        id=f"sec-{log.nid}",
                        category="SECURITY",
                        title="AI Guardrail & Security Alert",
                        message=f"Anomaly attempt/blocked access detected: {log.vmasked_detail[:90]}...",
                        timestamp=log.dcrea.isoformat(),
                        link="/audit/guardrail",
                        badge_variant="error",
                        metadata={"audit_id": log.nid, "hash": log.vhash},
                    )
                )

        if user_role == "INTERVIEWER":
            notifications.append(
                NotificationDTO(
                    id=f"interviewer-slot-{current_user.nid}",
                    category="INTERVIEW",
                    title="Your Interview Schedule & Evaluation",
                    message=f"Hello {user_name}, check your calendar schedule and interview evaluation sessions assigned to you.",
                    timestamp=datetime.now(UTC).isoformat(),
                    link="/interviews/sessions",
                    badge_variant="info",
                )
            )

        notifications.sort(key=lambda x: x.timestamp, reverse=True)
        return notifications
