"""V25C — notice service: formal notification requirements for proceedings."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class NoticeType(Enum):
    """Types of procedural notices."""

    CASE_OPENED = "case_opened"
    DEADLINE_APPROACHING = "deadline_approaching"
    DEADLINE_MISSED = "deadline_missed"
    DECISION_RENDERED = "decision_rendered"
    RECUSAL_REQUIRED = "recusal_required"
    REASONING_PUBLISHED = "reasoning_published"
    STATUS_CHANGED = "status_changed"
    CASE_CLOSED = "case_closed"


class DeliveryStatus(Enum):
    """Status of notice delivery."""

    PENDING = "pending"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"


@dataclass
class Notice:
    """A formal procedural notice."""

    notice_id: str
    case_number: str
    notice_type: NoticeType
    recipient: str
    subject: str
    body: str
    delivery_status: DeliveryStatus = DeliveryStatus.PENDING
    sent_at: str = ""
    delivered_at: str = ""
    acknowledged_at: str = ""
    notice_hash: str = ""

    def __post_init__(self) -> None:
        if not self.sent_at:
            self.sent_at = datetime.now(timezone.utc).isoformat()
        if not self.notice_hash:
            blob = f"{self.notice_id}:{self.case_number}:{self.notice_type.value}:{self.recipient}"
            self.notice_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "notice_id": self.notice_id,
            "case_number": self.case_number,
            "notice_type": self.notice_type.value,
            "recipient": self.recipient,
            "subject": self.subject,
            "body": self.body,
            "delivery_status": self.delivery_status.value,
            "sent_at": self.sent_at,
            "delivered_at": self.delivered_at,
            "acknowledged_at": self.acknowledged_at,
            "notice_hash": self.notice_hash,
        }


class NoticeService:
    """Manages formal notice requirements for constitutional proceedings."""

    def __init__(self) -> None:
        self._notices: list[Notice] = []

    def send_notice(
        self,
        case_number: str,
        notice_type: NoticeType,
        recipient: str,
        subject: str,
        body: str,
    ) -> Notice:
        """Send a formal notice to a party."""
        notice = Notice(
            notice_id=f"ntc-{uuid.uuid4().hex[:12]}",
            case_number=case_number,
            notice_type=notice_type,
            recipient=recipient,
            subject=subject,
            body=body,
        )
        self._notices.append(notice)
        return notice

    def notify_parties(
        self,
        case_number: str,
        notice_type: NoticeType,
        parties: list[str],
        subject: str,
        body: str,
    ) -> list[Notice]:
        """Send a notice to multiple parties at once."""
        notices = []
        for party in parties:
            n = self.send_notice(case_number, notice_type, party, subject, body)
            notices.append(n)
        return notices

    def mark_delivered(self, notice_id: str) -> bool:
        """Mark a notice as delivered."""
        for n in self._notices:
            if n.notice_id == notice_id and n.delivery_status == DeliveryStatus.PENDING:
                n.delivery_status = DeliveryStatus.DELIVERED
                n.delivered_at = datetime.now(timezone.utc).isoformat()
                return True
        return False

    def mark_acknowledged(self, notice_id: str) -> bool:
        """Mark a notice as acknowledged by the recipient."""
        for n in self._notices:
            if n.notice_id == notice_id and n.delivery_status in (
                DeliveryStatus.PENDING, DeliveryStatus.DELIVERED
            ):
                n.delivery_status = DeliveryStatus.ACKNOWLEDGED
                now = datetime.now(timezone.utc).isoformat()
                if not n.delivered_at:
                    n.delivered_at = now
                n.acknowledged_at = now
                return True
        return False

    def mark_failed(self, notice_id: str) -> bool:
        """Mark a notice delivery as failed."""
        for n in self._notices:
            if n.notice_id == notice_id and n.delivery_status == DeliveryStatus.PENDING:
                n.delivery_status = DeliveryStatus.FAILED
                return True
        return False

    def get_notice(self, notice_id: str) -> Notice | None:
        for n in self._notices:
            if n.notice_id == notice_id:
                return n
        return None

    def get_notices(
        self,
        case_number: str | None = None,
        recipient: str | None = None,
        notice_type: NoticeType | None = None,
        status: DeliveryStatus | None = None,
    ) -> list[Notice]:
        """Get notices with optional filters."""
        result = list(self._notices)
        if case_number is not None:
            result = [n for n in result if n.case_number == case_number]
        if recipient is not None:
            result = [n for n in result if n.recipient == recipient]
        if notice_type is not None:
            result = [n for n in result if n.notice_type == notice_type]
        if status is not None:
            result = [n for n in result if n.delivery_status == status]
        return result

    def get_unacknowledged(self, recipient: str | None = None) -> list[Notice]:
        """Get notices not yet acknowledged."""
        result = [
            n for n in self._notices
            if n.delivery_status != DeliveryStatus.ACKNOWLEDGED
        ]
        if recipient is not None:
            result = [n for n in result if n.recipient == recipient]
        return result

    @property
    def notice_count(self) -> int:
        return len(self._notices)

    @property
    def pending_count(self) -> int:
        return sum(1 for n in self._notices if n.delivery_status == DeliveryStatus.PENDING)

    @property
    def acknowledged_count(self) -> int:
        return sum(1 for n in self._notices if n.delivery_status == DeliveryStatus.ACKNOWLEDGED)

    def get_summary(self) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        by_recipient: dict[str, int] = {}
        for n in self._notices:
            by_type[n.notice_type.value] = by_type.get(n.notice_type.value, 0) + 1
            by_status[n.delivery_status.value] = by_status.get(n.delivery_status.value, 0) + 1
            by_recipient[n.recipient] = by_recipient.get(n.recipient, 0) + 1
        return {
            "total_notices": len(self._notices),
            "pending": self.pending_count,
            "acknowledged": self.acknowledged_count,
            "by_type": by_type,
            "by_status": by_status,
            "by_recipient": by_recipient,
        }


_service: NoticeService | None = None


def get_notice_service() -> NoticeService:
    """Module singleton."""
    global _service
    if _service is None:
        _service = NoticeService()
    return _service
