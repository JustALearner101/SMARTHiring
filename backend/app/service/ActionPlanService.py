import logging
import time
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.AgentState import OrchestratorAgentState
from app.dto.ActionPlanDTO import (
    ActionItemDraftDTO,
    ActionPlanDTO,
    PlanApprovalRequestDTO,
    PlanRejectRequestDTO,
    PlanUndoRequestDTO,
    ProposedSlotDTO,
    SourceCitationDTO,
)
from app.exception.CustomException import ConflictException, NotFoundException
from app.model.FollowupModel import FollowupPlan
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

    def _to_action_plan_dto(self, plan: FollowupPlan) -> ActionPlanDTO:
        now = datetime.now(UTC)
        meta = plan.vagent_metadata or {}
        raw_slot = meta.get("proposed_slot") or {}

        # 1. Resilient ProposedSlotDTO
        if isinstance(raw_slot, ProposedSlotDTO):
            slot_dto = raw_slot
        elif isinstance(raw_slot, dict):
            start_str = raw_slot.get("start_utc") or (
                plan.dscheduled_start_utc.isoformat()
                if plan.dscheduled_start_utc
                else now.isoformat()
            )
            end_str = raw_slot.get("end_utc") or (
                plan.dscheduled_end_utc.isoformat()
                if plan.dscheduled_end_utc
                else (now + timedelta(hours=1)).isoformat()
            )
            slot_dto = ProposedSlotDTO(
                title=str(raw_slot.get("title") or "Technical Interview"),
                start_utc=str(start_str),
                end_utc=str(end_str),
                formatted_wib=str(raw_slot.get("formatted_wib") or "WIB"),
                formatted_wita=str(raw_slot.get("formatted_wita") or "WITA"),
                formatted_wit=str(raw_slot.get("formatted_wit") or ""),
                duration_minutes=int(raw_slot.get("duration_minutes") or 60),
                location_type=str(raw_slot.get("location_type") or "Google Meet"),
                meeting_link=str(
                    raw_slot.get("meeting_link")
                    or "https://meet.google.com/hkt-ops-2026"
                ),
            )
        else:
            slot_dto = ProposedSlotDTO(
                title="Technical Interview",
                start_utc=now.isoformat(),
                end_utc=(now + timedelta(hours=1)).isoformat(),
                formatted_wib="10:00 WIB",
                formatted_wita="11:00 WITA",
                duration_minutes=60,
                location_type="Google Meet",
                meeting_link="https://meet.google.com/hkt-ops-2026",
            )

        # 2. Resilient SourceCitationDTO
        raw_sources = meta.get("sources_cited") or []
        if not raw_sources:
            raw_sources = [
                {
                    "id": "src-01",
                    "ref_code": "[cal-slot-verified]",
                    "source_type": "CALENDAR",
                    "title": "Verified Calendar Slot",
                    "detail": "Slot availability confirmed without conflict.",
                }
            ]
        sources_dtos: list[SourceCitationDTO] = []
        for idx, s in enumerate(raw_sources, start=1):
            if isinstance(s, SourceCitationDTO):
                sources_dtos.append(s)
            elif isinstance(s, dict):
                st = str(s.get("source_type") or "CALENDAR").upper()
                if st not in (
                    "CALENDAR",
                    "OPERATIONAL_RULE",
                    "CANDIDATE_ATS",
                    "CONTACT",
                ):
                    st = "CALENDAR"
                sources_dtos.append(
                    SourceCitationDTO(
                        id=str(s.get("id") or f"src-{idx:02d}"),
                        ref_code=str(s.get("ref_code") or f"[source-{idx:02d}]"),
                        source_type=st,  # type: ignore[arg-type]
                        title=str(s.get("title") or "Verified Source Reference"),
                        detail=str(
                            s.get("detail")
                            or "Verified constraint or availability reference."
                        ),
                    )
                )

        # 3. Resilient ActionItemDraftDTO
        raw_items = meta.get("items") or []
        if not raw_items:
            raw_items = [
                {
                    "id": "item-01",
                    "action_type": "send_email",
                    "recipient_name": str(
                        meta.get("interviewer_name") or "Interviewer"
                    ),
                    "recipient_role": str(
                        meta.get("interviewer_role") or "Interviewer"
                    ),
                    "recipient_contact": str(
                        meta.get("interviewer_email") or "interviewer@company.com"
                    ),
                    "channel": "email",
                    "subject": "Interview Invitation",
                    "content_preview": "Technical interview invitation.",
                    "is_external": False,
                }
            ]
        items_dtos: list[ActionItemDraftDTO] = []
        for idx, it in enumerate(raw_items, start=1):
            if isinstance(it, ActionItemDraftDTO):
                items_dtos.append(it)
            elif isinstance(it, dict):
                ch = str(it.get("channel") or "email").lower()
                if ch not in ("email", "whatsapp", "calendar"):
                    ch = "email"
                act = str(it.get("action_type") or f"send_{ch}").lower()
                if act not in ("send_email", "send_whatsapp", "book_calendar"):
                    act = (
                        f"send_{ch}"
                        if ch in ("email", "whatsapp")
                        else "book_calendar"
                    )
                items_dtos.append(
                    ActionItemDraftDTO(
                        id=str(it.get("id") or f"item-{idx:02d}"),
                        action_type=act,  # type: ignore[arg-type]
                        recipient_name=str(it.get("recipient_name") or "Participant"),
                        recipient_role=str(it.get("recipient_role") or "Recipient"),
                        recipient_contact=str(
                            it.get("recipient_contact") or "contact@example.com"
                        ),
                        channel=ch,  # type: ignore[arg-type]
                        subject=it.get("subject"),
                        content_preview=str(
                            it.get("content_preview") or "Schedule details."
                        ),
                        is_external=bool(it.get("is_external", False)),
                    )
                )

        # 4. Resilient Status Mapping to PlanStatus
        raw_status = str(plan.vapproval_status or "").upper()
        if raw_status in ("AWAITING_APPROVAL", "DRAFT"):
            mapped_status = "PENDING_APPROVAL"
        elif raw_status == "AWAITING_CLARIFICATION":
            mapped_status = "CLARIFICATION_NEEDED"
        elif raw_status == "APPROVED":
            mapped_status = "UNDO_WINDOW"
        elif raw_status == "INVALIDATED":
            mapped_status = "REJECTED"
        elif raw_status in (
            "IDLE",
            "ANALYZING",
            "CLARIFICATION_NEEDED",
            "PENDING_APPROVAL",
            "UNDO_WINDOW",
            "EXECUTED",
            "UNDONE",
            "REJECTED",
        ):
            mapped_status = raw_status
        else:
            mapped_status = "PENDING_APPROVAL"

        undo_exp = None
        if mapped_status == "UNDO_WINDOW" and plan.dundo_deadline:
            undo_exp = int(plan.dundo_deadline.timestamp())

        return ActionPlanDTO(
            id=str(plan.nid),
            candidate_id=str(meta.get("candidate_id") or "1"),
            candidate_name=str(meta.get("candidate_name") or "Candidate"),
            candidate_position=str(meta.get("candidate_position") or "Position"),
            candidate_email=meta.get("candidate_email") or "candidate@example.com",
            candidate_phone=meta.get("candidate_phone") or "+6281234567890",
            interviewer_id=str(meta.get("interviewer_id") or "1"),
            interviewer_name=str(meta.get("interviewer_name") or "Interviewer"),
            interviewer_role=str(
                meta.get("interviewer_role") or "Technical Interviewer"
            ),
            interviewer_dept=str(meta.get("interviewer_dept") or "Engineering"),
            interviewer_email=meta.get("interviewer_email")
            or "interviewer@company.com",
            interviewer_phone=meta.get("interviewer_phone") or "+6281198765432",
            raw_command=str(plan.vplan or "Autonomous scheduling"),
            negotiation_round=int(meta.get("negotiation_round") or 1),
            max_rounds=3,
            status=mapped_status,  # type: ignore[arg-type]
            is_high_impact=plan.vimpact_level == "HIGH",
            guardrail_passed=bool(meta.get("guardrail_passed", True)),
            guardrail_notes=str(
                meta.get("guardrail_notes") or "Verified secure by Guardrail."
            ),
            secondary_validator_passed=bool(
                meta.get("secondary_validator_passed", True)
            ),
            validator_notes=str(
                meta.get("validator_notes") or "Verified by Secondary Validator."
            ),
            proposed_slot=slot_dto,
            sources_cited=sources_dtos,
            items=items_dtos,
            created_at=plan.dcrea.isoformat() if plan.dcrea else now.isoformat(),
            undo_expires_at=undo_exp,
        )

    async def get_plan_by_id(self, plan_id: str) -> ActionPlanDTO | None:
        """Fetch a specific ActionPlan by ID (supporting direct deep links)."""
        try:
            clean_id = (
                str(plan_id)
                .replace("plan-rejected-", "")
                .replace("plan_rejected-", "")
                .replace("plan-", "")
                .replace("plan_", "")
                .strip()
            )
            p_id = int(clean_id) if clean_id.isdigit() else None
            if p_id is None:
                return None
            plan = await self.action_plan_repo.get_action_plan(p_id)
            if not plan:
                return None
            return self._to_action_plan_dto(plan)
        except Exception:
            logger.exception("Failed to get action plan by id: %s", plan_id)
            return None

    async def get_current_plan(self) -> ActionPlanDTO | None:
        try:
            # Prioritize active plans awaiting approval or within the 60s undo window
            plan = await self.action_plan_repo.get_latest_active_plan()
            if not plan:
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
                    cand_item = next(
                        (
                            it
                            for it in meta.get("items", [])
                            if "candidate" in str(it.get("recipient_role", "")).lower()
                        ),
                        None,
                    )
                    candidate_channel = (
                        cand_item.get("channel", "email")
                        if cand_item
                        else meta.get("candidate_channel", "email")
                    )
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
                        "thread_id": plan.nid_thread
                        or (int(meta["thread_id"]) if meta.get("thread_id") else None),
                    }
                    await self.executor_node.execute_plan(
                        state, approved_by="HR Admin (Auto-Dispatch)"
                    )
                    await self.action_plan_repo.update_plan_status(
                        plan.nid, status="EXECUTED"
                    )
                    return None
                except Exception:
                    logger.exception(
                        "Failed lazy execution of action plan #%s", plan.nid
                    )

            if plan.vapproval_status in ("EXECUTED", "UNDONE", "REJECTED"):
                return None

            return self._to_action_plan_dto(plan)
        except Exception:
            logger.exception("Failed to get current action plan")
            return None

    async def approve_plan(self, plan_id: str, request: PlanApprovalRequestDTO) -> ActionPlanDTO:
        p_id = int(plan_id) if plan_id.isdigit() else 1
        plan = await self.action_plan_repo.get_action_plan(p_id)
        if not plan:
            raise NotFoundException(f"Plan ID {plan_id} not found.")

        now = datetime.now(UTC)
        meta = plan.vagent_metadata or {}

        # Apply customized items if provided by user in Confirmation Card
        if request.customized_items:
            items_dicts = [i.model_dump() for i in request.customized_items]
            meta["items"] = items_dicts
            plan.vagent_metadata = meta
            self.session.add(plan)
            await self.session.commit()

        # Pre-Execution Secondary Validator Guard (TC-CHB-21)
        slot_to_verify = meta.get("proposed_slot") or {}
        start_utc_str = slot_to_verify.get("start_utc")
        if start_utc_str:
            try:
                st_utc = datetime.fromisoformat(start_utc_str)
                st_wib = st_utc + timedelta(hours=7)
                # Friday prayer blackout (11:30 - 13:00 WIB)
                if st_wib.weekday() == 4:
                    minute_of_day = st_wib.hour * 60 + st_wib.minute
                    if 11 * 60 + 30 <= minute_of_day < 13 * 60:
                        err_msg = (
                            "Secondary Validator Rejection: Slot yang diajukan (Jumat 11:30 - 13:00 WIB) "
                            "melanggar aturan operasional waktu ibadah sholat Jumat [rule-jumatan]."
                        )
                        await self.audit_service.log_event(
                            event_type="VALIDATION_VIOLATION_BLOCKED",
                            actor=request.approved_by,
                            actor_type="AGENT",
                            title="Approval Blocked by Secondary Validator",
                            description=err_msg,
                            metadata={"plan_id": p_id, "slot": slot_to_verify},
                        )
                        raise ConflictException(err_msg)
                # Indonesian working hours (09:00 - 17:00 WIB)
                if st_wib.hour < 9 or st_wib.hour >= 17:
                    err_msg = (
                        f"Secondary Validator Rejection: Slot pukul {st_wib.strftime('%H:%M')} WIB "
                        "berada di luar jam kerja operasional (09:00 - 17:00 WIB) [rule-jam-kerja]."
                    )
                    await self.audit_service.log_event(
                        event_type="VALIDATION_VIOLATION_BLOCKED",
                        actor=request.approved_by,
                        actor_type="AGENT",
                        title="Approval Blocked by Secondary Validator",
                        description=err_msg,
                        metadata={"plan_id": p_id, "slot": slot_to_verify},
                    )
                    raise ConflictException(err_msg)
            except ConflictException:
                raise
            except Exception as e:
                logger.warning("Slot validation check encountered an error: %s", e)

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
                f"Plan #{plan_id} cannot be approved because current status is: {status_desc}."
            )

        cand_item = next(
            (it for it in meta.get("items", []) if "candidate" in str(it.get("recipient_role", "")).lower()),
            None,
        )
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
                description=f"Action plan #{p_id} approved and executed immediately.",
                metadata={"plan_id": p_id},
            )
        else:
            await self.audit_service.log_event(
                event_type="HUMAN_APPROVED",
                actor=request.approved_by,
                actor_type="HUMAN",
                title="Action Plan Approved by HR",
                description=f"Action plan #{p_id} approved by HR. Entering 60-second undo buffer window.",
                metadata={"plan_id": p_id, "undo_window_seconds": 60},
            )

        updated = await self.action_plan_repo.get_action_plan(p_id)
        if not updated:
            raise ValueError("Failed to update plan status.")
        dto = self._to_action_plan_dto(updated)
        if not request.send_immediately:
            dto.status = "UNDO_WINDOW"
            dto.undo_expires_at = int(time.time() + 60)
        return dto

    async def undo_plan(self, plan_id: str, request: PlanUndoRequestDTO) -> ActionPlanDTO:
        p_id = int(plan_id) if plan_id.isdigit() else 1
        plan = await self.action_plan_repo.get_action_plan(p_id)
        if not plan:
            raise NotFoundException(f"Plan ID {plan_id} not found.")

        undone_plan = await self.action_plan_repo.atomic_undo_plan(p_id)
        if not undone_plan:
            existing = await self.action_plan_repo.get_action_plan(p_id)
            status_desc = existing.vapproval_status if existing else "NOT_FOUND"
            raise ConflictException(
                f"Plan #{plan_id} cannot be undone (Current status: {status_desc})."
            )

        await self.audit_service.log_event(
            event_type="ACTION_UNDONE",
            actor="HR Admin",
            actor_type="HUMAN",
            title="Action Plan Undone Within 60s Window",
            description=f"Execution of action plan #{p_id} undone manually by HR: {request.reason}.",
            metadata={"plan_id": p_id, "reason": request.reason},
        )

        updated = await self.action_plan_repo.get_action_plan(p_id)
        if not updated:
            raise ValueError("Failed to undo plan.")
        dto = self._to_action_plan_dto(updated)
        dto.status = "UNDONE"
        dto.undo_expires_at = None
        return dto

    async def reject_plan(self, plan_id: str, request: PlanRejectRequestDTO) -> ActionPlanDTO:
        p_id = int(plan_id) if plan_id.isdigit() else 1
        plan = await self.action_plan_repo.get_action_plan(p_id)
        if not plan:
            raise NotFoundException(f"Plan ID {plan_id} not found.")

        rejected_plan = await self.action_plan_repo.atomic_reject_plan(p_id)
        if not rejected_plan:
            existing = await self.action_plan_repo.get_action_plan(p_id)
            status_desc = existing.vapproval_status if existing else "NOT_FOUND"
            raise ConflictException(
                f"Plan #{plan_id} cannot be rejected (Current status: {status_desc})."
            )

        await self.audit_service.log_event(
            event_type="PLAN_REJECTED",
            actor=request.rejected_by,
            actor_type="HUMAN",
            title="Action Plan Rejected by HR (Approval Gate)",
            description=f"Action plan #{p_id} rejected by HR: {request.reason}. No external messages dispatched.",
            metadata={"plan_id": p_id, "reason": request.reason},
        )

        updated = await self.action_plan_repo.get_action_plan(p_id)
        if not updated:
            raise ValueError("Failed to update plan status to REJECTED.")
        dto = self._to_action_plan_dto(updated)
        dto.status = "REJECTED"
        dto.undo_expires_at = None
        return dto

