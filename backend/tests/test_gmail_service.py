from __future__ import annotations

import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.kortana.services.gmail_service import GmailConfigurationError, GmailService


def _make_service() -> GmailService:
    settings = MagicMock()
    settings.GOOGLE_CLIENT_ID = "google-client"
    settings.GOOGLE_CLIENT_SECRET = "google-secret"
    settings.GOOGLE_REFRESH_TOKEN = "google-refresh"
    settings.GMAIL_SCOPES = [
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.send",
    ]
    return GmailService(settings=settings)


class TestGmailService:
    @pytest.mark.asyncio
    async def test_status_reports_unconfigured_when_google_oauth_missing(self) -> None:
        settings = MagicMock()
        settings.GOOGLE_CLIENT_ID = None
        settings.GOOGLE_CLIENT_SECRET = None
        settings.GOOGLE_REFRESH_TOKEN = None
        settings.GMAIL_SCOPES = []
        service = GmailService(settings=settings)

        status = await service.get_status()

        assert status["configured"] is False
        assert status["ready"] is False
        assert "GOOGLE_CLIENT_ID" in status["detail"]

    @pytest.mark.asyncio
    async def test_list_messages_returns_summaries(self) -> None:
        service = _make_service()
        mock_request = AsyncMock(
            side_effect=[
                {"messages": [{"id": "msg-1"}], "resultSizeEstimate": 1},
                {
                    "id": "msg-1",
                    "threadId": "thr-1",
                    "historyId": "hist-1",
                    "internalDate": "171000",
                    "snippet": "hello",
                    "labelIds": ["INBOX", "UNREAD"],
                    "payload": {
                        "headers": [
                            {"name": "Subject", "value": "Sacred update"},
                            {"name": "From", "value": "alice@example.com"},
                            {"name": "To", "value": "madouble7@gmail.com"},
                            {"name": "Date", "value": "Mon, 01 Jan 2026 00:00:00 +0000"},
                        ]
                    },
                },
            ]
        )

        with patch.object(service, "_request", mock_request):
            result = await service.list_messages(limit=5, query="in:inbox")

        assert result["count"] == 1
        assert result["messages"][0]["subject"] == "Sacred update"
        assert result["messages"][0]["unread"] is True
        assert result["messages"][0]["in_inbox"] is True

    @pytest.mark.asyncio
    async def test_send_message_encodes_raw_mime_payload(self) -> None:
        service = _make_service()
        mock_request = AsyncMock(
            return_value={"id": "gmail-msg", "threadId": "gmail-thread", "labelIds": ["SENT"]}
        )

        with patch.object(service, "_request", mock_request):
            result = await service.send_message(
                to="friend@example.com",
                subject="Kor'tana",
                body="Hello from the sacred machine.",
                cc=["ally@example.com"],
                thread_id="thread-1",
                in_reply_to="<parent@example.com>",
            )

        assert result["id"] == "gmail-msg"
        sent_payload = mock_request.await_args.kwargs["json"]
        decoded = base64.urlsafe_b64decode(sent_payload["raw"].encode("utf-8"))
        decoded_text = decoded.decode("utf-8", errors="replace")
        assert "To: friend@example.com" in decoded_text
        assert "Cc: ally@example.com" in decoded_text
        assert "Subject: Kor'tana" in decoded_text
        assert "Hello from the sacred machine." in decoded_text
        assert sent_payload["threadId"] == "thread-1"

    @pytest.mark.asyncio
    async def test_archive_message_removes_inbox_label(self) -> None:
        service = _make_service()
        mock_request = AsyncMock(return_value={"labelIds": ["CATEGORY_PERSONAL"]})

        with patch.object(service, "_request", mock_request):
            result = await service.archive_message("msg-7")

        assert result == {
            "message_id": "msg-7",
            "archived": True,
            "label_ids": ["CATEGORY_PERSONAL"],
        }
        assert mock_request.await_args.kwargs["json"] == {"removeLabelIds": ["INBOX"]}

    def test_require_configured_raises_for_missing_refresh_token(self) -> None:
        settings = MagicMock()
        settings.GOOGLE_CLIENT_ID = "google-client"
        settings.GOOGLE_CLIENT_SECRET = "google-secret"
        settings.GOOGLE_REFRESH_TOKEN = None
        settings.GMAIL_SCOPES = []
        service = GmailService(settings=settings)

        with pytest.raises(GmailConfigurationError, match="GOOGLE_REFRESH_TOKEN"):
            service._require_configured()
