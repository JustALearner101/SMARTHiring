from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.NotificationDTO import NotificationDTO
from app.model.AuditModel import AuditLog
from app.model.FollowupModel import FollowupPlan
from app.model.OrchestrationModel import NegotiationThread
from app.model.UserModel import User


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_notifications(self, current_user: User) -> list[NotificationDTO]:
        notifications: list[NotificationDTO] = []
        user_role = current_user.vrole
        user_name = current_user.vname

        if user_role == "HR":
            plan_stmt = (
                select(FollowupPlan)
                .where(FollowupPlan.vapproval_status == "AWAITING_APPROVAL")
                .order_by(FollowupPlan.nid.desc())
                .limit(5)
            )
            pending_plans = (await self.session.execute(plan_stmt)).scalars().all()
            for plan in pending_plans:
                meta: dict[str, Any] = plan.vagent_metadata or {}
                cand_name = meta.get("candidate_name", "Kandidat")
                position = meta.get("candidate_position", "Posisi Baru")
                notifications.append(
                    NotificationDTO(
                        id=f"plan-{plan.nid}",
                        category="APPROVAL",
                        title="Action Plan Awaiting Approval",
                        message=f"AI Orchestrator menyusun draf jadwal untuk {cand_name} ({position}). Perlu review lengkap Anda.",
                        timestamp=plan.dcrea.isoformat(),
                        link="/orchestration/scheduling",
                        badge_variant="warning",
                        metadata={"plan_id": plan.nid, "candidate_name": cand_name},
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
                            message=f"Negosiasi jadwal pada Thread #{th.nid} mencapai ronde ke-{th.ncurrent_round}. Butuh bantuan HR.",
                            timestamp=(th.dlast_activity_at or th.dcrea).isoformat(),
                            link="/simulator/whatsapp",
                            badge_variant="error",
                            metadata={"thread_id": th.nid},
                        )
                    )

        if user_role in ("HR", "AUDITOR"):
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
                        title="AI Guardrail Alert",
                        message=f"Percobaan anomali/prompt injection terdeteksi: {log.vmasked_detail[:90]}...",
                        timestamp=log.dcrea.isoformat(),
                        link="/audit/guardrail",
                        badge_variant="error",
                        metadata={"audit_id": log.nid, "hash": log.vhash},
                    )
                )
                
        if user_role in ("USER_INTERVIEWER", "TECH_INTERVIEWER"):
            notifications.append(
                NotificationDTO(
                    id=f"interviewer-slot-{current_user.nid}",
                    category="INTERVIEW",
                    title="Jadwal Sesi Wawancara Anda",
                    message=f"Halo {user_name}, periksa jadwal ketersediaan kalender Anda untuk sesi interview pekan ini.",
                    timestamp=datetime.now(UTC).isoformat(),
                    link="/orchestration/calendar",
                    badge_variant="info",
                )
            )

        notifications.sort(key=lambda x: x.timestamp, reverse=True)
        return notifications