from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.AgentState import OrchestratorAgentState
from app.model.CandidateModel import Candidate
from app.model.OrchestrationModel import CalendarEvent, NegotiationThread, ThreadMessage
from app.service.AuditLogService import AuditLogService
from app.service.EmailDispatcherService import EmailDispatcherService


class ExecutorNode:
    """Node 5: Channel & Calendar Executor (Pilar APPROVAL, RECORD & SOURCES).

    Executes actual mutations to PostgreSQL and triggers real external communication
    (SMTP Email Gateway) when an ActionPlan is approved and passes the 60-second undo window:
    - Books calendar slot in tblt_calendar_event
    - Upserts negotiation thread in tblt_negotiation_thread
    - Appends sent messages to tblt_thread_message
    - Dispatches verified email invitations via EmailDispatcherService (Sumopod SMTP)
    - Updates candidate status to INTERVIEW_SCHEDULED
    - Writes immutable SHA-256 hash-chained audit logs (ACTION_EXECUTED & EMAIL_DISPATCHED)
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit_service = AuditLogService(session)
        self.email_service = EmailDispatcherService()

    async def execute_plan(self, state: OrchestratorAgentState, approved_by: str = "HR Admin") -> dict[str, Any]:
        slot = state.get("proposed_slot") or {}
        inter_id = state.get("interviewer_id") or 1
        cand_id = state.get("candidate_id") or 1
        cand_name = state.get("candidate_name") or "Rina Kusuma"
        cand_channel = state.get("candidate_channel") or "whatsapp"
        items = state.get("items") or []

        start_utc_str = slot.get("start_utc")
        end_utc_str = slot.get("end_utc")
        now = datetime.now(UTC)

        start_utc = datetime.fromisoformat(start_utc_str) if start_utc_str else now
        if start_utc.tzinfo is None:
            start_utc = start_utc.replace(tzinfo=UTC)

        duration = int(slot.get("duration_minutes") or 60)
        end_utc = datetime.fromisoformat(end_utc_str) if end_utc_str else (start_utc + timedelta(minutes=duration))
        if end_utc.tzinfo is None:
            end_utc = end_utc.replace(tzinfo=UTC)

        # 1. Book Calendar Event
        cal_event = CalendarEvent(
            nid_user=inter_id,
            vtitle=slot.get("title", f"User Technical Interview: {cand_name}"),
            dscheduled_start_utc=start_utc,
            dscheduled_end_utc=end_utc,
            vevent_type="SCHEDULED_INTERVIEW",
            vcandidate_name=cand_name,
            vrule_code="[cal-agent-booked]",
            vdescription=f"Automated booking via AI Orchestrator approved by {approved_by}.",
        )
        self.session.add(cal_event)

        # 2. Upsert Negotiation Thread
        thread_id = state.get("thread_id")
        existing_thread = None
        if thread_id:
            existing_thread = (await self.session.execute(
                select(NegotiationThread).where(NegotiationThread.nid == thread_id)
            )).scalars().first()

        if not existing_thread:
            stmt = (
                select(NegotiationThread)
                .where(
                    NegotiationThread.nid_candidate == cand_id,
                    NegotiationThread.nid_interviewer == inter_id,
                )
                .order_by(NegotiationThread.nid.desc())
            )
            existing_thread = (await self.session.execute(stmt)).scalars().first()

        agreed_slot_desc = slot.get("formatted_wib") or str(start_utc)

        if not existing_thread:
            thread = NegotiationThread(
                nid_candidate=cand_id,
                nid_interviewer=inter_id,
                ncurrent_round=state.get("negotiation_round", 1),
                nmax_rounds=state.get("max_rounds", 3),
                vstatus="SCHEDULED",
                vagreed_slot=agreed_slot_desc,
                dlast_activity_at=now,
            )
            self.session.add(thread)
            await self.session.flush()
        else:
            thread = existing_thread
            thread.vstatus = "SCHEDULED"
            thread.vagreed_slot = agreed_slot_desc
            thread.dlast_activity_at = now
            self.session.add(thread)

        # 3. Append Outbound Dialogue Messages & Dispatch Real Email
        dispatched_emails: list[dict[str, Any]] = []

        for item in items:
            channel = item.get("channel", "email")
            if channel in ["whatsapp", "email"]:
                content = item.get("content_preview") or f"Undangan interview untuk {cand_name}."
                recipient_contact = item.get("recipient_contact") or ""
                recipient_name = item.get("recipient_name", cand_name)
                recipient_role = item.get("recipient_role", "Candidate")

                # If channel is email and a valid address is present, dispatch real email
                if channel == "email" and "@" in recipient_contact:
                    email_res = await self.email_service.send_interview_email(
                        to_email=recipient_contact,
                        recipient_name=recipient_name,
                        recipient_role=recipient_role,
                        subject=item.get("subject") or f"[Undangan] User Technical Interview: {cand_name}",
                        content=content,
                        slot_wib=agreed_slot_desc,
                        meeting_link=slot.get("meeting_link", "https://meet.google.com/hkt-ops-2026"),
                        citations=state.get("sources_cited", []),
                    )
                    dispatched_emails.append({
                        "recipient": recipient_contact,
                        "name": recipient_name,
                        "res": email_res,
                    })

                msg = ThreadMessage(
                    nid_thread=thread.nid,
                    nround_number=thread.ncurrent_round,
                    vsender_role="AI_ORCHESTRATOR",
                    vsender_name="SmartHiring AI Orchestrator",
                    vchannel=channel,
                    vcontent=content,
                    vproposed_slot=agreed_slot_desc,
                    vsource_citation="[cal-booking-confirmed]",
                    bis_rejection=False,
                )
                self.session.add(msg)

        # 4. Update Candidate Application Stage
        cand_stmt = select(Candidate).where(Candidate.nid == cand_id)
        candidate = (await self.session.execute(cand_stmt)).scalars().first()
        if candidate:
            candidate.vstatus = "INTERVIEW_SCHEDULED"
            self.session.add(candidate)

        await self.session.commit()

        # 5. Append SHA-256 Audit Log for Action Execution
        audit_entries = [*state.get("audit_entries", [])]

        action_audit = await self.audit_service.log_event(
            event_type="ACTION_EXECUTED",
            actor=approved_by,
            actor_type="HUMAN",
            title="Interview Action Plan Executed",
            description=(
                f"Undangan wawancara untuk {cand_name} ({cand_channel.upper()}) dan {state.get('interviewer_name')} "
                f"berhasil dikirim dan dijadwalkan pada {agreed_slot_desc}."
            ),
            metadata={
                "candidate_id": cand_id,
                "interviewer_id": inter_id,
                "slot": agreed_slot_desc,
                "calendar_event_id": cal_event.nid,
                "thread_id": thread.nid,
            },
        )
        audit_entries.append({
            "event_type": "ACTION_EXECUTED",
            "id": action_audit.id,
            "hash": action_audit.metadata.get("hash"),
        })

        # 6. Append SHA-256 Audit Logs for Dispatched Emails
        for disp in dispatched_emails:
            res = disp["res"]
            to_email = disp["recipient"]
            name = disp["name"]
            if res.get("success"):
                email_audit = await self.audit_service.log_event(
                    event_type="EMAIL_DISPATCHED",
                    actor="AI_ORCHESTRATOR",
                    actor_type="AGENT",
                    title=f"Interview Email Delivered: {name}",
                    description=(
                        f"Undangan wawancara berhasil dikirim ke {to_email} via Sumopod SMTP (SSL 465). "
                        f"Message-ID: {res.get('message_id')}"
                    ),
                    metadata={
                        "recipient": to_email,
                        "recipient_name": name,
                        "message_id": res.get("message_id"),
                        "simulated": res.get("simulated", False),
                        "slot": agreed_slot_desc,
                    },
                )
                audit_entries.append({
                    "event_type": "EMAIL_DISPATCHED",
                    "id": email_audit.id,
                    "hash": email_audit.metadata.get("hash"),
                })
            else:
                fail_audit = await self.audit_service.log_event(
                    event_type="EMAIL_DISPATCH_FAILED",
                    actor="AI_ORCHESTRATOR",
                    actor_type="AGENT",
                    title=f"Email Delivery Failed: {name}",
                    description=f"Gagal mengirim email ke {to_email}: {res.get('error')}",
                    metadata={
                        "recipient": to_email,
                        "error": res.get("error"),
                    },
                )
                audit_entries.append({
                    "event_type": "EMAIL_DISPATCH_FAILED",
                    "id": fail_audit.id,
                    "hash": fail_audit.metadata.get("hash"),
                })

        return {
            "status": "EXECUTED",
            "thread_id": thread.nid,
            "dispatched_emails": dispatched_emails,
            "audit_entries": audit_entries,
        }
