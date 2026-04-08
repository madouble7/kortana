"""V12C — CI/CD Credential Enforcement.

Enforces credential requirements at CI/CD pipeline checkpoints and
runtime API edges.  Each checkpoint has a policy that specifies the
minimum verification level, required scopes, and session freshness
before allowing an operation.

Integrates with V11B identity sessions and V11C credential gates to
produce auditable enforcement decisions.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger("kortana.ci_credential_enforcement")


# ---------------------------------------------------------------------------
# CI/CD checkpoints
# ---------------------------------------------------------------------------


class CICheckpoint(str, Enum):
    """Pipeline checkpoints where credentials can be enforced."""

    PRE_DEPLOY = "pre_deploy"               # Before deployment starts
    POST_DEPLOY = "post_deploy"             # After deployment (verification)
    BRANCH_PROTECTION = "branch_protection" # Branch merge gates
    RUNTIME_EDGE = "runtime_edge"           # API boundary enforcement
    PIPELINE_GATE = "pipeline_gate"         # Generic pipeline stage gate


# ---------------------------------------------------------------------------
# Credential policy
# ---------------------------------------------------------------------------


@dataclass
class CICredentialPolicy:
    """Defines credential requirements for a CI/CD checkpoint."""

    name: str
    checkpoint: CICheckpoint
    required_verification_level: str = "basic"  # none / basic / elevated / full
    required_scopes: list[str] = field(default_factory=list)
    require_fresh_session: bool = False
    max_session_age_minutes: int = 60
    require_binding: bool = False
    policy_hash: str = ""

    def __post_init__(self) -> None:
        if not self.policy_hash:
            self.policy_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "name": self.name,
                "checkpoint": self.checkpoint.value,
                "required_verification_level": self.required_verification_level,
                "required_scopes": sorted(self.required_scopes),
                "require_fresh_session": self.require_fresh_session,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "checkpoint": self.checkpoint.value,
            "required_verification_level": self.required_verification_level,
            "required_scopes": self.required_scopes,
            "require_fresh_session": self.require_fresh_session,
            "max_session_age_minutes": self.max_session_age_minutes,
            "require_binding": self.require_binding,
            "policy_hash": self.policy_hash,
        }


# ---------------------------------------------------------------------------
# Enforcement result
# ---------------------------------------------------------------------------


@dataclass
class CICredentialCheck:
    """Result of a CI/CD credential enforcement check."""

    check_id: str = field(default_factory=lambda: f"ci_{secrets.token_hex(8)}")
    checkpoint: CICheckpoint = CICheckpoint.PIPELINE_GATE
    session_id: str = ""
    operator_id: str = ""
    passed: bool = False
    reason: str = ""
    policy_applied: str = ""
    verification_level: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    check_hash: str = ""

    def __post_init__(self) -> None:
        if not self.check_hash:
            self.check_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        payload = json.dumps(
            {
                "check_id": self.check_id,
                "checkpoint": self.checkpoint.value,
                "session_id": self.session_id,
                "passed": self.passed,
                "timestamp": self.timestamp.isoformat(),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "checkpoint": self.checkpoint.value,
            "session_id": self.session_id,
            "operator_id": self.operator_id,
            "passed": self.passed,
            "reason": self.reason,
            "policy_applied": self.policy_applied,
            "verification_level": self.verification_level,
            "timestamp": self.timestamp.isoformat(),
            "check_hash": self.check_hash,
        }


# ---------------------------------------------------------------------------
# Default policies
# ---------------------------------------------------------------------------

_LEVEL_ORDER = ["none", "basic", "elevated", "full"]

DEFAULT_CI_POLICIES: dict[str, CICredentialPolicy] = {
    "pre_deploy": CICredentialPolicy(
        name="pre_deploy",
        checkpoint=CICheckpoint.PRE_DEPLOY,
        required_verification_level="elevated",
        required_scopes=["deploy"],
        require_fresh_session=True,
        max_session_age_minutes=30,
    ),
    "post_deploy": CICredentialPolicy(
        name="post_deploy",
        checkpoint=CICheckpoint.POST_DEPLOY,
        required_verification_level="basic",
    ),
    "branch_protection": CICredentialPolicy(
        name="branch_protection",
        checkpoint=CICheckpoint.BRANCH_PROTECTION,
        required_verification_level="elevated",
        required_scopes=["branch_write"],
        require_fresh_session=True,
        max_session_age_minutes=15,
    ),
    "runtime_edge": CICredentialPolicy(
        name="runtime_edge",
        checkpoint=CICheckpoint.RUNTIME_EDGE,
        required_verification_level="basic",
    ),
    "pipeline_gate": CICredentialPolicy(
        name="pipeline_gate",
        checkpoint=CICheckpoint.PIPELINE_GATE,
        required_verification_level="basic",
    ),
}


# ---------------------------------------------------------------------------
# Enforcement function
# ---------------------------------------------------------------------------


def enforce_ci_credential(
    checkpoint: str | CICheckpoint,
    session_id: str,
    policy: CICredentialPolicy | None = None,
) -> CICredentialCheck:
    """Enforce credential requirements at a CI/CD checkpoint.

    Validates the identity session meets the policy requirements:
    - Session exists and is active
    - Verification level meets minimum
    - Required scopes are present
    - Session is fresh enough (if required)
    - Identity binding exists (if required)

    Returns an auditable CICredentialCheck result.
    """
    from src.kortana.services.identity_verification import (
        get_identity_verification_manager,
    )

    # Resolve checkpoint enum
    if isinstance(checkpoint, str):
        try:
            cp = CICheckpoint(checkpoint)
        except ValueError:
            return CICredentialCheck(
                checkpoint=CICheckpoint.PIPELINE_GATE,
                session_id=session_id,
                passed=False,
                reason=f"Unknown checkpoint: {checkpoint!r}",
            )
    else:
        cp = checkpoint

    # Resolve policy
    if policy is None:
        policy = DEFAULT_CI_POLICIES.get(cp.value)
    if policy is None:
        policy = DEFAULT_CI_POLICIES["pipeline_gate"]

    manager = get_identity_verification_manager()
    session = manager.get_session(session_id)

    # Check 1: Session exists and is active
    if session is None:
        return CICredentialCheck(
            checkpoint=cp,
            session_id=session_id,
            passed=False,
            reason="Session not found or expired",
            policy_applied=policy.name,
        )

    if not session.is_active:
        return CICredentialCheck(
            checkpoint=cp,
            session_id=session_id,
            operator_id=session.operator_id,
            passed=False,
            reason="Session is not active",
            policy_applied=policy.name,
            verification_level=session.verification_level.value,
        )

    # Check 2: Verification level
    session_level = session.verification_level.value
    required_idx = _LEVEL_ORDER.index(policy.required_verification_level) if policy.required_verification_level in _LEVEL_ORDER else 0
    session_idx = _LEVEL_ORDER.index(session_level) if session_level in _LEVEL_ORDER else 0

    if session_idx < required_idx:
        return CICredentialCheck(
            checkpoint=cp,
            session_id=session_id,
            operator_id=session.operator_id,
            passed=False,
            reason=f"Verification level {session_level!r} below required {policy.required_verification_level!r}",
            policy_applied=policy.name,
            verification_level=session_level,
        )

    # Check 3: Required scopes
    if policy.required_scopes:
        session_scopes = getattr(session, "scopes", []) or []
        missing = [s for s in policy.required_scopes if s not in session_scopes]
        if missing:
            return CICredentialCheck(
                checkpoint=cp,
                session_id=session_id,
                operator_id=session.operator_id,
                passed=False,
                reason=f"Missing required scopes: {missing}",
                policy_applied=policy.name,
                verification_level=session_level,
            )

    # Check 4: Session freshness
    if policy.require_fresh_session:
        session_age = datetime.utcnow() - session.created_at
        max_age = timedelta(minutes=policy.max_session_age_minutes)
        if session_age > max_age:
            return CICredentialCheck(
                checkpoint=cp,
                session_id=session_id,
                operator_id=session.operator_id,
                passed=False,
                reason=f"Session too old ({session_age.total_seconds():.0f}s > {max_age.total_seconds():.0f}s max)",
                policy_applied=policy.name,
                verification_level=session_level,
            )

    # Check 5: Binding requirement
    if policy.require_binding:
        bindings = manager.get_bindings(session.operator_id)
        active_bindings = [b for b in bindings if b.active]
        if not active_bindings:
            return CICredentialCheck(
                checkpoint=cp,
                session_id=session_id,
                operator_id=session.operator_id,
                passed=False,
                reason="No active identity bindings found",
                policy_applied=policy.name,
                verification_level=session_level,
            )

    # All checks passed
    return CICredentialCheck(
        checkpoint=cp,
        session_id=session_id,
        operator_id=session.operator_id,
        passed=True,
        reason="All credential requirements met",
        policy_applied=policy.name,
        verification_level=session_level,
    )


# ---------------------------------------------------------------------------
# Runtime edge enforcer
# ---------------------------------------------------------------------------


@dataclass
class ProtectedEdge:
    """A protected runtime API edge with a credential policy."""

    path_pattern: str          # regex pattern to match API paths
    policy: CICredentialPolicy
    description: str = ""

    def matches(self, path: str) -> bool:
        """Check if a path matches this edge's pattern."""
        return bool(re.match(self.path_pattern, path))

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_pattern": self.path_pattern,
            "policy": self.policy.to_dict(),
            "description": self.description,
        }


class RuntimeEdgeEnforcer:
    """Enforces credential requirements at runtime API boundaries.

    Maintains a registry of protected API paths and checks incoming
    requests against the configured credential policies.
    """

    def __init__(self) -> None:
        self._edges: list[ProtectedEdge] = []
        self._checks: list[CICredentialCheck] = []

    def register_edge(
        self,
        path_pattern: str,
        policy: CICredentialPolicy | None = None,
        description: str = "",
    ) -> ProtectedEdge:
        """Register a protected runtime edge."""
        if policy is None:
            policy = DEFAULT_CI_POLICIES["runtime_edge"]

        edge = ProtectedEdge(
            path_pattern=path_pattern,
            policy=policy,
            description=description,
        )
        self._edges.append(edge)
        logger.info("Runtime edge registered: %s", path_pattern)
        return edge

    def check_edge(self, path: str, session_id: str) -> CICredentialCheck:
        """Check credential requirements for a request path.

        Finds the first matching edge and enforces its policy.
        If no edge matches, the request is allowed by default.
        """
        for edge in self._edges:
            if edge.matches(path):
                check = enforce_ci_credential(
                    CICheckpoint.RUNTIME_EDGE,
                    session_id,
                    edge.policy,
                )
                self._checks.append(check)
                return check

        # No matching edge — allow by default
        check = CICredentialCheck(
            checkpoint=CICheckpoint.RUNTIME_EDGE,
            session_id=session_id,
            passed=True,
            reason="No matching edge protection; allowed by default",
        )
        self._checks.append(check)
        return check

    @property
    def protected_edges(self) -> list[ProtectedEdge]:
        return list(self._edges)

    @property
    def edge_count(self) -> int:
        return len(self._edges)

    @property
    def check_count(self) -> int:
        return len(self._checks)

    def recent_checks(self, limit: int = 20) -> list[CICredentialCheck]:
        return self._checks[-limit:]


# ---------------------------------------------------------------------------
# Module singletons
# ---------------------------------------------------------------------------

_enforcer: RuntimeEdgeEnforcer | None = None


def get_ci_enforcer() -> RuntimeEdgeEnforcer:
    """Return the module-level runtime edge enforcer."""
    global _enforcer
    if _enforcer is None:
        _enforcer = RuntimeEdgeEnforcer()
    return _enforcer


def get_default_ci_policies() -> dict[str, CICredentialPolicy]:
    """Return all default CI policies."""
    return dict(DEFAULT_CI_POLICIES)
