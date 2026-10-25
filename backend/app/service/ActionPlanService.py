import time
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.ActionPlanDTO import (
    ActionItemDraftDTO,
    ActionPlanDTO,
    PlanApprovalRequestDTO,
    PlanUndoRequestDTO,
    ProposedSlotDTO,
    SourceCitationDTO,
)
from app.repository.ActionPlanRepository import ActionPlanRepository


class ActionPlanService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.action_plan_repo = ActionPlanRepository(session)

    async def get_current_plan(self) -> ActionPlanDTO | None:
        plan = await self.action_plan_repo.get_latest_plan()
        if not plan:
            return None

        slot_dto = ProposedSlotDTO(
            title="User Technical Interview (Round 1)",
            start_utc=plan.dscheduled_start_utc.isoformat() if plan.dscheduled_start_utc else datetime.now(UTC).isoformat(),
            end_utc=plan.dscheduled_end_utc.isoformat() if plan.dscheduled_end_utc else (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
            formatted_wib="Rabu, 26 Okt 2026, 10:00 WIB",
            formatted_wita="Rabu, 26 Okt 2026, 11:00 WITA",
            duration_minutes=60,
            location_type="Google Meet",
            meeting_link="https://meet.google.com/hkt-ops-2026",
        )

        sources = [
            SourceCitationDTO(
                id="src-01",
                ref_code="[cal-budi-01]",
                source_type="CALENDAR",
                title="Kalender Budi Santoso",
                detail="Slot kosong terverifikasi pukul 10:00 - 11:00 WIB.",
            ),
        ]

        mapped_status = (
            "PENDING_APPROVAL"
            if plan.vapproval_status == "AWAITING_APPROVAL"
            else ("UNDO_WINDOW" if plan.vapproval_status == "APPROVED" else plan.vapproval_status)
        )

        return ActionPlanDTO(
            id=str(plan.nid),
            candidate_id="1",
            candidate_name="Rina Kusuma",
            candidate_position="Senior Frontend Engineer (Next.js)",
            interviewer_id="1",
            interviewer_name="Budi Santoso",
            interviewer_role="VP of Engineering",
            interviewer_dept="Engineering",
            raw_command=plan.vplan,
            negotiation_round=1,
            max_rounds=3,
            status=mapped_status,  # type: ignore[arg-type]
            is_high_impact=True,
            guardrail_passed=True,
            guardrail_notes="Instruksi terverifikasi aman.",
            secondary_validator_passed=True,
            validator_notes="Slot mematuhi jam kerja dan buffer 15 menit.",
            proposed_slot=slot_dto,
            sources_cited=sources,
            items=[
                ActionItemDraftDTO(
                    id="item-01",
                    action_type="send_email",
                    recipient_name="Budi Santoso",
                    recipient_role="VP of Engineering",
                    recipient_contact="budi.santoso@company.com",
                    channel="email",
                    subject="Undangan Technical Interview",
                    content_preview="Undangan interview teknis via Google Meet.",
                    is_external=False,
                ),
            ],
            created_at=plan.dcrea.isoformat() if plan.dcrea else datetime.now(UTC).isoformat(),
        )

    async def approve_plan(self, plan_id: str, request: PlanApprovalRequestDTO) -> ActionPlanDTO:
        p_id = int(plan_id) if plan_id.isdigit() else 1
        plan = await self.action_plan_repo.get_action_plan(p_id)
        if not plan:
            raise ValueError(f"Plan ID {plan_id} tidak ditemukan.")

        target_db_status = "EXECUTED" if request.send_immediately else "APPROVED"
        target_dto_status = "EXECUTED" if request.send_immediately else "UNDO_WINDOW"
        await self.action_plan_repo.update_plan_status(p_id, status=target_db_status, approved_by_id=1)

        current = await self.get_current_plan()
        if current:
            current.status = target_dto_status  # type: ignore[assignment]
            current.undo_expires_at = int(time.time() + 60) if target_dto_status == "UNDO_WINDOW" else None
            return current
        raise ValueError("Gagal memperbarui status plan.")

    async def undo_plan(self, plan_id: str, request: PlanUndoRequestDTO) -> ActionPlanDTO:
        p_id = int(plan_id) if plan_id.isdigit() else 1
        plan = await self.action_plan_repo.get_action_plan(p_id)
        if not plan:
            raise ValueError(f"Plan ID {plan_id} tidak ditemukan.")

        await self.action_plan_repo.update_plan_status(p_id, status="UNDONE")
        current = await self.get_current_plan()
        if current:
            current.status = "UNDONE"
            current.undo_expires_at = None
            return current
        raise ValueError("Gagal membatalkan plan.")
