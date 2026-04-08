"""V10A — Operator Identity & Role Mapping.

Replaces fixed approver name strings with proper identity objects
that carry roles, permissions, and audit context.  Operators are
registered with a role, and every governance action is checked
against a permission matrix before execution.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger("kortana.operator_identity")


# ---------------------------------------------------------------------------
# Roles and permissions
# ---------------------------------------------------------------------------


class OperatorRole(str, Enum):
    """Roles an operator can hold within the governance system."""

    ADMIN = "admin"          # full authority — create/revoke overrides, quorum, deploy
    OPERATOR = "operator"    # can create overrides, vote on quorum, view control room
    REVIEWER = "reviewer"    # can vote on quorum, export audit bundles, read-only control room
    VIEWER = "viewer"        # read-only access to control room and audit history
    ONCALL = "oncall"        # operator + emergency override without quorum


class Permission(str, Enum):
    """Fine-grained permissions for governance actions."""

    OVERRIDE_CREATE = "override.create"
    OVERRIDE_REVOKE = "override.revoke"
    QUORUM_REQUEST = "quorum.request"
    QUORUM_VOTE = "quorum.vote"
    DRILL_RUN = "drill.run"
    DRILL_SCHEDULE = "drill.schedule"
    SLO_MANAGE = "slo.manage"
    AUDIT_EXPORT = "audit.export"
    DEPLOY_APPROVE = "deploy.approve"
    DEPLOY_GATE = "deploy.gate"
    POLICY_MANAGE = "policy.manage"
    CONTROL_ROOM_VIEW = "control_room.view"
    EMERGENCY_OVERRIDE = "emergency.override"


# Role → permissions matrix
ROLE_PERMISSIONS: dict[OperatorRole, frozenset[Permission]] = {
    OperatorRole.ADMIN: frozenset(Permission),
    OperatorRole.ONCALL: frozenset({
        Permission.OVERRIDE_CREATE,
        Permission.OVERRIDE_REVOKE,
        Permission.QUORUM_REQUEST,
        Permission.QUORUM_VOTE,
        Permission.DRILL_RUN,
        Permission.DRILL_SCHEDULE,
        Permission.SLO_MANAGE,
        Permission.AUDIT_EXPORT,
        Permission.DEPLOY_APPROVE,
        Permission.DEPLOY_GATE,
        Permission.CONTROL_ROOM_VIEW,
        Permission.EMERGENCY_OVERRIDE,
    }),
    OperatorRole.OPERATOR: frozenset({
        Permission.OVERRIDE_CREATE,
        Permission.OVERRIDE_REVOKE,
        Permission.QUORUM_REQUEST,
        Permission.QUORUM_VOTE,
        Permission.DRILL_RUN,
        Permission.DRILL_SCHEDULE,
        Permission.AUDIT_EXPORT,
        Permission.CONTROL_ROOM_VIEW,
    }),
    OperatorRole.REVIEWER: frozenset({
        Permission.QUORUM_VOTE,
        Permission.AUDIT_EXPORT,
        Permission.CONTROL_ROOM_VIEW,
    }),
    OperatorRole.VIEWER: frozenset({
        Permission.CONTROL_ROOM_VIEW,
    }),
}


# ---------------------------------------------------------------------------
# Operator identity
# ---------------------------------------------------------------------------


def compute_identity_hash(
    operator_id: str,
    display_name: str,
    role: str,
    created_at: str,
) -> str:
    """SHA-256 hash over identity fields for tamper evidence."""
    payload = json.dumps(
        {
            "operator_id": operator_id,
            "display_name": display_name,
            "role": role,
            "created_at": created_at,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode()).hexdigest()


@dataclass
class OperatorIdentity:
    """An authenticated operator with role-based permissions."""

    operator_id: str
    display_name: str
    role: OperatorRole
    created_at: datetime = field(default_factory=datetime.utcnow)
    active: bool = True
    identity_hash: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.role, str):
            self.role = OperatorRole(self.role)
        if not self.identity_hash:
            self.identity_hash = compute_identity_hash(
                self.operator_id,
                self.display_name,
                self.role.value,
                self.created_at.isoformat(),
            )

    @property
    def permissions(self) -> frozenset[Permission]:
        return ROLE_PERMISSIONS.get(self.role, frozenset())

    def has_permission(self, perm: Permission) -> bool:
        return perm in self.permissions

    def to_dict(self) -> dict[str, Any]:
        return {
            "operator_id": self.operator_id,
            "display_name": self.display_name,
            "role": self.role.value,
            "active": self.active,
            "permissions": sorted(p.value for p in self.permissions),
            "identity_hash": self.identity_hash,
            "created_at": self.created_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# Permission check
# ---------------------------------------------------------------------------


@dataclass
class PermissionCheck:
    """Result of a permission check against an operator."""

    allowed: bool
    operator_id: str
    permission: str
    role: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "operator_id": self.operator_id,
            "permission": self.permission,
            "role": self.role,
            "reason": self.reason,
        }


def check_permission(
    operator: OperatorIdentity | None,
    permission: Permission,
) -> PermissionCheck:
    """Check if an operator has a specific permission.

    Returns a PermissionCheck with the result and reason.
    """
    if operator is None:
        return PermissionCheck(
            allowed=False,
            operator_id="unknown",
            permission=permission.value,
            role="none",
            reason="No operator identity provided",
        )

    if not operator.active:
        return PermissionCheck(
            allowed=False,
            operator_id=operator.operator_id,
            permission=permission.value,
            role=operator.role.value,
            reason=f"Operator {operator.operator_id!r} is deactivated",
        )

    if operator.has_permission(permission):
        return PermissionCheck(
            allowed=True,
            operator_id=operator.operator_id,
            permission=permission.value,
            role=operator.role.value,
            reason=f"Role {operator.role.value!r} grants {permission.value!r}",
        )

    return PermissionCheck(
        allowed=False,
        operator_id=operator.operator_id,
        permission=permission.value,
        role=operator.role.value,
        reason=f"Role {operator.role.value!r} does not grant {permission.value!r}",
    )


# ---------------------------------------------------------------------------
# Operator registry
# ---------------------------------------------------------------------------


class OperatorRegistry:
    """Manages registered operators and their identities."""

    def __init__(self) -> None:
        self._operators: dict[str, OperatorIdentity] = {}

    def register(
        self,
        operator_id: str,
        display_name: str,
        role: OperatorRole | str,
    ) -> OperatorIdentity:
        """Register a new operator. Raises ValueError if ID already exists."""
        if operator_id in self._operators:
            raise ValueError(f"Operator {operator_id!r} already registered")

        if isinstance(role, str):
            role = OperatorRole(role)

        identity = OperatorIdentity(
            operator_id=operator_id,
            display_name=display_name,
            role=role,
        )
        self._operators[operator_id] = identity
        logger.info(
            "Operator registered: %s (%s) as %s",
            operator_id, display_name, role.value,
        )
        return identity

    def get(self, operator_id: str) -> OperatorIdentity | None:
        """Look up an operator by ID."""
        return self._operators.get(operator_id)

    def deactivate(self, operator_id: str) -> bool:
        """Deactivate an operator. Returns True if found."""
        op = self._operators.get(operator_id)
        if op is None:
            return False
        op.active = False
        logger.info("Operator deactivated: %s", operator_id)
        return True

    def activate(self, operator_id: str) -> bool:
        """Re-activate an operator. Returns True if found."""
        op = self._operators.get(operator_id)
        if op is None:
            return False
        op.active = True
        return True

    def update_role(self, operator_id: str, new_role: OperatorRole | str) -> bool:
        """Update an operator's role. Returns True if found."""
        op = self._operators.get(operator_id)
        if op is None:
            return False
        if isinstance(new_role, str):
            new_role = OperatorRole(new_role)
        old_role = op.role
        op.role = new_role
        logger.info(
            "Operator %s role changed: %s → %s",
            operator_id, old_role.value, new_role.value,
        )
        return True

    def check(self, operator_id: str, permission: Permission) -> PermissionCheck:
        """Check if a registered operator has a permission."""
        op = self.get(operator_id)
        return check_permission(op, permission)

    @property
    def all_operators(self) -> list[OperatorIdentity]:
        return list(self._operators.values())

    @property
    def active_operators(self) -> list[OperatorIdentity]:
        return [op for op in self._operators.values() if op.active]

    @property
    def count(self) -> int:
        return len(self._operators)


# Module-level singleton with default matt operator
_registry = OperatorRegistry()
_registry.register("matt", "Matt", OperatorRole.ADMIN)


def get_operator_registry() -> OperatorRegistry:
    """Return the module-level operator registry singleton."""
    return _registry
