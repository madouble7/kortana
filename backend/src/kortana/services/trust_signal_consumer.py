"""V13D — External Trust Signal Consumer.

Consumes external trust signals (IdP verification, secret rotation,
CI attestation, webhook signing, deploy approval) and evaluates them
against configurable requirements before allowing promotion or deploy
decisions to proceed.
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger("kortana.trust_signal_consumer")


# ---------------------------------------------------------------------------
# Enums & value objects
# ---------------------------------------------------------------------------


class TrustSignalType(str, Enum):
    """Types of external trust signal."""

    IDP_VERIFIED = "idp_verified"
    SECRET_ROTATED = "secret_rotated"
    CI_ATTESTED = "ci_attested"
    WEBHOOK_SIGNED = "webhook_signed"
    DEPLOY_APPROVED = "deploy_approved"


@dataclass
class TrustSignal:
    """An incoming trust signal from an external source."""

    signal_id: str = field(default_factory=lambda: f"ts_{secrets.token_hex(8)}")
    signal_type: TrustSignalType = TrustSignalType.IDP_VERIFIED
    source: str = ""
    confidence: float = 1.0
    evidence: dict[str, Any] = field(default_factory=dict)
    version_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    signal_hash: str = ""

    def __post_init__(self) -> None:
        if not self.signal_hash:
            self.signal_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "signal_id": self.signal_id,
                "signal_type": self.signal_type.value,
                "source": self.source,
                "timestamp": self.timestamp.isoformat(),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.utcnow() >= self.expires_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "signal_type": self.signal_type.value,
            "source": self.source,
            "confidence": self.confidence,
            "version_id": self.version_id,
            "evidence": self.evidence,
            "timestamp": self.timestamp.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_expired": self.is_expired,
            "signal_hash": self.signal_hash,
        }


@dataclass
class TrustRequirement:
    """Requirements that must be met by trust signals."""

    required_signals: list[TrustSignalType] = field(default_factory=list)
    min_confidence: float = 0.8
    require_all: bool = True
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "required_signals": [s.value for s in self.required_signals],
            "min_confidence": self.min_confidence,
            "require_all": self.require_all,
            "description": self.description,
        }


@dataclass
class TrustEvaluation:
    """Result of evaluating trust signals against requirements."""

    evaluation_id: str = field(
        default_factory=lambda: f"eval_{secrets.token_hex(8)}"
    )
    version_id: str = ""
    requirements: TrustRequirement = field(default_factory=TrustRequirement)
    signals: list[TrustSignal] = field(default_factory=list)
    passed: bool = False
    score: float = 0.0
    missing_signals: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    eval_hash: str = ""

    def __post_init__(self) -> None:
        if not self.eval_hash:
            self.eval_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "evaluation_id": self.evaluation_id,
                "version_id": self.version_id,
                "passed": self.passed,
                "score": self.score,
                "timestamp": self.timestamp.isoformat(),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "version_id": self.version_id,
            "passed": self.passed,
            "score": self.score,
            "missing_signals": self.missing_signals,
            "signals": [s.to_dict() for s in self.signals],
            "requirements": self.requirements.to_dict(),
            "timestamp": self.timestamp.isoformat(),
            "eval_hash": self.eval_hash,
        }


# ---------------------------------------------------------------------------
# Trust signal consumer
# ---------------------------------------------------------------------------


class TrustSignalConsumer:
    """Collects and evaluates external trust signals."""

    def __init__(self) -> None:
        self._signals: list[TrustSignal] = []
        self._evaluations: list[TrustEvaluation] = []

    def register_signal(self, signal: TrustSignal) -> TrustSignal:
        """Register an incoming trust signal."""
        self._signals.append(signal)
        logger.info(
            "Trust signal registered: type=%s source=%s confidence=%.2f",
            signal.signal_type.value,
            signal.source,
            signal.confidence,
        )
        return signal

    def evaluate(
        self,
        requirements: TrustRequirement,
        version_id: str = "",
    ) -> TrustEvaluation:
        """Evaluate current trust signals against requirements."""
        # Collect non-expired signals per required type
        matched: list[TrustSignal] = []
        missing: list[str] = []

        for req_type in requirements.required_signals:
            candidates = [
                s
                for s in self._signals
                if s.signal_type == req_type
                and not s.is_expired
                and s.confidence >= requirements.min_confidence
                and (not version_id or not s.version_id or s.version_id == version_id)
            ]
            if candidates:
                # Use highest-confidence signal
                best = max(candidates, key=lambda s: s.confidence)
                matched.append(best)
            else:
                missing.append(req_type.value)

        # Calculate score
        if matched:
            score = sum(s.confidence for s in matched) / len(
                requirements.required_signals
            )
        else:
            score = 0.0

        # Determine pass/fail
        if requirements.require_all:
            passed = len(missing) == 0
        else:
            passed = len(matched) > 0

        evaluation = TrustEvaluation(
            version_id=version_id,
            requirements=requirements,
            signals=matched,
            passed=passed,
            score=round(score, 4),
            missing_signals=missing,
        )
        self._evaluations.append(evaluation)

        logger.info(
            "Trust evaluation: passed=%s score=%.2f missing=%s",
            passed,
            score,
            missing,
        )
        return evaluation

    def get_signals(
        self, signal_type: TrustSignalType | None = None
    ) -> list[TrustSignal]:
        """Get signals, optionally filtered by type."""
        if signal_type is None:
            return list(self._signals)
        return [s for s in self._signals if s.signal_type == signal_type]

    def get_evaluations(
        self, version_id: str | None = None
    ) -> list[TrustEvaluation]:
        """Get evaluations, optionally filtered by version_id."""
        if version_id is None:
            return list(self._evaluations)
        return [e for e in self._evaluations if e.version_id == version_id]

    @property
    def signal_count(self) -> int:
        return len(self._signals)

    @property
    def evaluation_count(self) -> int:
        return len(self._evaluations)


# ---------------------------------------------------------------------------
# Deploy trust gate
# ---------------------------------------------------------------------------


class DeployTrustGate:
    """Gates promotion/deploy behind trust-signal evaluation.

    Wraps the V12D AuthenticatedPromotionManager so that a deployment
    only proceeds when trust requirements are satisfied.
    """

    def __init__(
        self,
        consumer: TrustSignalConsumer | None = None,
    ) -> None:
        self._consumer = consumer or get_trust_signal_consumer()

    def promote_with_trust(
        self,
        version_id: str,
        session_id: str,
        requirements: TrustRequirement,
    ) -> tuple[Any | None, str | None]:
        """Promote a rule version only if trust evaluation passes."""
        evaluation = self._consumer.evaluate(requirements, version_id=version_id)

        if not evaluation.passed:
            missing = ", ".join(evaluation.missing_signals)
            return None, (
                f"Trust evaluation failed (score={evaluation.score:.2f}). "
                f"Missing signals: {missing}"
            )

        from src.kortana.services.authenticated_promotion import (
            get_authenticated_promotion_manager,
        )

        manager = get_authenticated_promotion_manager()
        return manager.submit_for_review(version_id, session_id)


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_consumer: TrustSignalConsumer | None = None


def get_trust_signal_consumer() -> TrustSignalConsumer:
    """Return the module-level trust-signal consumer."""
    global _consumer
    if _consumer is None:
        _consumer = TrustSignalConsumer()
    return _consumer
