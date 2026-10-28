from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.SimulatorEmailDTO import SimulatedEmailDTO
from app.model.OrchestrationModel import ThreadMessage


class SimulatorEmailService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_emails(self, folder: str = "inbox") -> list[SimulatedEmailDTO]:
        stmt = (
            select(ThreadMessage)
            .where(ThreadMessage.vchannel == "email")
            .order_by(ThreadMessage.nid.desc())
        )
        messages = (await self.session.execute(stmt)).scalars().all()
        if messages:
            return [
                SimulatedEmailDTO(
                    id=f"em-{m.nid}",
                    thread_id=str(m.nid_thread),
                    sender_name=m.vsender_name,
                    sender_email="budi.santoso@company.com" if m.vsender_role != "AI_ORCHESTRATOR" else "orchestrator@smarthiring.ai",
                    sender_role="Hiring Manager" if m.vsender_role != "AI_ORCHESTRATOR" else "AI System",
                    recipient_name="Budi Santoso",
                    recipient_email="budi.santoso@company.com",
                    subject=f"[Undangan] User Technical Interview — Ronde #{m.nround_number}",
                    body_text=m.vcontent,
                    sent_at=m.dcrea.isoformat(),
                    is_read=True,
                    is_starred=False,
                    folder=folder,
                    tags=["Invitation", "High-Impact"],
                    meeting_details={
                        "platform": "Google Meet",
                        "meeting_link": "https://meet.google.com/hkt-ops-2026",
                        "date_formatted": "Rabu, 28 Oktober 2026",
                        "time_wib": "10:00 - 11:00 WIB",
                        "time_wita": "11:00 - 12:00 WITA",
                        "calendar_ref": m.vsource_citation or "[cal-budi-01]",
                    },
                )
                for m in messages
            ]

        now_str = datetime.now(UTC).isoformat()
        return [
            SimulatedEmailDTO(
                id="em-001",
                thread_id="th-001",
                sender_name="SmartHiring AI Orchestrator",
                sender_email="orchestrator@smarthiring.ai",
                sender_role="AI System",
                recipient_name="Budi Santoso",
                recipient_email="budi.santoso@company.com",
                subject="[Undangan] User Technical Interview — Rina Kusuma",
                body_text="Yth. Pak Budi Santoso,\n\nKandidat Rina Kusuma (Senior Frontend Engineer) telah lolos screening awal dan dijadwalkan untuk wawancara teknis.",
                sent_at=now_str,
                is_read=True,
                is_starred=False,
                folder="inbox",
                tags=["Invitation", "High-Impact"],
                meeting_details={
                    "platform": "Google Meet",
                    "meeting_link": "https://meet.google.com/hkt-ops-2026",
                    "date_formatted": "Rabu, 28 Oktober 2026",
                    "time_wib": "10:00 - 11:00 WIB",
                    "time_wita": "11:00 - 12:00 WITA",
                    "calendar_ref": "[cal-budi-01]",
                },
            ),
            SimulatedEmailDTO(
                id="em-002",
                thread_id="th-001",
                sender_name="Budi Santoso",
                sender_email="budi.santoso@company.com",
                sender_role="VP of Engineering",
                recipient_name="SmartHiring AI Orchestrator",
                recipient_email="orchestrator@smarthiring.ai",
                subject="Re: [Undangan] User Technical Interview — Rina Kusuma",
                body_text="Halo tim, slot Rabu 28 Oktober jam 10:00 WIB aman di kalender saya. Silakan konfirmasi ke kandidat.",
                sent_at=now_str,
                is_read=True,
                is_starred=True,
                folder="sent" if folder == "sent" else "inbox",
                tags=["Confirmation"],
            ),
        ]
