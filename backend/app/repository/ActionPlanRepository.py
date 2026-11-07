from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.model.FollowupModel import ActionRecipient, FollowupPlan
from app.repository.BaseRepository import BaseRepository


class ActionPlanRepository(BaseRepository[FollowupPlan]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(FollowupPlan, session)

    async def get_action_plan(self, plan_id: int) -> FollowupPlan | None:
        stmt = (
            select(FollowupPlan)
            .options(
                selectinload(FollowupPlan.recipients).selectinload(ActionRecipient.candidate),
                selectinload(FollowupPlan.recipients).selectinload(ActionRecipient.user),
            )
            .where(FollowupPlan.nid == plan_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_plan(self) -> FollowupPlan | None:
        stmt = (
            select(FollowupPlan)
            .options(
                selectinload(FollowupPlan.recipients).selectinload(ActionRecipient.candidate),
                selectinload(FollowupPlan.recipients).selectinload(ActionRecipient.user),
            )
            .order_by(FollowupPlan.nid.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_active_plan(self) -> FollowupPlan | None:
        """Get latest plan currently awaiting approval or in undo window."""
        stmt = (
            select(FollowupPlan)
            .options(
                selectinload(FollowupPlan.recipients).selectinload(ActionRecipient.candidate),
                selectinload(FollowupPlan.recipients).selectinload(ActionRecipient.user),
            )
            .where(FollowupPlan.vapproval_status.in_(["AWAITING_APPROVAL", "APPROVED"]))
            .order_by(FollowupPlan.nid.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_action_plan(
        self,
        plan_data: dict,
        recipients_data: list[dict] | None = None,
    ) -> FollowupPlan:
        plan = FollowupPlan(**plan_data)
        self.session.add(plan)
        await self.session.flush()

        if recipients_data:
            for r_data in recipients_data:
                recipient = ActionRecipient(nid_followup_plan=plan.nid, **r_data)
                self.session.add(recipient)

        await self.session.commit()
        return await self.get_action_plan(plan.nid) or plan

    async def atomic_approve_plan(
        self,
        plan_id: int,
        approved_by_id: int | None = None,
        undo_deadline: datetime | None = None,
        immediate: bool = False,
    ) -> FollowupPlan | None:
        """Atomically approve an ActionPlan.

        If immediate is False:
            Transitions from 'AWAITING_APPROVAL' -> 'APPROVED' (with undo_deadline set).
        If immediate is True:
            Transitions from 'AWAITING_APPROVAL' or 'APPROVED' -> 'EXECUTED' (clearing undo_deadline).

        Returns None if already executed, undone, or not found.
        Prevents race condition on concurrent approval requests.
        """
        target_status = "EXECUTED" if immediate else "APPROVED"
        allowed_statuses = ["AWAITING_APPROVAL", "APPROVED"] if immediate else ["AWAITING_APPROVAL"]
        stmt = (
            update(FollowupPlan)
            .where(
                FollowupPlan.nid == plan_id,
                FollowupPlan.vapproval_status.in_(allowed_statuses),
            )
            .values(
                vapproval_status=target_status,
                nid_approved_by=approved_by_id or 1,
                dundo_deadline=undo_deadline if not immediate else None,
                dmodi=func.now(),
            )
            .returning(FollowupPlan)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def atomic_undo_plan(self, plan_id: int) -> FollowupPlan | None:
        """Atomically undo an ActionPlan if and only if it is currently APPROVED (within undo window)."""
        stmt = (
            update(FollowupPlan)
            .where(
                FollowupPlan.nid == plan_id,
                FollowupPlan.vapproval_status == "APPROVED",
            )
            .values(
                vapproval_status="UNDONE",
                dmodi=func.now(),
            )
            .returning(FollowupPlan)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def atomic_reject_plan(self, plan_id: int) -> FollowupPlan | None:
        """Atomically reject an ActionPlan if and only if it is currently AWAITING_APPROVAL."""
        stmt = (
            update(FollowupPlan)
            .where(
                FollowupPlan.nid == plan_id,
                FollowupPlan.vapproval_status == "AWAITING_APPROVAL",
            )
            .values(
                vapproval_status="REJECTED",
                dmodi=func.now(),
            )
            .returning(FollowupPlan)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one_or_none()


    async def update_plan_status(
        self,
        plan_id: int,
        status: str,
        approved_by_id: int | None = None,
    ) -> FollowupPlan | None:
        plan = await self.get_by_id(plan_id)
        if not plan:
            return None
        plan.vapproval_status = status
        if status == "EXECUTED" and not plan.vapproval_token:
            plan.vapproval_token = f"tok_appr_{plan_id}"
        if approved_by_id:
            plan.nid_approved_by = approved_by_id
        self.session.add(plan)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan
