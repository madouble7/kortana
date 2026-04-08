"""V22A — constitution: immutable vs amendable policy classes with hard boundaries."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from kortana.services.policy_feedback_loop import PolicyArea


class PolicyClassification(Enum):
    """Whether a policy area can be modified by the learning system."""

    IMMUTABLE = "immutable"
    AMENDABLE = "amendable"
    RESTRICTED = "restricted"


class Sensitivity(Enum):
    """How sensitive a policy area is to autonomous changes."""

    CRITICAL = "critical"
    HIGH = "high"
    STANDARD = "standard"
    LOW = "low"


class ViolationSeverity(Enum):
    """Severity when a constitutional boundary is violated."""

    FATAL = "fatal"
    MAJOR = "major"
    MINOR = "minor"
    WARNING = "warning"


@dataclass
class ConstitutionalArticle:
    """A single rule in the governance constitution."""

    article_id: str
    title: str
    policy_area: PolicyArea
    classification: PolicyClassification
    sensitivity: Sensitivity
    boundary_rule: str
    violation_severity: ViolationSeverity
    rationale: str
    created_at: str = ""
    article_hash: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.article_hash:
            blob = f"{self.article_id}:{self.title}:{self.policy_area.value}:{self.classification.value}"
            self.article_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "article_id": self.article_id,
            "title": self.title,
            "policy_area": self.policy_area.value,
            "classification": self.classification.value,
            "sensitivity": self.sensitivity.value,
            "boundary_rule": self.boundary_rule,
            "violation_severity": self.violation_severity.value,
            "rationale": self.rationale,
            "created_at": self.created_at,
            "article_hash": self.article_hash,
        }


# Default constitutional articles
_DEFAULT_ARTICLES: list[dict[str, Any]] = [
    {
        "title": "Security actions require human approval",
        "policy_area": PolicyArea.GOVERNANCE,
        "classification": PolicyClassification.IMMUTABLE,
        "sensitivity": Sensitivity.CRITICAL,
        "boundary_rule": "security_action policy cannot be auto-amended",
        "violation_severity": ViolationSeverity.FATAL,
        "rationale": "Security policy changes must always involve human oversight",
    },
    {
        "title": "Autonomy expansion requires high trust",
        "policy_area": PolicyArea.AUTONOMY,
        "classification": PolicyClassification.RESTRICTED,
        "sensitivity": Sensitivity.HIGH,
        "boundary_rule": "autonomy thresholds cannot increase beyond 1.5x baseline without quorum",
        "violation_severity": ViolationSeverity.MAJOR,
        "rationale": "Expanding autonomy beyond safe limits requires institutional consensus",
    },
    {
        "title": "Escalation paths must remain available",
        "policy_area": PolicyArea.ESCALATION,
        "classification": PolicyClassification.RESTRICTED,
        "sensitivity": Sensitivity.HIGH,
        "boundary_rule": "escalation rules cannot be removed or disabled by learning",
        "violation_severity": ViolationSeverity.MAJOR,
        "rationale": "Human escalation paths are a safety net that cannot be eliminated",
    },
    {
        "title": "Rollout windows are amendable",
        "policy_area": PolicyArea.ROLLOUT,
        "classification": PolicyClassification.AMENDABLE,
        "sensitivity": Sensitivity.STANDARD,
        "boundary_rule": "rollout timing can be adjusted within 10-120 minute range",
        "violation_severity": ViolationSeverity.MINOR,
        "rationale": "Rollout timing is operational and safe to optimize",
    },
    {
        "title": "Retry counts are amendable",
        "policy_area": PolicyArea.RETRY,
        "classification": PolicyClassification.AMENDABLE,
        "sensitivity": Sensitivity.LOW,
        "boundary_rule": "retry counts can be adjusted within 1-10 range",
        "violation_severity": ViolationSeverity.WARNING,
        "rationale": "Retry tuning is low-risk and benefits from learning",
    },
    {
        "title": "Priority rules are amendable",
        "policy_area": PolicyArea.PRIORITY,
        "classification": PolicyClassification.AMENDABLE,
        "sensitivity": Sensitivity.STANDARD,
        "boundary_rule": "priority ordering can be adjusted by learning",
        "violation_severity": ViolationSeverity.MINOR,
        "rationale": "Priority adjustments improve efficiency without safety risk",
    },
]


class Constitution:
    """Defines the governance constitution: what can and cannot be changed."""

    def __init__(self, load_defaults: bool = True) -> None:
        self._articles: dict[str, ConstitutionalArticle] = {}
        if load_defaults:
            self._load_defaults()

    def _load_defaults(self) -> None:
        for i, spec in enumerate(_DEFAULT_ARTICLES):
            article = ConstitutionalArticle(
                article_id=f"art-{i + 1:03d}",
                **spec,
            )
            self._articles[article.article_id] = article

    def add_article(self, article: ConstitutionalArticle) -> None:
        self._articles[article.article_id] = article

    def get_article(self, article_id: str) -> ConstitutionalArticle | None:
        return self._articles.get(article_id)

    def get_articles(self) -> list[ConstitutionalArticle]:
        return list(self._articles.values())

    def get_articles_for_area(self, area: PolicyArea) -> list[ConstitutionalArticle]:
        return [a for a in self._articles.values() if a.policy_area == area]

    def get_classification(self, area: PolicyArea) -> PolicyClassification:
        """Get the most restrictive classification for a policy area."""
        articles = self.get_articles_for_area(area)
        if not articles:
            return PolicyClassification.AMENDABLE
        order = {
            PolicyClassification.IMMUTABLE: 0,
            PolicyClassification.RESTRICTED: 1,
            PolicyClassification.AMENDABLE: 2,
        }
        return min((a.classification for a in articles), key=lambda c: order[c])

    def get_sensitivity(self, area: PolicyArea) -> Sensitivity:
        """Get the highest sensitivity for a policy area."""
        articles = self.get_articles_for_area(area)
        if not articles:
            return Sensitivity.STANDARD
        order = {
            Sensitivity.CRITICAL: 0,
            Sensitivity.HIGH: 1,
            Sensitivity.STANDARD: 2,
            Sensitivity.LOW: 3,
        }
        return min((a.sensitivity for a in articles), key=lambda s: order[s])

    def is_immutable(self, area: PolicyArea) -> bool:
        return self.get_classification(area) == PolicyClassification.IMMUTABLE

    def is_restricted(self, area: PolicyArea) -> bool:
        return self.get_classification(area) == PolicyClassification.RESTRICTED

    def is_amendable(self, area: PolicyArea) -> bool:
        return self.get_classification(area) == PolicyClassification.AMENDABLE

    @property
    def article_count(self) -> int:
        return len(self._articles)

    def get_summary(self) -> dict[str, Any]:
        by_class: dict[str, int] = {}
        by_sensitivity: dict[str, int] = {}
        for a in self._articles.values():
            by_class[a.classification.value] = by_class.get(a.classification.value, 0) + 1
            by_sensitivity[a.sensitivity.value] = by_sensitivity.get(a.sensitivity.value, 0) + 1
        return {
            "total_articles": self.article_count,
            "by_classification": by_class,
            "by_sensitivity": by_sensitivity,
        }


_constitution: Constitution | None = None


def get_constitution() -> Constitution:
    """Module singleton."""
    global _constitution
    if _constitution is None:
        _constitution = Constitution()
    return _constitution
