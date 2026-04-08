"""V14D — Externally-Issued Trust Artifact Policy.

Extends V13D TrustSignalConsumer & DeployTrustGate with artifact-based
policy: signed manifests, SBOM attestations, vulnerability scans,
compliance certificates, and audit reports gate promotion/deploy.
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

logger = logging.getLogger("kortana.trust_artifact_policy")


# ---------------------------------------------------------------------------
# Enums & value objects
# ---------------------------------------------------------------------------


class ArtifactType(str, Enum):
    """Types of externally-issued trust artifact."""

    SIGNED_MANIFEST = "signed_manifest"
    SBOM_ATTESTATION = "sbom_attestation"
    VULNERABILITY_SCAN = "vulnerability_scan"
    COMPLIANCE_CERT = "compliance_cert"
    AUDIT_REPORT = "audit_report"


@dataclass
class TrustArtifact:
    """An externally-issued trust artifact."""

    artifact_id: str = field(
        default_factory=lambda: f"art_{secrets.token_hex(8)}"
    )
    artifact_type: ArtifactType = ArtifactType.SIGNED_MANIFEST
    issuer: str = ""
    subject: str = ""
    signature: str = ""
    content_hash: str = ""
    version_id: str = ""
    issued_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    artifact_hash: str = ""

    def __post_init__(self) -> None:
        if not self.artifact_hash:
            self.artifact_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "artifact_id": self.artifact_id,
                "artifact_type": self.artifact_type.value,
                "issuer": self.issuer,
                "issued_at": self.issued_at.isoformat(),
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

    @property
    def age_hours(self) -> float:
        return (datetime.utcnow() - self.issued_at).total_seconds() / 3600.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type.value,
            "issuer": self.issuer,
            "subject": self.subject,
            "content_hash": self.content_hash,
            "version_id": self.version_id,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_expired": self.is_expired,
            "age_hours": round(self.age_hours, 2),
            "artifact_hash": self.artifact_hash,
        }


@dataclass
class ArtifactPolicy:
    """Policy requiring specific trust artifacts for promotion."""

    policy_id: str = field(
        default_factory=lambda: f"apol_{secrets.token_hex(8)}"
    )
    policy_name: str = ""
    required_artifacts: list[ArtifactType] = field(default_factory=list)
    min_artifact_age_hours: float = 0.0
    max_artifact_age_hours: float = 720.0  # 30 days
    require_all: bool = True
    policy_hash: str = ""

    def __post_init__(self) -> None:
        if not self.policy_hash:
            self.policy_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "policy_id": self.policy_id,
                "policy_name": self.policy_name,
                "required": [a.value for a in self.required_artifacts],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "policy_name": self.policy_name,
            "required_artifacts": [a.value for a in self.required_artifacts],
            "min_artifact_age_hours": self.min_artifact_age_hours,
            "max_artifact_age_hours": self.max_artifact_age_hours,
            "require_all": self.require_all,
            "policy_hash": self.policy_hash,
        }


@dataclass
class ArtifactVerification:
    """Result of verifying an artifact against a policy."""

    verification_id: str = field(
        default_factory=lambda: f"averif_{secrets.token_hex(8)}"
    )
    artifact_id: str = ""
    artifact_type: ArtifactType = ArtifactType.SIGNED_MANIFEST
    policy_id: str = ""
    verified: bool = False
    reason: str = ""
    verified_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verification_id": self.verification_id,
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type.value,
            "policy_id": self.policy_id,
            "verified": self.verified,
            "reason": self.reason,
            "verified_at": self.verified_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# Policy orchestrator
# ---------------------------------------------------------------------------


class PolicyOrchestrator:
    """Orchestrates trust-artifact policies for promotion/deploy."""

    def __init__(self) -> None:
        self._artifacts: list[TrustArtifact] = []
        self._policies: list[ArtifactPolicy] = []
        self._verifications: list[ArtifactVerification] = []

    def register_artifact(self, artifact: TrustArtifact) -> TrustArtifact:
        """Register an incoming trust artifact."""
        self._artifacts.append(artifact)
        logger.info(
            "Artifact registered: type=%s issuer=%s",
            artifact.artifact_type.value,
            artifact.issuer,
        )
        return artifact

    def define_policy(
        self,
        policy_name: str,
        required_artifacts: list[ArtifactType],
        require_all: bool = True,
        max_artifact_age_hours: float = 720.0,
    ) -> ArtifactPolicy:
        """Define an artifact policy."""
        policy = ArtifactPolicy(
            policy_name=policy_name,
            required_artifacts=required_artifacts,
            require_all=require_all,
            max_artifact_age_hours=max_artifact_age_hours,
        )
        self._policies.append(policy)
        logger.info("Policy defined: %s requires %s", policy_name, [a.value for a in required_artifacts])
        return policy

    def verify_artifact(
        self, artifact: TrustArtifact, policy: ArtifactPolicy
    ) -> ArtifactVerification:
        """Verify an artifact against a policy's age constraints."""
        if artifact.is_expired:
            v = ArtifactVerification(
                artifact_id=artifact.artifact_id,
                artifact_type=artifact.artifact_type,
                policy_id=policy.policy_id,
                verified=False,
                reason="Artifact has expired",
            )
            self._verifications.append(v)
            return v

        age = artifact.age_hours
        if age < policy.min_artifact_age_hours:
            v = ArtifactVerification(
                artifact_id=artifact.artifact_id,
                artifact_type=artifact.artifact_type,
                policy_id=policy.policy_id,
                verified=False,
                reason=f"Artifact too new ({age:.1f}h < {policy.min_artifact_age_hours}h)",
            )
            self._verifications.append(v)
            return v

        if age > policy.max_artifact_age_hours:
            v = ArtifactVerification(
                artifact_id=artifact.artifact_id,
                artifact_type=artifact.artifact_type,
                policy_id=policy.policy_id,
                verified=False,
                reason=f"Artifact too old ({age:.1f}h > {policy.max_artifact_age_hours}h)",
            )
            self._verifications.append(v)
            return v

        v = ArtifactVerification(
            artifact_id=artifact.artifact_id,
            artifact_type=artifact.artifact_type,
            policy_id=policy.policy_id,
            verified=True,
            reason="OK",
        )
        self._verifications.append(v)
        return v

    def evaluate_deployment(
        self, version_id: str, policy: ArtifactPolicy
    ) -> tuple[bool, list[ArtifactVerification]]:
        """Evaluate whether all required artifacts exist for a deployment."""
        verifications: list[ArtifactVerification] = []
        missing: list[str] = []

        for req_type in policy.required_artifacts:
            candidates = [
                a
                for a in self._artifacts
                if a.artifact_type == req_type
                and not a.is_expired
                and (not version_id or not a.version_id or a.version_id == version_id)
            ]
            if candidates:
                best = max(candidates, key=lambda a: a.issued_at)
                v = self.verify_artifact(best, policy)
                verifications.append(v)
            else:
                missing.append(req_type.value)
                verifications.append(
                    ArtifactVerification(
                        artifact_type=req_type,
                        policy_id=policy.policy_id,
                        verified=False,
                        reason=f"No {req_type.value} artifact found",
                    )
                )

        if policy.require_all:
            passed = all(v.verified for v in verifications)
        else:
            passed = any(v.verified for v in verifications)

        return passed, verifications

    def promote_with_artifacts(
        self, version_id: str, session_id: str, policy: ArtifactPolicy
    ) -> tuple[Any | None, str | None]:
        """Promote a version only if artifact policy is satisfied."""
        passed, verifications = self.evaluate_deployment(version_id, policy)
        if not passed:
            failed = [v for v in verifications if not v.verified]
            reasons = "; ".join(v.reason for v in failed)
            return None, f"Artifact policy failed: {reasons}"

        from src.kortana.services.trust_signal_consumer import (
            DeployTrustGate,
            TrustRequirement,
            get_trust_signal_consumer,
        )

        gate = DeployTrustGate(get_trust_signal_consumer())
        req = TrustRequirement(
            required_signals=[],
            require_all=True,
        )
        return gate.promote_with_trust(version_id, session_id, req)

    def get_artifacts(
        self, artifact_type: ArtifactType | None = None
    ) -> list[TrustArtifact]:
        if artifact_type is None:
            return list(self._artifacts)
        return [a for a in self._artifacts if a.artifact_type == artifact_type]

    def get_policies(self) -> list[ArtifactPolicy]:
        return list(self._policies)

    def get_verifications(
        self, version_id: str | None = None
    ) -> list[ArtifactVerification]:
        if version_id is None:
            return list(self._verifications)
        # Return verifications whose artifact matches version
        artifact_ids = {
            a.artifact_id for a in self._artifacts if a.version_id == version_id
        }
        return [v for v in self._verifications if v.artifact_id in artifact_ids]

    @property
    def artifact_count(self) -> int:
        return len(self._artifacts)

    @property
    def policy_count(self) -> int:
        return len(self._policies)

    @property
    def verification_count(self) -> int:
        return len(self._verifications)


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_orchestrator: PolicyOrchestrator | None = None


def get_policy_orchestrator() -> PolicyOrchestrator:
    """Return the module-level policy orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = PolicyOrchestrator()
    return _orchestrator
