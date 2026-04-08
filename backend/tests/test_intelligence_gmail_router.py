from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch


class TestGmailIntelligenceRouter:
    def test_status_requires_authentication(self, client) -> None:
        response = client.get("/api/intelligence/email/status")
        assert response.status_code == 401

    def test_status_returns_gmail_readiness(self, authenticated_client) -> None:
        service = MagicMock()
        service.get_status = AsyncMock(
            return_value={
                "configured": True,
                "ready": True,
                "email_address": "madouble7@gmail.com",
                "scopes": [
                    "https://www.googleapis.com/auth/gmail.modify",
                    "https://www.googleapis.com/auth/gmail.send",
                ],
            }
        )

        with patch(
            "src.kortana.routers.intelligence.get_gmail_service",
            return_value=service,
        ):
            response = authenticated_client.get("/api/intelligence/email/status")

        assert response.status_code == 200
        assert response.json()["email_address"] == "madouble7@gmail.com"

    def test_list_messages_returns_triage_payload(self, authenticated_client) -> None:
        service = MagicMock()
        service.list_messages = AsyncMock(
            return_value={
                "query": "in:inbox",
                "count": 1,
                "messages": [{"id": "msg-1", "subject": "hello"}],
            }
        )

        with patch(
            "src.kortana.routers.intelligence.get_gmail_service",
            return_value=service,
        ):
            response = authenticated_client.get(
                "/api/intelligence/email/messages?limit=5&query=in:inbox"
            )

        assert response.status_code == 200
        assert response.json()["messages"][0]["id"] == "msg-1"

    def test_send_message_is_protected_and_uses_service(self, authenticated_client) -> None:
        service = MagicMock()
        service.send_message = AsyncMock(
            return_value={"id": "gmail-msg", "thread_id": "gmail-thread"}
        )

        with patch(
            "src.kortana.routers.intelligence.get_gmail_service",
            return_value=service,
        ):
            response = authenticated_client.post(
                "/api/intelligence/email/send",
                json={
                    "to": "friend@example.com",
                    "subject": "Sacred mail",
                    "body": "Kor'tana is online.",
                },
            )

        assert response.status_code == 200
        assert response.json()["id"] == "gmail-msg"
        assert service.send_message.await_count == 1

    def test_archive_message_uses_service(self, authenticated_client) -> None:
        service = MagicMock()
        service.archive_message = AsyncMock(
            return_value={"message_id": "msg-9", "archived": True}
        )

        with patch(
            "src.kortana.routers.intelligence.get_gmail_service",
            return_value=service,
        ):
            response = authenticated_client.post(
                "/api/intelligence/email/messages/msg-9/archive"
            )

        assert response.status_code == 200
        assert response.json()["archived"] is True
