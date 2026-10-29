import asyncio
import email.utils
import logging
import smtplib
import uuid
from datetime import UTC, datetime, timedelta
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from app.core.AppConfig import settings

logger = logging.getLogger(__name__)


class EmailDispatcherService:
    """Asynchronous Email Dispatcher Service for Heketon AI Orchestrator.

    Integrates with SMTP Gateway (Sumopod / SSL Port 465) to deliver real
    interview invitations and notifications to candidates and interviewers.
    Adheres strictly to RFC 2822 / 5322 header hygiene, RFC 5545 iCalendar (.ics)
    interactivity (RSVP widget in Gmail/Outlook), and CAN-SPAM compliant copywriting.
    """

    def __init__(self) -> None:
        self.enabled = settings.SMTP_ENABLED
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.use_ssl = settings.SMTP_SSL
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME

    def _generate_ics(
        self,
        start_utc: datetime,
        end_utc: datetime,
        summary: str,
        description: str,
        meeting_link: str,
        recipient_email: str,
        recipient_name: str,
    ) -> str:
        """Generate an RFC 5545 compliant iCalendar (.ics) payload."""
        now_utc = datetime.now(UTC)
        uid = f"{uuid.uuid4()}@heketon.ai"
        dtstamp = now_utc.strftime("%Y%m%dT%H%M%SZ")
        dtstart = start_utc.strftime("%Y%m%dT%H%M%SZ")
        dtend = end_utc.strftime("%Y%m%dT%H%M%SZ")

        # Clean description for ICS (escape newlines and special characters)
        clean_desc = (
            description.replace("\r\n", "\\n")
            .replace("\n", "\\n")
            .replace(",", "\\,")
            .replace(";", "\\;")
        )

        ics_lines = [
            "BEGIN:VCALENDAR",
            "PRODID:-//Heketon AI Orchestrator//ID",
            "VERSION:2.0",
            "CALSCALE:GREGORIAN",
            "METHOD:REQUEST",
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dtstamp}",
            f"DTSTART:{dtstart}",
            f"DTEND:{dtend}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{clean_desc}",
            f"LOCATION:{meeting_link}",
            "STATUS:CONFIRMED",
            "SEQUENCE:0",
            f"ORGANIZER;CN={self.from_name}:mailto:{self.from_email}",
            f"ATTENDEE;ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=TRUE;CN={recipient_name}:mailto:{recipient_email}",
            "TRANSP:OPAQUE",
            "END:VEVENT",
            "END:VCALENDAR",
        ]
        return "\r\n".join(ics_lines) + "\r\n"

    def _build_html_body(
        self,
        recipient_name: str,
        role: str,
        agenda: str,
        slot_wib: str,
        meeting_link: str,
        citations: list[dict[str, Any]] | None = None,
    ) -> str:
        sources_html = ""
        if citations:
            citations_li = "".join(
                f'<li style="margin-bottom: 6px;"><strong>{c.get("ref_code", "")}</strong> — {c.get("title", "")}: <span style="color: #64748b;">{c.get("detail", "")}</span></li>'
                for c in citations
            )
            sources_html = f"""
            <div style="margin-top: 24px; padding: 16px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
                <h4 style="margin: 0 0 10px 0; color: #0f172a; font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em;">
                    Verified Grounding Sources (Pilar SOURCES):
                </h4>
                <ul style="margin: 0; padding-left: 20px; font-size: 12px; color: #334155; line-height: 1.5;">
                    {citations_li}
                </ul>
            </div>
            """

        sender_domain = self.from_email.split("@")[-1] if "@" in self.from_email else "smarthiring.ai"

        return f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Undangan Interview — SmartHiring AI Orchestrator</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 24px;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);">
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 32px 24px; text-align: center; color: #ffffff;">
            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.15em; color: #93c5fd; margin-bottom: 8px;">
                Tencent Cloud Hackathon Indonesia 2026
            </div>
            <h1 style="margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.02em;">
                SmartHiring AI Orchestrator
            </h1>
            <p style="margin: 8px 0 0 0; font-size: 14px; color: #e0e7ff;">
                Konfirmasi Jadwal User Technical Interview
            </p>
        </div>

        <!-- Body -->
        <div style="padding: 32px 24px; color: #1e293b; line-height: 1.6;">
            <p style="font-size: 16px; margin: 0 0 16px 0;">
                Halo <strong>{recipient_name}</strong> ({role}),
            </p>
            <p style="font-size: 14px; margin: 0 0 20px 0; color: #475569;">
                {agenda}
            </p>

            <!-- Schedule Card -->
            <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 18px 20px; margin-bottom: 24px;">
                <div style="font-size: 12px; font-weight: 700; color: #15803d; text-transform: uppercase; margin-bottom: 6px;">
                    Waktu Wawancara Disepakati:
                </div>
                <div style="font-size: 18px; font-weight: 800; color: #166534;">
                    📅 {slot_wib}
                </div>
                <div style="font-size: 12px; color: #15803d; margin-top: 4px;">
                    Bebas konflik jadwal operasional & di luar jendela Sholat Jumat.
                </div>
            </div>

            <!-- Action Button -->
            <div style="text-align: center; margin: 28px 0;">
                <a href="{meeting_link}" target="_blank" style="background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 14px 28px; border-radius: 8px; font-weight: 700; font-size: 15px; display: inline-block; box-shadow: 0 2px 4px rgba(37, 99, 235, 0.3);">
                    Masuk Google Meet Interview
                </a>
                <div style="font-size: 12px; color: #64748b; margin-top: 8px;">
                    Link: <a href="{meeting_link}" style="color: #2563eb;">{meeting_link}</a>
                </div>
            </div>

            <!-- Interactive Calendar Notice -->
            <div style="margin-top: 20px; padding: 12px 16px; background-color: #f0fdfa; border: 1px solid #ccfbf1; border-radius: 8px; font-size: 12px; color: #0f766e;">
                🗓️ <strong>Undangan Kalender Interaktif Terlampir</strong>: Email ini memuat file kalender terintegrasi (<code>invite.ics</code>). Anda dapat langsung mengklik <em>Terima / Accept</em> pada tombol kalender di aplikasi Gmail / Outlook Anda.
            </div>

            <!-- Sources / Verification -->
            {sources_html}

            <!-- Human-in-the-Loop Badge -->
            <div style="margin-top: 24px; padding: 12px 16px; background-color: #eff6ff; border-left: 4px solid #3b82f6; border-radius: 4px; font-size: 12px; color: #1e40af;">
                🛡️ <strong>Pilar Human-in-the-Loop & Audit Record</strong>: Undangan ini telah disetujui secara eksplisit oleh HR Lead melalui verifikasi gerbang persetujuan AI Heketon.
            </div>
        </div>

        <!-- CAN-SPAM Compliant Footer -->
        <div style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 20px 24px; text-align: center; font-size: 11px; color: #94a3b8; line-height: 1.5;">
            <strong>SmartHiring Inc. / Heketon Ops</strong><br>
            Menara BTPN Lt. 32, Jl. Dr. Ide Anak Agung Gde Agung Kav 5.5-5.6, Jakarta Selatan 12950, Indonesia<br>
            Email otomatis dikirimkan terkait proses seleksi interview terverifikasi.<br>
            <a href="mailto:unsubscribe@{sender_domain}?subject=unsubscribe" style="color: #64748b; text-decoration: underline;">Berhenti Berlangganan / Unsubscribe</a> • <a href="https://heketon.ai/privacy" style="color: #64748b; text-decoration: underline;">Kebijakan Privasi</a>
        </div>
    </div>
</body>
</html>"""

    def _sync_send(
        self,
        to_email: str,
        recipient_name: str,
        subject: str,
        plain_text: str,
        html_body: str,
        ics_content: str | None = None,
    ) -> str:
        """Synchronous SMTP delivery helper with RFC 2822 hygiene and .ics attachment."""
        sender_domain = self.from_email.split("@")[-1] if "@" in self.from_email else "smarthiring.ai"
        message_id = email.utils.make_msgid(domain=sender_domain)

        # Outer multipart/mixed container
        msg = MIMEMultipart("mixed")
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = f"{recipient_name} <{to_email}>"
        msg["Reply-To"] = f"{self.from_name} <{self.from_email}>"
        msg["Return-Path"] = f"bounces@{sender_domain}"
        msg["Subject"] = subject
        msg["Date"] = email.utils.formatdate(localtime=True)
        msg["Message-ID"] = message_id
        msg["X-Mailer"] = "Heketon AI Orchestrator 1.0 (Hackathon Edition)"
        msg["Auto-Submitted"] = "auto-generated"
        msg["Precedence"] = "bulk"
        msg["List-Unsubscribe"] = f"<mailto:unsubscribe@{sender_domain}?subject=unsubscribe>"
        msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
        msg["X-Auto-Response-Suppress"] = "All"

        # Inner multipart/alternative container for text and HTML
        alt_container = MIMEMultipart("alternative")
        part_text = MIMEText(plain_text, "plain", "utf-8")
        part_html = MIMEText(html_body, "html", "utf-8")
        alt_container.attach(part_text)
        alt_container.attach(part_html)

        # If interactive iCalendar is provided, attach it to alternative part
        if ics_content:
            part_cal = MIMEText(ics_content, "calendar; method=REQUEST; charset=UTF-8", "utf-8")
            part_cal.add_header("Content-Class", "urn:content-classes:calendarmessage")
            alt_container.attach(part_cal)

        msg.attach(alt_container)

        # Also attach .ics as an explicit calendar attachment for Outlook / Apple Mail
        if ics_content:
            cal_attachment = MIMEBase("text", "calendar", name="invite.ics")
            cal_attachment.set_payload(ics_content.encode("utf-8"))
            cal_attachment.add_header("Content-Disposition", 'attachment; filename="invite.ics"')
            cal_attachment.add_header("Content-Class", "urn:content-classes:calendarmessage")
            msg.attach(cal_attachment)

        if self.use_ssl:
            with smtplib.SMTP_SSL(self.host, self.port, timeout=15) as server:
                server.login(self.user, self.password)
                server.sendmail(self.from_email, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(self.host, self.port, timeout=15) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.from_email, [to_email], msg.as_string())

        return message_id

    async def send_interview_email(
        self,
        to_email: str,
        recipient_name: str,
        subject: str,
        content: str,
        slot_wib: str,
        meeting_link: str = "https://meet.google.com/hkt-ops-2026",
        citations: list[dict[str, Any]] | None = None,
        recipient_role: str = "Candidate",
        start_utc: datetime | None = None,
        end_utc: datetime | None = None,
    ) -> dict[str, Any]:
        """Dispatch a verified interview invitation email via SMTP Gateway."""
        if not self.enabled or not self.user or not self.password:
            logger.info("SMTP disabled or unconfigured; falling back to internal simulation.")
            return {
                "success": True,
                "simulated": True,
                "message_id": f"simulated-{email.utils.make_msgid()}",
                "recipient": to_email,
                "error": None,
            }

        html_body = self._build_html_body(
            recipient_name=recipient_name,
            role=recipient_role,
            agenda=content,
            slot_wib=slot_wib,
            meeting_link=meeting_link,
            citations=citations,
        )

        plain_text = (
            f"Halo {recipient_name},\n\n"
            f"{content}\n\n"
            f"Waktu Wawancara: {slot_wib}\n"
            f"Link Google Meet: {meeting_link}\n\n"
            f"Undangan kalender interaktif (.ics) terlampir pada email ini.\n\n"
            f"---\n"
            f"SmartHiring AI Orchestrator (Tencent Cloud Hackathon 2026)\n"
            f"Menara BTPN Lt. 32, Jakarta Selatan 12950, Indonesia"
        )

        # Setup start & end UTC for .ics
        now = datetime.now(UTC)
        cal_start = start_utc or (now + timedelta(days=2, hours=3))
        cal_end = end_utc or (cal_start + timedelta(hours=1))

        ics_content = self._generate_ics(
            start_utc=cal_start,
            end_utc=cal_end,
            summary=f"User Technical Interview: {recipient_name}",
            description=content,
            meeting_link=meeting_link,
            recipient_email=to_email,
            recipient_name=recipient_name,
        )

        try:
            msg_id = await asyncio.to_thread(
                self._sync_send,
                to_email=to_email,
                recipient_name=recipient_name,
                subject=subject,
                plain_text=plain_text,
                html_body=html_body,
                ics_content=ics_content,
            )
            logger.info("Real email successfully dispatched to %s with Message-ID: %s", to_email, msg_id)
            return {
                "success": True,
                "simulated": False,
                "message_id": msg_id,
                "recipient": to_email,
                "error": None,
            }
        except Exception as exc:
            logger.exception("Failed to send real email to %s", to_email)
            return {
                "success": False,
                "simulated": False,
                "message_id": None,
                "recipient": to_email,
                "error": str(exc),
            }
