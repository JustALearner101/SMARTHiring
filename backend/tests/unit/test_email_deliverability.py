import email
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.service.EmailDispatcherService import EmailDispatcherService


@pytest.mark.asyncio
async def test_email_ics_rfc5545_generation():
    service = EmailDispatcherService()
    now = datetime.now(UTC)
    start_utc = now + timedelta(days=2, hours=3)
    end_utc = start_utc + timedelta(hours=1)

    ics = service._generate_ics(
        start_utc=start_utc,
        end_utc=end_utc,
        summary="User Technical Interview: Rina Kusuma",
        description="Agenda wawancara teknis frontend engineering.",
        meeting_link="https://meet.google.com/hkt-ops-2026",
        recipient_email="rina.kusuma@example.com",
        recipient_name="Rina Kusuma",
    )

    assert "BEGIN:VCALENDAR" in ics
    assert "VERSION:2.0" in ics
    assert "METHOD:REQUEST" in ics
    assert "BEGIN:VEVENT" in ics
    assert "UID:" in ics
    assert "@heketon.ai" in ics
    assert "DTSTAMP:" in ics
    assert "DTSTART:" in ics
    assert "DTEND:" in ics
    assert "SUMMARY:User Technical Interview: Rina Kusuma" in ics
    assert "ORGANIZER;CN=" in ics
    assert "ATTENDEE;ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=TRUE;CN=Rina Kusuma:mailto:rina.kusuma@example.com" in ics
    assert "END:VEVENT" in ics
    assert "END:VCALENDAR" in ics


@pytest.mark.asyncio
async def test_email_deliverability_header_hygiene_and_mime():
    service = EmailDispatcherService()
    service.enabled = True
    service.user = "test_user"
    service.password = "test_pass"
    service.use_ssl = True

    captured_raw_email: list[str] = []

    mock_server = MagicMock()
    with patch("smtplib.SMTP_SSL", return_value=mock_server):
        mock_server.__enter__.return_value = mock_server

        def capture_sendmail(from_addr, to_addrs, msg_string):
            captured_raw_email.append(msg_string)

        mock_server.sendmail.side_effect = capture_sendmail

        res = await service.send_interview_email(
            to_email="candidate@example.com",
            recipient_name="Ahmad Fauzi",
            subject="Undangan Wawancara Teknis — SmartHiring",
            content="Halo Ahmad, kami mengundang Anda untuk sesi teknis.",
            slot_wib="Kamis, 05 Nov 2026, 14:00 WIB",
            meeting_link="https://meet.google.com/hkt-ops-2026",
        )

        assert res["success"] is True
        assert len(captured_raw_email) == 1

        raw_str = captured_raw_email[0]
        parsed_msg = email.message_from_string(raw_str)

        # 1. Deliverability RFC headers
        assert parsed_msg["Message-ID"] is not None
        assert "@" in parsed_msg["Message-ID"]
        assert parsed_msg["Auto-Submitted"] == "auto-generated"
        assert parsed_msg["Precedence"] == "bulk"
        assert "mailto:unsubscribe@" in parsed_msg["List-Unsubscribe"]
        assert parsed_msg["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
        assert parsed_msg["X-Auto-Response-Suppress"] == "All"
        assert "bounces@" in parsed_msg["Return-Path"]

        # 2. MIME Structure: multipart/mixed
        assert parsed_msg.is_multipart()
        assert parsed_msg.get_content_type() == "multipart/mixed"

        # 3. Payload contains alternative part + attachment
        parts = list(parsed_msg.walk())
        content_types = [p.get_content_type() for p in parts]

        assert "text/plain" in content_types
        assert "text/html" in content_types
        assert "text/calendar" in content_types


@pytest.mark.asyncio
async def test_email_html_canspam_footer():
    service = EmailDispatcherService()
    html = service._build_html_body(
        recipient_name="Rina Kusuma",
        role="Candidate",
        agenda="Sesi evaluasi coding online.",
        slot_wib="Rabu, 04 Nov 2026, 10:00 WIB",
        meeting_link="https://meet.google.com/hkt-ops-2026",
    )

    # Physical address check
    assert "SmartHiring Inc. / Heketon Ops" in html
    assert "Menara BTPN Lt. 32" in html
    assert "Jakarta Selatan" in html
    # Unsubscribe link check
    assert "Unsubscribe" in html
