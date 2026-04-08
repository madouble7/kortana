"""V25D — decision registry: searchable public record of constitutional decisions."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class DecisionOutcome(Enum):
    """Possible outcomes of a constitutional decision."""

    APPROVED = "approved"
    DENIED = "denied"
    UPHELD = "upheld"
    OVERTURNED = "overturned"
    REMANDED = "remanded"
    DISMISSED = "dismissed"
    GRANTED = "granted"
    REVOKED = "revoked"
    MODIFIED = "modified"


@dataclass
class DecisionRecord:
    """A final, searchable record of a constitutional decision."""

    decision_id: str
    case_number: str
    decision_type: str
    outcome: DecisionOutcome
    summary: str
    policy_area: str = ""
    parties: list[str] = field(default_factory=list)
    reasoning_id: str = ""
    cited_articles: list[str] = field(default_factory=list)
    cited_precedents: list[str] = field(default_factory=list)
    decided_by: str = ""
    decided_at: str = ""
    tags: list[str] = field(default_factory=list)
    decision_hash: str = ""

    def __post_init__(self) -> None:
        if not self.decided_at:
            self.decided_at = datetime.now(timezone.utc).isoformat()
        if not self.decision_hash:
            blob = f"{self.decision_id}:{self.case_number}:{self.outcome.value}"
            self.decision_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "case_number": self.case_number,
            "decision_type": self.decision_type,
            "outcome": self.outcome.value,
            "summary": self.summary,
            "policy_area": self.policy_area,
            "parties": self.parties,
            "reasoning_id": self.reasoning_id,
            "cited_articles": self.cited_articles,
            "cited_precedents": self.cited_precedents,
            "decided_by": self.decided_by,
            "decided_at": self.decided_at,
            "tags": self.tags,
            "decision_hash": self.decision_hash,
        }


class DecisionRegistry:
    """Searchable public registry of constitutional decisions."""

    def __init__(self) -> None:
        self._decisions: list[DecisionRecord] = []

    def record_decision(
        self,
        case_number: str,
        decision_type: str,
        outcome: DecisionOutcome,
        summary: str,
        policy_area: str = "",
        parties: list[str] | None = None,
        reasoning_id: str = "",
        cited_articles: list[str] | None = None,
        cited_precedents: list[str] | None = None,
        decided_by: str = "",
        tags: list[str] | None = None,
    ) -> DecisionRecord:
        """Record a final decision in the public registry."""
        record = DecisionRecord(
            decision_id=f"dec-{uuid.uuid4().hex[:12]}",
            case_number=case_number,
            decision_type=decision_type,
            outcome=outcome,
            summary=summary,
            policy_area=policy_area,
            parties=parties or [],
            reasoning_id=reasoning_id,
            cited_articles=cited_articles or [],
            cited_precedents=cited_precedents or [],
            decided_by=decided_by,
            tags=tags or [],
        )
        self._decisions.append(record)
        return record

    def get_decision(self, decision_id: str) -> DecisionRecord | None:
        for d in self._decisions:
            if d.decision_id == decision_id:
                return d
        return None

    def get_by_case(self, case_number: str) -> list[DecisionRecord]:
        return [d for d in self._decisions if d.case_number == case_number]

    def search(
        self,
        decision_type: str | None = None,
        outcome: DecisionOutcome | None = None,
        policy_area: str | None = None,
        decided_by: str | None = None,
        party: str | None = None,
        tag: str | None = None,
        query: str | None = None,
    ) -> list[DecisionRecord]:
        """Full-text and faceted search across decisions."""
        result = list(self._decisions)
        if decision_type is not None:
            result = [d for d in result if d.decision_type == decision_type]
        if outcome is not None:
            result = [d for d in result if d.outcome == outcome]
        if policy_area is not None:
            result = [d for d in result if d.policy_area == policy_area]
        if decided_by is not None:
            result = [d for d in result if d.decided_by == decided_by]
        if party is not None:
            result = [d for d in result if party in d.parties]
        if tag is not None:
            result = [d for d in result if tag in d.tags]
        if query is not None:
            q = query.lower()
            result = [
                d for d in result
                if q in d.summary.lower()
                or q in d.policy_area.lower()
                or q in d.decision_type.lower()
                or any(q in a.lower() for a in d.cited_articles)
                or any(q in t.lower() for t in d.tags)
            ]
        return result

    @property
    def decision_count(self) -> int:
        return len(self._decisions)

    def get_summary(self) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        by_outcome: dict[str, int] = {}
        by_area: dict[str, int] = {}
        for d in self._decisions:
            by_type[d.decision_type] = by_type.get(d.decision_type, 0) + 1
            by_outcome[d.outcome.value] = by_outcome.get(d.outcome.value, 0) + 1
            if d.policy_area:
                by_area[d.policy_area] = by_area.get(d.policy_area, 0) + 1
        return {
            "total_decisions": len(self._decisions),
            "by_type": by_type,
            "by_outcome": by_outcome,
            "by_policy_area": by_area,
        }


_registry: DecisionRegistry | None = None


def get_decision_registry() -> DecisionRegistry:
    """Module singleton."""
    global _registry
    if _registry is None:
        _registry = DecisionRegistry()
    return _registry
