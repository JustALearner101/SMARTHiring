from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.BaseDTO import PaginatedResponse, PaginationParams
from app.dto.NegotiationThreadDTO import (
    NegotiationThreadDTO,
    ThreadMessageDTO,
)
from app.model.OrchestrationModel import NegotiationThread
from app.repository.NegotiationThreadRepository import NegotiationThreadRepository
from app.service.AuditLogService import AuditLogService


class NegotiationThreadService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.negotiation_repo = NegotiationThreadRepository(session)
        self.audit_service = AuditLogService(session)

    @staticmethod
    def _to_thread_dto(t: NegotiationThread) -> NegotiationThreadDTO:
        cand_name = t.candidate.vname if t.candidate else "Kandidat"
        cand_channel = t.candidate.vpreferred_channel if t.candidate else "whatsapp"
        cand_pos = t.candidate.vjob_position if t.candidate else "General Role"
        cand_phone = t.candidate.vphone_number if t.candidate else None
        cand_email = t.candidate.vemail if t.candidate else None

        inter_name = t.interviewer.vname if t.interviewer else "Interviewer"
        inter_role = t.interviewer.vposition or t.interviewer.vrole if t.interviewer else "Interviewer"
        inter_dept = t.interviewer.vdepartment if t.interviewer else "Engineering"
        inter_tz = t.interviewer.vtimezone if t.interviewer else "WIB"

        messages_dto = [
            ThreadMessageDTO(
                id=str(m.nid),
                round_number=m.nround_number,
                sender_role=m.vsender_role,  # type: ignore[arg-type]
                sender_name=m.vsender_name,
                channel=m.vchannel,  # type: ignore[arg-type]
                sent_at=m.dcrea.isoformat(),
                content=m.vcontent,
                proposed_slot=m.vproposed_slot,
                source_citation=m.vsource_citation,
                is_rejection=m.bis_rejection,
            )
            for m in t.messages
        ]

        last_preview = t.messages[-1].vcontent if t.messages else "Belum ada pesan."
        last_activity = t.dmodi.isoformat() if t.dmodi else t.dcrea.isoformat()

        return NegotiationThreadDTO(
            id=str(t.nid),
            candidate_id=str(t.nid_candidate),
            candidate_name=cand_name,
            candidate_channel=cand_channel,  # type: ignore[arg-type]
            candidate_position=cand_pos,
            candidate_phone=cand_phone,
            candidate_email=cand_email,
            interviewer_id=str(t.nid_interviewer),
            interviewer_name=inter_name,
            interviewer_role=inter_role,
            interviewer_dept=inter_dept,
            interviewer_timezone=inter_tz,  # type: ignore[arg-type]
            current_round=t.ncurrent_round,
            max_rounds=t.nmax_rounds,
            status=t.vstatus,  # type: ignore[arg-type]
            last_activity_at=last_activity,
            last_message_preview=last_preview,
            deadline_at=t.ddeadline_at.isoformat() if t.ddeadline_at else datetime.now(UTC).isoformat(),
            messages=messages_dto,
            escalation_reason=t.vescalation_reason,
            agreed_slot=t.vagreed_slot,
        )

    async def list_threads(
        self,
        status: str | None = None,
        params: PaginationParams | None = None,
    ) -> PaginatedResponse[NegotiationThreadDTO]:
        p = params or PaginationParams()
        items, total = await self.negotiation_repo.list_threads(status=status, offset=p.offset, limit=p.limit)
        return PaginatedResponse.create(
            items=[self._to_thread_dto(t) for t in items],
            total=total,
            page=p.page,
            page_size=p.page_size,
        )

    async def get_thread(self, thread_id: str) -> NegotiationThreadDTO | None:
        t_id = int(thread_id) if thread_id.isdigit() else 1
        thread = await self.negotiation_repo.get_thread(t_id)
        return self._to_thread_dto(thread) if thread else None

    async def reply_thread_message(
        self,
        thread_id: str,
        content: str,
        sender_role: str = "HR_ADMIN",
        channel: str = "whatsapp",
    ) -> ThreadMessageDTO:
        t_id = int(thread_id) if thread_id.isdigit() else 1
        thread = await self.negotiation_repo.get_thread(t_id)
        if not thread:
            raise ValueError(f"Thread {thread_id} tidak ditemukan.")

        msg_data = {
            "nround_number": thread.ncurrent_round,
            "vsender_role": sender_role,
            "vsender_name": "HR Operations",
            "vchannel": channel,
            "vcontent": content,
            "vproposed_slot": None,
            "vsource_citation": "[manual-hr-input]",
            "bis_rejection": False,
        }
        msg = await self.negotiation_repo.append_message(t_id, msg_data)

        # Log audit
        await self.audit_service.log_event(
            event_type="THREAD_REPLY_SENT",
            actor=sender_role,
            actor_type="HUMAN",
            title="Negotiation Thread Reply",
            description=f"Balasan dikirimkan pada thread #{t_id} via {channel.upper()}: {content[:80]}...",
            metadata={"thread_id": t_id, "channel": channel, "sender_role": sender_role},
        )

        return ThreadMessageDTO(
            id=str(msg.nid),
            round_number=msg.nround_number,
            sender_role=msg.vsender_role,  # type: ignore[arg-type]
            sender_name=msg.vsender_name,
            channel=msg.vchannel,  # type: ignore[arg-type]
            sent_at=datetime.now(UTC).isoformat(),
            content=msg.vcontent,
            proposed_slot=msg.vproposed_slot,
            source_citation=msg.vsource_citation,
            is_rejection=msg.bis_rejection,
        )
