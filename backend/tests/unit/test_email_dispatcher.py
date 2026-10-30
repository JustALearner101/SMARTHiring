from unittest.mock import MagicMock, patch

import pytest

from app.service.EmailDispatcherService import EmailDispatcherService


@pytest.mark.asyncio
async def test_email_dispatcher_build_html() -> None:
    service = EmailDispatcherService()
    citations = [
        {"ref_code": "[cal-test]", "title": "Test Calendar", "detail": "Test Slot Details"},
    ]
    html = service._build_html_body(
        recipient_name="Akhtar Ramadhan",
        role="Candidate",
        agenda="Wawancara Teknis AI",
        slot_wib="Rabu, 29 Okt 2026, 10:00 WIB",
        meeting_link="https://meet.google.com/test-123",
        citations=citations,
    )
    assert "Akhtar Ramadhan" in html
    assert "Candidate" in html
    assert "Rabu, 29 Okt 2026, 10:00 WIB" in html
    assert "https://meet.google.com/test-123" in html
    assert "[cal-test]" in html
    assert "Test Calendar" in html


@pytest.mark.asyncio
async def test_email_dispatcher_mocked_success() -> None:
    service = EmailDispatcherService()
    service.enabled = True
    service.user = "mock_user"
    service.password = "mock_pass"
    service.use_ssl = True

    mock_server = MagicMock()
    with patch("smtplib.SMTP_SSL", return_value=mock_server):
        mock_server.__enter__.return_value = mock_server

        res = await service.send_interview_email(
            to_email="test.candidate@example.com",
            recipient_name="Test Candidate",
            subject="Test Subject",
            content="Test Agenda",
            slot_wib="Rabu, 29 Okt 2026, 10:00 WIB",
        )

        assert res["success"] is True
        assert res["simulated"] is False
        assert res["recipient"] == "test.candidate@example.com"
        assert res["message_id"] is not None
        assert res["error"] is None
        mock_server.login.assert_called_once_with("mock_user", "mock_pass")
        assert mock_server.sendmail.called


@pytest.mark.asyncio
async def test_email_dispatcher_resilient_error_handling() -> None:
    service = EmailDispatcherService()
    service.enabled = True
    service.user = "mock_user"
    service.password = "mock_pass"
    service.use_ssl = True

    with patch("smtplib.SMTP_SSL", side_effect=ConnectionRefusedError("SMTP server down")):
        res = await service.send_interview_email(
            to_email="test.candidate@example.com",
            recipient_name="Test Candidate",
            subject="Test Subject",
            content="Test Agenda",
            slot_wib="Rabu, 29 Okt 2026, 10:00 WIB",
        )

        assert res["success"] is False
        assert res["simulated"] is False
        assert "SMTP server down" in res["error"]


@pytest.mark.asyncio
async def test_email_dispatcher_disabled_simulation() -> None:
    service = EmailDispatcherService()
    service.enabled = False

    res = await service.send_interview_email(
        to_email="test.candidate@example.com",
        recipient_name="Test Candidate",
        subject="Test Subject",
        content="Test Agenda",
        slot_wib="Rabu, 29 Okt 2026, 10:00 WIB",
    )

    assert res["success"] is True
    assert res["simulated"] is True
    assert res["error"] is None
    assert "simulated-" in res["message_id"]
