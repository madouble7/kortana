"""V22D — constitutional audit: compliance proofs and violation tracking."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from src.kortana.services.boundary_enforcer import BoundaryCheck
from src.kortana.services.constitution import ViolationSeverity


@dataclass
class ComplianceProof:
    """Proof that a proposal underwent constitutional review and passed."""

    proof_id: str
    proposal_id: str
    all_checks_passed: bool
    checks_performed: int
    violations_found: int
    warnings_found: int
    boundary_checks: list[str]
    issued_at: str = ""
    proof_hash: str = ""

    def __post_init__(self) -> None:
        if not self.issued_at:
            self.issued_at = datetime.now(timezone.utc).isoformat()
        if not self.proof_hash:
            blob = f"{self.proof_id}:{self.proposal_id}:{self.all_checks_passed}:{self.checks_performed}"
            self.proof_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "proof_id": self.proof_id,
            "proposal_id": self.proposal_id,
            "all_checks_passed": self.all_checks_passed,
            "checks_performed": self.checks_performed,
            "violations_found": self.violations_found,
            "warnings_found": self.warnings_found,
            "boundary_checks": self.boundary_checks,
            "issued_at": self.issued_at,
            "proof_hash": self.proof_hash,
        }


@dataclass
class ViolationRecord:
    """Persistent record of a constitutional violation."""

    violation_id: str
    article_id: str
    proposal_id: str
    severity: ViolationSeverity
    description: str
    recorded_at: str = ""
    resolved: bool = False
    resolution_notes: str = ""
    violation_hash: str = ""

    def __post_init__(self) -> None:
        if not self.recorded_at:
            self.recorded_at = datetime.now(timezone.utc).isoformat()
        if not self.violation_hash:
            blob = f"{self.violation_id}:{self.article_id}:{self.proposal_id}:{self.severity.value}"
            self.violation_hash = hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "violation_id": self.violation_id,
            "article_id": self.article_id,
            "proposal_id": self.proposal_id,
            "severity": self.severity.value,
            "description": self.description,
            "recorded_at": self.recorded_at,
            "resolved": self.resolved,
            "resolution_notes": self.resolution_notes,
            "violation_hash": self.violation_hash,
        }


class ConstitutionalAudit:
    """Tracks compliance proofs, violations, and generates reports."""

    def __init__(self) -> None:
        self._proofs: list[ComplianceProof] = []
        self._violations: list[ViolationRecord] = []

    def record_check(self, check: BoundaryCheck) -> ComplianceProof:
        """Record a boundary check and issue a compliance proof."""
        # Record violations
        for v in check.violations:
            record = ViolationRecord(
                violation_id=f"viol-{uuid.uuid4().hex[:12]}",
                article_id=v.article_id,
                proposal_id=check.proposal_id,
                severity=v.severity,
                description=v.description,
            )
            self._violations.append(record)

        # Issue compliance proof
        proof = ComplianceProof(
            proof_id=f"proof-{uuid.uuid4().hex[:12]}",
            proposal_id=check.proposal_id,
            all_checks_passed=check.passed,
            checks_performed=check.articles_checked,
            violations_found=len(check.violations),
            warnings_found=len(check.warnings),
            boundary_checks=[check.check_id],
        )
        self._proofs.append(proof)
        return proof

    def resolve_violation(self, violation_id: str, notes: str = "") -> bool:
        """Mark a violation as resolved."""
        for v in self._violations:
            if v.violation_id == violation_id:
                v.resolved = True
                v.resolution_notes = notes
                return True
        return False

    def get_proofs(self, proposal_id: str | None = None) -> list[ComplianceProof]:
        if proposal_id is None:
            return list(self._proofs)
        return [p for p in self._proofs if p.proposal_id == proposal_id]

    def get_violations(
        self,
        proposal_id: str | None = None,
        severity: ViolationSeverity | None = None,
        unresolved_only: bool = False,
    ) -> list[ViolationRecord]:
        result = list(self._violations)
        if proposal_id is not None:
            result = [v for v in result if v.proposal_id == proposal_id]
        if severity is not None:
            result = [v for v in result if v.severity == severity]
        if unresolved_only:
            result = [v for v in result if not v.resolved]
        return result

    def get_compliance_report(self) -> dict[str, Any]:
        """Generate a comprehensive compliance report."""
        total_proofs = len(self._proofs)
        passed = sum(1 for p in self._proofs if p.all_checks_passed)
        failed = total_proofs - passed

        total_violations = len(self._violations)
        unresolved = sum(1 for v in self._violations if not v.resolved)
        by_severity: dict[str, int] = {}
        for v in self._violations:
            key = v.severity.value
            by_severity[key] = by_severity.get(key, 0) + 1

        return {
            "total_proofs": total_proofs,
            "proofs_passed": passed,
            "proofs_failed": failed,
            "compliance_rate": passed / max(total_proofs, 1),
            "total_violations": total_violations,
            "unresolved_violations": unresolved,
            "violations_by_severity": by_severity,
            "constitutional_health": "healthy" if unresolved == 0 else "attention_needed",
        }

    @property
    def proof_count(self) -> int:
        return len(self._proofs)

    @property
    def violation_count(self) -> int:
        return len(self._violations)


_audit: ConstitutionalAudit | None = None


def get_constitutional_audit() -> ConstitutionalAudit:
    """Module singleton."""
    global _audit
    if _audit is None:
        _audit = ConstitutionalAudit()
    return _audit
