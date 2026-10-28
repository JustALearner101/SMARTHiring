import asyncio
import email.utils
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from app.core.AppConfig import settings

logger = logging.getLogger(__name__)


class EmailDispatcherService:
    """Asynchronous Email Dispatcher Service for Heketon AI Orchestrator.

    Integrates with SMTP Gateway (Sumopod / SSL Port 465) to deliver real
    interview invitations and notifications to candidates and interviewers.
    Preserves Pillar 1 (SOURCES Cited) and Pillar 3 (Human Approval Gate).
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

            <!-- Sources / Verification -->
            {sources_html}

            <!-- Human-in-the-Loop Badge -->
            <div style="margin-top: 24px; padding: 12px 16px; background-color: #eff6ff; border-left: 4px solid #3b82f6; border-radius: 4px; font-size: 12px; color: #1e40af;">
                🛡️ <strong>Pilar Human-in-the-Loop & Audit Record</strong>: Undangan ini telah disetujui secara eksplisit oleh HR Lead melalui verifikasi gerbang persetujuan AI Heketon.
            </div>
        </div>

        <!-- Footer -->
        <div style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 20px 24px; text-align: center; font-size: 12px; color: #94a3b8;">
            Heketon Autonomous Office Agent — Challenge B (The Office Agent)<br>
            Powered by Tencent Cloud & Sumopod AI Infrastructure
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
    ) -> str:
        """Synchronous SMTP delivery helper executed in thread pool."""
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = f"{recipient_name} <{to_email}>"
        msg["Reply-To"] = f"{self.from_name} <{self.from_email}>"
        msg["Subject"] = subject
        msg["Date"] = email.utils.formatdate(localtime=True)
        sender_domain = self.from_email.split("@")[-1] if "@" in self.from_email else "smarthiring.ai"
        message_id = email.utils.make_msgid(domain=sender_domain)
        msg["Message-ID"] = message_id
        msg["X-Mailer"] = "Heketon AI Orchestrator 1.0 (Hackathon Edition)"
        msg["Auto-Submitted"] = "auto-generated"
        msg["X-Auto-Response-Suppress"] = "All"

        part_text = MIMEText(plain_text, "plain", "utf-8")
        part_html = MIMEText(html_body, "html", "utf-8")
        msg.attach(part_text)
        msg.attach(part_html)

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
            f"---\n"
            f"SmartHiring AI Orchestrator (Tencent Cloud Hackathon 2026)"
        )

        try:
            msg_id = await asyncio.to_thread(
                self._sync_send,
                to_email=to_email,
                recipient_name=recipient_name,
                subject=subject,
                plain_text=plain_text,
                html_body=html_body,
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
