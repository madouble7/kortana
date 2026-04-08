"""V23D — precedent tracker: case law for constitutional adjudication."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from src.kortana.services.policy_feedback_loop import PolicyArea


class DecisionType(Enum):
    """Type of adjudication decision that creates precedent."""

    WAIVER_GRANTED = "waiver_granted"
    WAIVER_DENIED = "waiver_denied"
    APPEAL_UPHELD = "appeal_upheld"
    APPEAL_OVERTURNED = "appeal_overturned"
    APPEAL_REMANDED = "appeal_remanded"
    EMERGENCY_DECLARED = "emergency_declared"
    EMERGENCY_REVIEWED = "emergency_reviewed"
    BOUNDARY_EXCEPTION = "boundary_exception"


class PrecedentStrength(Enum):
    """How strongly a precedent influences future decisions."""

    BINDING = "binding"
    PERSUASIVE = "persuasive"
    INFORMATIONAL = "informational"


@dataclass
class CitedArticle:
    """An article cited in a precedent decision."""

    article_id: str
    relevance: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "article_id": self.article_id,
            "relevance": self.relevance,
        }


@dataclass
class Precedent:
    """A recorded decision that informs future adjudication."""

    precedent_id: str
    decision_type: DecisionType
    reference_id: str
    policy_area: PolicyArea
    decision_summary: str
    reasoning: str
    outcome: str
    strength: PrecedentStrength
    cited_articles: list[CitedArticle] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    superseded_by: str | None = None
    created_at: str = ""
    precedent_hash: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.precedent_hash:
            blob = f"{self.precedent_id}:{self.decision_type.value}:{self.policy_area.value}:{self.decision_summary}"
            self.precedent_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]

    @property
    def is_active(self) -> bool:
        return self.superseded_by is None

    def to_dict(self) -> dict[str, Any]:
        return {
            "precedent_id": self.precedent_id,
            "decision_type": self.decision_type.value,
            "reference_id": self.reference_id,
            "policy_area": self.policy_area.value,
            "decision_summary": self.decision_summary,
            "reasoning": self.reasoning,
            "outcome": self.outcome,
            "strength": self.strength.value,
            "cited_articles": [c.to_dict() for c in self.cited_articles],
            "tags": self.tags,
            "superseded_by": self.superseded_by,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "precedent_hash": self.precedent_hash,
        }


class PrecedentTracker:
    """Records and retrieves adjudication precedents — the system's case law."""

    def __init__(self) -> None:
        self._precedents: list[Precedent] = []

    def record_precedent(
        self,
        decision_type: DecisionType,
        reference_id: str,
        policy_area: PolicyArea,
        decision_summary: str,
        reasoning: str,
        outcome: str,
        strength: PrecedentStrength = PrecedentStrength.PERSUASIVE,
        cited_articles: list[CitedArticle] | None = None,
        tags: list[str] | None = None,
    ) -> Precedent:
        """Record a new precedent from an adjudication decision."""
        precedent = Precedent(
            precedent_id=f"prec-{uuid.uuid4().hex[:12]}",
            decision_type=decision_type,
            reference_id=reference_id,
            policy_area=policy_area,
            decision_summary=decision_summary,
            reasoning=reasoning,
            outcome=outcome,
            strength=strength,
            cited_articles=cited_articles or [],
            tags=tags or [],
        )
        self._precedents.append(precedent)
        return precedent

    def supersede(self, old_precedent_id: str, new_precedent_id: str) -> bool:
        """Mark an old precedent as superseded by a new one."""
        for p in self._precedents:
            if p.precedent_id == old_precedent_id and p.is_active:
                p.superseded_by = new_precedent_id
                return True
        return False

    def find_precedents(
        self,
        policy_area: PolicyArea | None = None,
        decision_type: DecisionType | None = None,
        strength: PrecedentStrength | None = None,
        tag: str | None = None,
        active_only: bool = True,
    ) -> list[Precedent]:
        """Search precedents by criteria."""
        result = list(self._precedents)
        if active_only:
            result = [p for p in result if p.is_active]
        if policy_area is not None:
            result = [p for p in result if p.policy_area == policy_area]
        if decision_type is not None:
            result = [p for p in result if p.decision_type == decision_type]
        if strength is not None:
            result = [p for p in result if p.strength == strength]
        if tag is not None:
            result = [p for p in result if tag in p.tags]
        return result

    def get_precedent(self, precedent_id: str) -> Precedent | None:
        for p in self._precedents:
            if p.precedent_id == precedent_id:
                return p
        return None

    def get_binding_precedents(self, policy_area: PolicyArea) -> list[Precedent]:
        """Get binding precedents for an area — these must be followed."""
        return self.find_precedents(
            policy_area=policy_area,
            strength=PrecedentStrength.BINDING,
            active_only=True,
        )

    def check_conflicts(self, policy_area: PolicyArea, proposed_outcome: str) -> list[Precedent]:
        """Check if a proposed outcome conflicts with binding precedents."""
        binding = self.get_binding_precedents(policy_area)
        conflicts: list[Precedent] = []
        for p in binding:
            if p.outcome != proposed_outcome:
                conflicts.append(p)
        return conflicts

    @property
    def precedent_count(self) -> int:
        return len(self._precedents)

    @property
    def active_count(self) -> int:
        return sum(1 for p in self._precedents if p.is_active)

    @property
    def binding_count(self) -> int:
        return sum(1 for p in self._precedents if p.strength == PrecedentStrength.BINDING and p.is_active)

    def get_summary(self) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        by_strength: dict[str, int] = {}
        by_area: dict[str, int] = {}
        for p in self._precedents:
            if p.is_active:
                by_type[p.decision_type.value] = by_type.get(p.decision_type.value, 0) + 1
                by_strength[p.strength.value] = by_strength.get(p.strength.value, 0) + 1
                by_area[p.policy_area.value] = by_area.get(p.policy_area.value, 0) + 1
        return {
            "total_precedents": len(self._precedents),
            "active": self.active_count,
            "binding": self.binding_count,
            "by_type": by_type,
            "by_strength": by_strength,
            "by_area": by_area,
        }


_tracker: PrecedentTracker | None = None


def get_precedent_tracker() -> PrecedentTracker:
    """Module singleton."""
    global _tracker
    if _tracker is None:
        _tracker = PrecedentTracker()
    return _tracker
