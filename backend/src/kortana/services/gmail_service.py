"""Gmail integration service for autonomous inbox stewardship."""

from __future__ import annotations

import asyncio
import base64
from email.message import EmailMessage
from typing import Any

import httpx

from src.kortana.config import Settings, get_settings
from src.kortana.logger import get_logger

logger = get_logger(__name__)

GOOGLE_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_API_BASE_URL = "https://gmail.googleapis.com/gmail/v1/users/me"
DEFAULT_GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]


class GmailConfigurationError(RuntimeError):
    """Raised when Gmail OAuth secrets are missing."""


class GmailAPIError(RuntimeError):
    """Raised when the Gmail API returns an actionable error."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 502,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


def _extract_header(headers: list[dict[str, Any]], name: str) -> str | None:
    """Extract a header value from a Gmail payload header list."""
    lowered_name = name.lower()
    for header in headers:
        if str(header.get("name", "")).lower() == lowered_name:
            value = str(header.get("value", "")).strip()
            return value or None
    return None


def _decode_gmail_body(data: str | None) -> str | None:
    """Decode a base64url Gmail body chunk into UTF-8 text."""
    if not data:
        return None

    padding = "=" * (-len(data) % 4)
    decoded = base64.urlsafe_b64decode(f"{data}{padding}".encode("utf-8"))
    text = decoded.decode("utf-8", errors="replace").strip()
    return text or None


def _extract_message_bodies(payload: dict[str, Any] | None) -> dict[str, str | None]:
    """Extract the first plain-text and HTML bodies from a Gmail payload tree."""
    bodies: dict[str, str | None] = {"text": None, "html": None}

    def _walk(part: dict[str, Any] | None) -> None:
        if not part:
            return

        mime_type = str(part.get("mimeType", "")).lower()
        body = part.get("body") or {}
        data = _decode_gmail_body(body.get("data"))

        if mime_type == "text/plain" and bodies["text"] is None and data:
            bodies["text"] = data
        elif mime_type == "text/html" and bodies["html"] is None and data:
            bodies["html"] = data

        for child in part.get("parts") or []:
            if isinstance(child, dict):
                _walk(child)

    _walk(payload)
    return bodies


class GmailService:
    """Minimal Gmail API client using Google OAuth refresh tokens."""

    def __init__(self, settings: Settings | None = None, *, timeout: float = 20.0):
        self.settings = settings or get_settings()
        self.timeout = timeout

    @property
    def scopes(self) -> list[str]:
        """Return the configured Gmail scopes or the runtime defaults."""
        return list(self.settings.GMAIL_SCOPES or DEFAULT_GMAIL_SCOPES)

    def is_configured(self) -> bool:
        """Return whether Gmail OAuth credentials are present."""
        return all(
            [
                self.settings.GOOGLE_CLIENT_ID,
                self.settings.GOOGLE_CLIENT_SECRET,
                self.settings.GOOGLE_REFRESH_TOKEN,
            ]
        )

    def _require_configured(self) -> None:
        """Raise when Gmail OAuth credentials are incomplete."""
        missing = [
            name
            for name, value in (
                ("GOOGLE_CLIENT_ID", self.settings.GOOGLE_CLIENT_ID),
                ("GOOGLE_CLIENT_SECRET", self.settings.GOOGLE_CLIENT_SECRET),
                ("GOOGLE_REFRESH_TOKEN", self.settings.GOOGLE_REFRESH_TOKEN),
            )
            if not value
        ]
        if missing:
            raise GmailConfigurationError(
                "Gmail OAuth is not configured. Missing: " + ", ".join(missing)
            )

    async def _get_access_token(self) -> str:
        """Exchange the configured refresh token for a short-lived access token."""
        self._require_configured()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                GOOGLE_OAUTH_TOKEN_URL,
                data={
                    "client_id": self.settings.GOOGLE_CLIENT_ID,
                    "client_secret": self.settings.GOOGLE_CLIENT_SECRET,
                    "refresh_token": self.settings.GOOGLE_REFRESH_TOKEN,
                    "grant_type": "refresh_token",
                },
            )

        payload = response.json()
        if response.status_code >= 400:
            error_message = (
                payload.get("error_description")
                or payload.get("error")
                or "Google OAuth token refresh failed"
            )
            raise GmailAPIError(
                f"Gmail token refresh failed: {error_message}",
                status_code=502,
                details=payload,
            )

        access_token = payload.get("access_token")
        if not access_token:
            raise GmailAPIError(
                "Google OAuth token refresh did not return an access token",
                status_code=502,
                details=payload,
            )

        return str(access_token)

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Make an authenticated Gmail API request."""
        access_token = await self._get_access_token()
        headers = dict(kwargs.pop("headers", {}))
        headers["Authorization"] = f"Bearer {access_token}"
        headers.setdefault("Accept", "application/json")

        url = f"{GMAIL_API_BASE_URL}{path}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(method, url, headers=headers, **kwargs)

        if response.status_code >= 400:
            try:
                payload = response.json()
            except ValueError:
                payload = {"error": {"message": response.text}}
            error_payload = payload.get("error") if isinstance(payload, dict) else None
            message = (
                error_payload.get("message")
                if isinstance(error_payload, dict)
                else response.text
            )
            raise GmailAPIError(
                f"Gmail API request failed: {message or 'Unknown Gmail API error'}",
                status_code=response.status_code,
                details=payload if isinstance(payload, dict) else {},
            )

        if response.status_code == 204:
            return None

        content_type = response.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            return response.json()
        return response.text

    async def get_status(self) -> dict[str, Any]:
        """Return configuration and live profile status for the Gmail integration."""
        status: dict[str, Any] = {
            "configured": self.is_configured(),
            "ready": False,
            "scopes": self.scopes,
            "actions": [
                "read_recent_messages",
                "read_message_detail",
                "archive_message",
                "mark_message_read",
                "send_message",
            ],
        }

        if not status["configured"]:
            status["detail"] = (
                "Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and "
                "GOOGLE_REFRESH_TOKEN to enable Gmail autonomy."
            )
            return status

        try:
            profile = await self._request("GET", "/profile")
        except GmailAPIError as exc:
            status["detail"] = str(exc)
            status["error"] = exc.details
            return status

        status["ready"] = True
        status["email_address"] = profile.get("emailAddress")
        status["messages_total"] = profile.get("messagesTotal")
        status["threads_total"] = profile.get("threadsTotal")
        status["history_id"] = profile.get("historyId")
        return status

    async def list_messages(
        self,
        *,
        limit: int = 10,
        query: str = "in:inbox",
    ) -> dict[str, Any]:
        """List recent Gmail messages matching a search query."""
        bounded_limit = max(1, min(limit, 25))
        payload = await self._request(
            "GET",
            "/messages",
            params={"maxResults": bounded_limit, "q": query},
        )
        message_refs = payload.get("messages", []) if isinstance(payload, dict) else []
        if not message_refs:
            return {
                "query": query,
                "count": 0,
                "messages": [],
                "result_size_estimate": payload.get("resultSizeEstimate", 0),
            }

        messages = await asyncio.gather(
            *[
                self.get_message_summary(str(message_ref["id"]))
                for message_ref in message_refs
                if isinstance(message_ref, dict) and message_ref.get("id")
            ]
        )
        return {
            "query": query,
            "count": len(messages),
            "messages": messages,
            "result_size_estimate": payload.get("resultSizeEstimate", len(messages)),
        }

    async def get_message_summary(self, message_id: str) -> dict[str, Any]:
        """Fetch a compact message summary for inbox triage."""
        payload = await self._request(
            "GET",
            f"/messages/{message_id}",
            params=[
                ("format", "metadata"),
                ("metadataHeaders", "From"),
                ("metadataHeaders", "To"),
                ("metadataHeaders", "Subject"),
                ("metadataHeaders", "Date"),
            ],
        )

        gmail_payload = payload.get("payload", {}) if isinstance(payload, dict) else {}
        headers = (
            gmail_payload.get("headers", []) if isinstance(gmail_payload, dict) else []
        )
        label_ids = payload.get("labelIds", []) if isinstance(payload, dict) else []

        return {
            "id": payload.get("id"),
            "thread_id": payload.get("threadId"),
            "history_id": payload.get("historyId"),
            "internal_date": payload.get("internalDate"),
            "snippet": payload.get("snippet"),
            "subject": _extract_header(headers, "Subject"),
            "from": _extract_header(headers, "From"),
            "to": _extract_header(headers, "To"),
            "date": _extract_header(headers, "Date"),
            "label_ids": label_ids,
            "unread": "UNREAD" in label_ids,
            "in_inbox": "INBOX" in label_ids,
        }

    async def get_message(self, message_id: str) -> dict[str, Any]:
        """Fetch a detailed Gmail message body for summarization or reply drafting."""
        payload = await self._request(
            "GET",
            f"/messages/{message_id}",
            params={"format": "full"},
        )
        gmail_payload = payload.get("payload", {}) if isinstance(payload, dict) else {}
        headers = (
            gmail_payload.get("headers", []) if isinstance(gmail_payload, dict) else []
        )
        bodies = _extract_message_bodies(gmail_payload)

        return {
            "id": payload.get("id"),
            "thread_id": payload.get("threadId"),
            "history_id": payload.get("historyId"),
            "internal_date": payload.get("internalDate"),
            "snippet": payload.get("snippet"),
            "label_ids": payload.get("labelIds", []),
            "headers": {
                "subject": _extract_header(headers, "Subject"),
                "from": _extract_header(headers, "From"),
                "to": _extract_header(headers, "To"),
                "cc": _extract_header(headers, "Cc"),
                "date": _extract_header(headers, "Date"),
                "message_id": _extract_header(headers, "Message-ID"),
            },
            "body": bodies,
        }

    async def archive_message(self, message_id: str) -> dict[str, Any]:
        """Archive a Gmail message by removing the INBOX label."""
        payload = await self._request(
            "POST",
            f"/messages/{message_id}/modify",
            json={"removeLabelIds": ["INBOX"]},
        )
        return {
            "message_id": message_id,
            "archived": True,
            "label_ids": payload.get("labelIds", []),
        }

    async def mark_message_read(self, message_id: str) -> dict[str, Any]:
        """Mark a Gmail message as read by removing the UNREAD label."""
        payload = await self._request(
            "POST",
            f"/messages/{message_id}/modify",
            json={"removeLabelIds": ["UNREAD"]},
        )
        return {
            "message_id": message_id,
            "read": True,
            "label_ids": payload.get("labelIds", []),
        }

    async def send_message(
        self,
        *,
        to: str,
        subject: str,
        body: str,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        thread_id: str | None = None,
        in_reply_to: str | None = None,
    ) -> dict[str, Any]:
        """Send an outbound Gmail message from the connected account."""
        message = EmailMessage()
        message["To"] = to
        message["Subject"] = subject
        if cc:
            message["Cc"] = ", ".join(cc)
        if bcc:
            message["Bcc"] = ", ".join(bcc)
        if in_reply_to:
            message["In-Reply-To"] = in_reply_to
            message["References"] = in_reply_to
        message.set_content(body)

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        send_payload: dict[str, Any] = {"raw": raw_message}
        if thread_id:
            send_payload["threadId"] = thread_id

        payload = await self._request("POST", "/messages/send", json=send_payload)
        return {
            "id": payload.get("id"),
            "thread_id": payload.get("threadId"),
            "label_ids": payload.get("labelIds", []),
        }


def get_gmail_service() -> GmailService:
    """Construct a Gmail service using the active settings."""
    return GmailService()
