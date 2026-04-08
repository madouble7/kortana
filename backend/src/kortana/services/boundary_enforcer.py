"""V22C — boundary enforcer: proves the system stayed inside constitutional limits."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from kortana.services.constitution import (
    Constitution,
    PolicyClassification,
    Sensitivity,
    ViolationSeverity,
    get_constitution,
)
from kortana.services.proposal_registry import PolicyProposal


@dataclass
class BoundaryViolation:
    """A single constitutional boundary violation."""

    article_id: str
    article_title: str
    severity: ViolationSeverity
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "article_id": self.article_id,
            "article_title": self.article_title,
            "severity": self.severity.value,
            "description": self.description,
        }


@dataclass
class BoundaryWarning:
    """A non-blocking warning about constitutional proximity."""

    article_id: str
    article_title: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "article_id": self.article_id,
            "article_title": self.article_title,
            "message": self.message,
        }


@dataclass
class BoundaryCheck:
    """Result of checking a proposal against constitutional boundaries."""

    check_id: str
    proposal_id: str
    passed: bool
    violations: list[BoundaryViolation]
    warnings: list[BoundaryWarning]
    articles_checked: int
    policy_area: str
    classification: str
    sensitivity: str
    checked_at: str = ""
    check_hash: str = ""

    def __post_init__(self) -> None:
        if not self.checked_at:
            self.checked_at = datetime.now(timezone.utc).isoformat()
        if not self.check_hash:
            blob = f"{self.check_id}:{self.proposal_id}:{self.passed}:{len(self.violations)}"
            self.check_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "proposal_id": self.proposal_id,
            "passed": self.passed,
            "violations": [v.to_dict() for v in self.violations],
            "warnings": [w.to_dict() for w in self.warnings],
            "articles_checked": self.articles_checked,
            "policy_area": self.policy_area,
            "classification": self.classification,
            "sensitivity": self.sensitivity,
            "checked_at": self.checked_at,
            "check_hash": self.check_hash,
        }


class BoundaryEnforcer:
    """Enforces constitutional boundaries during policy evolution."""

    def __init__(self, constitution: Constitution | None = None) -> None:
        self._constitution = constitution or get_constitution()
        self._checks: list[BoundaryCheck] = []

    def check_proposal(self, proposal: PolicyProposal) -> BoundaryCheck:
        """Check a proposal against all applicable constitutional articles."""
        area = proposal.policy_area
        articles = self._constitution.get_articles_for_area(area)
        classification = self._constitution.get_classification(area)
        sensitivity = self._constitution.get_sensitivity(area)

        violations: list[BoundaryViolation] = []
        warnings: list[BoundaryWarning] = []

        # Check 1: Immutable areas cannot be changed
        if classification == PolicyClassification.IMMUTABLE:
            for art in articles:
                if art.classification == PolicyClassification.IMMUTABLE:
                    violations.append(BoundaryViolation(
                        article_id=art.article_id,
                        article_title=art.title,
                        severity=art.violation_severity,
                        description=f"Policy area '{area.value}' is immutable: {art.boundary_rule}",
                    ))

        # Check 2: Restricted areas generate warnings
        if classification == PolicyClassification.RESTRICTED:
            for art in articles:
                if art.classification == PolicyClassification.RESTRICTED:
                    warnings.append(BoundaryWarning(
                        article_id=art.article_id,
                        article_title=art.title,
                        message=f"Restricted area requires quorum: {art.boundary_rule}",
                    ))

        # Check 3: Low confidence on high-sensitivity changes
        if sensitivity in (Sensitivity.CRITICAL, Sensitivity.HIGH) and proposal.confidence < 0.7:
            for art in articles:
                warnings.append(BoundaryWarning(
                    article_id=art.article_id,
                    article_title=art.title,
                    message=f"Low confidence ({proposal.confidence:.2f}) on {sensitivity.value}-sensitivity area",
                ))

        passed = len(violations) == 0

        check = BoundaryCheck(
            check_id=f"bc-{uuid.uuid4().hex[:12]}",
            proposal_id=proposal.proposal_id,
            passed=passed,
            violations=violations,
            warnings=warnings,
            articles_checked=len(articles),
            policy_area=area.value,
            classification=classification.value,
            sensitivity=sensitivity.value,
        )
        self._checks.append(check)
        return check

    def validate_evolution_batch(self, proposals: list[PolicyProposal]) -> dict[str, Any]:
        """Validate a batch of proposals and return aggregate results."""
        results: list[BoundaryCheck] = []
        for p in proposals:
            results.append(self.check_proposal(p))

        all_passed = all(r.passed for r in results)
        total_violations = sum(len(r.violations) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)

        return {
            "all_passed": all_passed,
            "total_proposals": len(proposals),
            "passed_count": sum(1 for r in results if r.passed),
            "blocked_count": sum(1 for r in results if not r.passed),
            "total_violations": total_violations,
            "total_warnings": total_warnings,
            "checks": [r.to_dict() for r in results],
        }

    def get_checks(self, proposal_id: str | None = None) -> list[BoundaryCheck]:
        if proposal_id is None:
            return list(self._checks)
        return [c for c in self._checks if c.proposal_id == proposal_id]

    def get_violation_summary(self) -> dict[str, Any]:
        """Summarize all violations across all checks."""
        total = 0
        by_severity: dict[str, int] = {}
        for check in self._checks:
            for v in check.violations:
                total += 1
                key = v.severity.value
                by_severity[key] = by_severity.get(key, 0) + 1
        return {
            "total_violations": total,
            "by_severity": by_severity,
            "total_checks": len(self._checks),
            "pass_rate": sum(1 for c in self._checks if c.passed) / max(len(self._checks), 1),
        }

    @property
    def check_count(self) -> int:
        return len(self._checks)


_enforcer: BoundaryEnforcer | None = None


def get_boundary_enforcer() -> BoundaryEnforcer:
    """Module singleton."""
    global _enforcer
    if _enforcer is None:
        _enforcer = BoundaryEnforcer()
    return _enforcer
