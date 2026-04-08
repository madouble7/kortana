"""V10B — Authenticated Governance Context.

Wraps every governance action (override, quorum vote, drill, audit export)
in an AuthContext that ties the action to a verified operator identity.
Produces signed action records for non-repudiation.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger("kortana.auth_context")


# ---------------------------------------------------------------------------
# Auth context
# ---------------------------------------------------------------------------


def compute_action_signature(
    operator_id: str,
    action: str,
    resource: str,
    timestamp: str,
    identity_hash: str,
) -> str:
    """SHA-256 signature over the action fields + identity hash."""
    payload = json.dumps(
        {
            "operator_id": operator_id,
            "action": action,
            "resource": resource,
            "timestamp": timestamp,
            "identity_hash": identity_hash,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode()).hexdigest()


@dataclass
class AuthContext:
    """Authenticated context for a governance action.

    Captures who is performing the action, what their role is,
    and produces a signed action record for audit.
    """

    operator_id: str
    display_name: str
    role: str
    identity_hash: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_operator(cls, operator: Any) -> AuthContext:
        """Create AuthContext from an OperatorIdentity."""
        return cls(
            operator_id=operator.operator_id,
            display_name=operator.display_name,
            role=operator.role.value if hasattr(operator.role, "value") else str(operator.role),
            identity_hash=operator.identity_hash,
        )

    def sign_action(self, action: str, resource: str) -> SignedAction:
        """Create a signed action record for this context."""
        return SignedAction(
            operator_id=self.operator_id,
            display_name=self.display_name,
            role=self.role,
            action=action,
            resource=resource,
            identity_hash=self.identity_hash,
            timestamp=self.timestamp,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "operator_id": self.operator_id,
            "display_name": self.display_name,
            "role": self.role,
            "identity_hash": self.identity_hash,
            "timestamp": self.timestamp.isoformat(),
        }


# ---------------------------------------------------------------------------
# Signed action record
# ---------------------------------------------------------------------------


@dataclass
class SignedAction:
    """An action tied to an authenticated operator with a signature."""

    operator_id: str
    display_name: str
    role: str
    action: str
    resource: str
    identity_hash: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    action_signature: str = ""

    def __post_init__(self) -> None:
        if not self.action_signature:
            self.action_signature = compute_action_signature(
                self.operator_id,
                self.action,
                self.resource,
                self.timestamp.isoformat(),
                self.identity_hash,
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "operator_id": self.operator_id,
            "display_name": self.display_name,
            "role": self.role,
            "action": self.action,
            "resource": self.resource,
            "identity_hash": self.identity_hash,
            "action_signature": self.action_signature,
            "timestamp": self.timestamp.isoformat(),
        }


# ---------------------------------------------------------------------------
# Action log (in-memory, complements DB persistence)
# ---------------------------------------------------------------------------


class GovernanceActionLog:
    """In-memory log of signed governance actions for the current session."""

    def __init__(self) -> None:
        self._actions: list[SignedAction] = []

    def record(self, signed_action: SignedAction) -> None:
        """Record a signed action."""
        self._actions.append(signed_action)
        logger.info(
            "Governance action: %s by %s (%s) on %s — sig=%s",
            signed_action.action,
            signed_action.operator_id,
            signed_action.role,
            signed_action.resource,
            signed_action.action_signature[:12],
        )

    def actions_by_operator(self, operator_id: str) -> list[SignedAction]:
        return [a for a in self._actions if a.operator_id == operator_id]

    def actions_by_resource(self, resource: str) -> list[SignedAction]:
        return [a for a in self._actions if a.resource == resource]

    @property
    def all_actions(self) -> list[dict[str, Any]]:
        return [a.to_dict() for a in reversed(self._actions)]

    @property
    def count(self) -> int:
        return len(self._actions)


# ---------------------------------------------------------------------------
# Resolve operator helper
# ---------------------------------------------------------------------------


def resolve_auth_context(
    operator_id: str,
    permission_required: str | None = None,
) -> tuple[AuthContext | None, str | None]:
    """Resolve an operator ID to an AuthContext.

    Optionally checks a permission before returning the context.
    Returns (auth_context, error_message).  If error_message is not None,
    the action should be denied.
    """
    from src.kortana.services.operator_identity import (
        Permission,
        get_operator_registry,
    )

    registry = get_operator_registry()
    operator = registry.get(operator_id)

    if operator is None:
        return None, f"Operator {operator_id!r} not found"

    if not operator.active:
        return None, f"Operator {operator_id!r} is deactivated"

    if permission_required:
        try:
            perm = Permission(permission_required)
        except ValueError:
            return None, f"Unknown permission {permission_required!r}"

        check = registry.check(operator_id, perm)
        if not check.allowed:
            return None, check.reason

    ctx = AuthContext.from_operator(operator)
    return ctx, None


# Module-level singletons
_action_log = GovernanceActionLog()


def get_governance_action_log() -> GovernanceActionLog:
    """Return the module-level governance action log singleton."""
    return _action_log
