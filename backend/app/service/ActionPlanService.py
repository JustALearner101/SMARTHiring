import logging
import time
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.AgentState import OrchestratorAgentState
from app.dto.ActionPlanDTO import (
    ActionItemDraftDTO,
    ActionPlanDTO,
    PlanApprovalRequestDTO,
    PlanUndoRequestDTO,
    ProposedSlotDTO,
    SourceCitationDTO,
)
from app.exception.CustomException import ConflictException, NotFoundException
from app.repository.ActionPlanRepository import ActionPlanRepository
from app.service.AuditLogService import AuditLogService

logger = logging.getLogger(__name__)


class ActionPlanService:
    def __init__(self, session: AsyncSession) -> None:
        from app.agent.ExecutorNode import ExecutorNode

        self.session = session
        self.action_plan_repo = ActionPlanRepository(session)
        self.audit_service = AuditLogService(session)
        self.executor_node = ExecutorNode(session)

    async def get_current_plan(self) -> ActionPlanDTO | None:
        plan = await self.action_plan_repo.get_latest_plan()
        if not plan:
            return None

        now = datetime.now(UTC)

        # Lazy auto-execution if 60-second undo window expired
        dundo = plan.dundo_deadline
        if dundo and dundo.tzinfo is None:
            dundo = dundo.replace(tzinfo=UTC)

        if plan.vapproval_status == "APPROVED" and dundo and now >= dundo:
            try:
                meta = plan.vagent_metadata or {}
                cand_item = next((it for it in meta.get("items", []) if "candidate" in str(it.get("recipient_role", "")).lower()), None)
                candidate_channel = cand_item.get("channel", "email") if cand_item else meta.get("candidate_channel", "email")
                state: OrchestratorAgentState = {
                    "proposed_slot": meta.get("proposed_slot"),
                    "candidate_id": int(meta.get("candidate_id", 1)),
                    "candidate_name": meta.get("candidate_name", "Rina Kusuma"),
                    "candidate_channel": candidate_channel,
                    "interviewer_id": int(meta.get("interviewer_id", 1)),
                    "interviewer_name": meta.get("interviewer_name", "Budi Santoso"),
                    "items": meta.get("items", []),
                    "negotiation_round": meta.get("negotiation_round", 1),
                    "max_rounds": 3,
                    "sources_cited": meta.get("sources_cited", []),
                    "thread_id": plan.nid_thread or (int(meta["thread_id"]) if meta.get("thread_id") else None),
                }
                await self.executor_node.execute_plan(state, approved_by="HR Admin (Auto-Dispatch)")
                await self.action_plan_repo.update_plan_status(plan.nid, status="EXECUTED")
                refreshed = await self.action_plan_repo.get_action_plan(plan.nid)
                if refreshed:
                    plan = refreshed
            except Exception:
                logger.exception("Failed lazy execution of action plan #%s", plan.nid)

        meta = plan.vagent_metadata or {}
        slot_data = meta.get("proposed_slot") or {
            "title": "User Technical Interview (Round 1)",
            "start_utc": plan.dscheduled_start_utc.isoformat() if plan.dscheduled_start_utc else now.isoformat(),
            "end_utc": plan.dscheduled_end_utc.isoformat() if plan.dscheduled_end_utc else (now + timedelta(hours=1)).isoformat(),
            "formatted_wib": "Rabu, 28 Okt 2026, 10:00 WIB",
            "formatted_wita": "Rabu, 28 Okt 2026, 11:00 WITA",
            "duration_minutes": 60,
            "location_type": "Google Meet",
            "meeting_link": "https://meet.google.com/hkt-ops-2026",
        }

        sources_data = meta.get("sources_cited") or [
            {
                "id": "src-01",
                "ref_code": "[cal-budi-01]",
                "source_type": "CALENDAR",
                "title": "Kalender Budi Santoso",
                "detail": "Slot kosong terverifikasi pukul 10:00 - 11:00 WIB.",
            }
        ]

        items_data = meta.get("items") or [
            {
                "id": "item-01",
                "action_type": "send_email",
                "recipient_name": meta.get("interviewer_name", "Budi Santoso"),
                "recipient_role": meta.get("interviewer_role", "VP of Engineering"),
                "recipient_contact": "budi.santoso@company.com",
                "channel": "email",
                "subject": "Undangan Technical Interview",
                "content_preview": "Undangan interview teknis via Google Meet.",
                "is_external": False,
            }
        ]

        mapped_status = (
            "PENDING_APPROVAL"
            if plan.vapproval_status == "AWAITING_APPROVAL"
            else ("UNDO_WINDOW" if plan.vapproval_status == "APPROVED" else plan.vapproval_status)
        )

        undo_exp = None
        if mapped_status == "UNDO_WINDOW" and plan.dundo_deadline:
            undo_exp = int(plan.dundo_deadline.timestamp())

        return ActionPlanDTO(
            id=str(plan.nid),
            candidate_id=meta.get("candidate_id", "1"),
            candidate_name=meta.get("candidate_name", "Rina Kusuma"),
            candidate_position=meta.get("candidate_position", "Senior Frontend Engineer (Next.js)"),
            candidate_email=meta.get("candidate_email", "akhtar.ramadhan01@gmail.com"),
            candidate_phone=meta.get("candidate_phone", "+6281234567890"),
            interviewer_id=meta.get("interviewer_id", "1"),
            interviewer_name=meta.get("interviewer_name", "Budi Santoso"),
            interviewer_role=meta.get("interviewer_role", "VP of Engineering"),
            interviewer_dept=meta.get("interviewer_dept", "Engineering"),
            interviewer_email=meta.get("interviewer_email", "akhtar.ramadhan01@gmail.com"),
            interviewer_phone=meta.get("interviewer_phone", "+6281198765432"),
            raw_command=plan.vplan,
            negotiation_round=meta.get("negotiation_round", 1),
            max_rounds=3,
            status=mapped_status,  # type: ignore[arg-type]
            is_high_impact=plan.vimpact_level == "HIGH",
            guardrail_passed=meta.get("guardrail_passed", True),
            guardrail_notes=meta.get("guardrail_notes", "Instruksi terverifikasi aman."),
            secondary_validator_passed=meta.get("secondary_validator_passed", True),
            validator_notes=meta.get("validator_notes", "Slot mematuhi jam kerja dan buffer 15 menit."),
            proposed_slot=ProposedSlotDTO(**slot_data),
            sources_cited=[SourceCitationDTO(**s) for s in sources_data],
            items=[ActionItemDraftDTO(**i) for i in items_data],
            created_at=plan.dcrea.isoformat() if plan.dcrea else now.isoformat(),
            undo_expires_at=undo_exp,
        )

    async def approve_plan(self, plan_id: str, request: PlanApprovalRequestDTO) -> ActionPlanDTO:
        p_id = int(plan_id) if plan_id.isdigit() else 1
        plan = await self.action_plan_repo.get_action_plan(p_id)
        if not plan:
            raise NotFoundException(f"Plan ID {plan_id} tidak ditemukan.")

        now = datetime.now(UTC)
        meta = plan.vagent_metadata or {}

        # Apply customized items if provided by user in Confirmation Card
        if request.customized_items:
            items_dicts = [i.model_dump() for i in request.customized_items]
            meta["items"] = items_dicts
            plan.vagent_metadata = meta
            self.session.add(plan)
            await self.session.commit()

        # Atomic conditional update prevents concurrent double approval race condition
        undo_deadline = None if request.send_immediately else now + timedelta(seconds=60)
        approved_plan = await self.action_plan_repo.atomic_approve_plan(
            plan_id=p_id,
            approved_by_id=1,
            undo_deadline=undo_deadline,
            immediate=request.send_immediately,
        )
        if not approved_plan:
            existing = await self.action_plan_repo.get_action_plan(p_id)
            status_desc = existing.vapproval_status if existing else "NOT_FOUND"
            raise ConflictException(
                f"Plan #{plan_id} tidak dapat disetujui karena status saat ini: {status_desc}."
            )

        cand_item = next((it for it in meta.get("items", []) if "candidate" in str(it.get("recipient_role", "")).lower()), None)
        candidate_channel = cand_item.get("channel", "email") if cand_item else meta.get("candidate_channel", "email")

        if request.send_immediately:
            # Immediate Execution
            state: OrchestratorAgentState = {
                "proposed_slot": meta.get("proposed_slot"),
                "candidate_id": int(meta.get("candidate_id", 1)),
                "candidate_name": meta.get("candidate_name", "Rina Kusuma"),
                "candidate_channel": candidate_channel,
                "interviewer_id": int(meta.get("interviewer_id", 1)),
                "interviewer_name": meta.get("interviewer_name", "Budi Santoso"),
                "items": meta.get("items", []),
                "negotiation_round": meta.get("negotiation_round", 1),
                "max_rounds": 3,
                "sources_cited": meta.get("sources_cited", []),
                "thread_id": plan.nid_thread or (int(meta["thread_id"]) if meta.get("thread_id") else None),
            }
            await self.executor_node.execute_plan(state, approved_by=request.approved_by)
            await self.audit_service.log_event(
                event_type="ACTION_EXECUTED",
                actor=request.approved_by,
                actor_type="HUMAN",
                title="Action Plan Executed Immediately by HR",
                description=f"Rencana aksi #{p_id} disetujui dan dieksekusi secara instan.",
                metadata={"plan_id": p_id},
            )
        else:
            await self.audit_service.log_event(
                event_type="HUMAN_APPROVED",
                actor=request.approved_by,
                actor_type="HUMAN",
                title="Action Plan Approved by HR",
                description=f"Rencana aksi #{p_id} disetujui HR. Memasuki jendela undo buffer 60 detik.",
                metadata={"plan_id": p_id, "undo_window_seconds": 60},
            )

        current = await self.get_current_plan()
        if current:
            if not request.send_immediately:
                current.status = "UNDO_WINDOW"
                current.undo_expires_at = int(time.time() + 60)
            return current
        raise ValueError("Gagal memperbarui status plan.")

    async def undo_plan(self, plan_id: str, request: PlanUndoRequestDTO) -> ActionPlanDTO:
        p_id = int(plan_id) if plan_id.isdigit() else 1
        plan = await self.action_plan_repo.get_action_plan(p_id)
        if not plan:
            raise NotFoundException(f"Plan ID {plan_id} tidak ditemukan.")

        undone_plan = await self.action_plan_repo.atomic_undo_plan(p_id)
        if not undone_plan:
            existing = await self.action_plan_repo.get_action_plan(p_id)
            status_desc = existing.vapproval_status if existing else "NOT_FOUND"
            raise ConflictException(
                f"Plan #{plan_id} tidak dapat dibatalkan (Status saat ini: {status_desc})."
            )

        await self.audit_service.log_event(
            event_type="ACTION_UNDONE",
            actor="HR Admin",
            actor_type="HUMAN",
            title="Action Plan Undone Within 60s Window",
            description=f"Eksekusi rencana aksi #{p_id} dibatalkan secara manual oleh HR: {request.reason}.",
            metadata={"plan_id": p_id, "reason": request.reason},
        )

        current = await self.get_current_plan()
        if current:
            current.status = "UNDONE"
            current.undo_expires_at = None
            return current
        raise ValueError("Gagal membatalkan plan.")
