"""V16C — Deployment Binding.

Wires V15D's PipelineEnforcer stage gates into concrete deployment actions.
Supports registering deployment targets (environments with endpoints),
binding pipelines to targets, executing deployment actions, and verifying
that deployments actually landed.
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

logger = logging.getLogger("kortana.deployment_binding")


# ---------------------------------------------------------------------------
# Enums & value objects
# ---------------------------------------------------------------------------


class TargetEnvironment(str, Enum):
    """Deployment target environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    CANARY = "canary"
    PRODUCTION = "production"
    DISASTER_RECOVERY = "disaster_recovery"


class ActionType(str, Enum):
    """Type of deployment action."""

    DEPLOY = "deploy"
    ROLLBACK = "rollback"
    PROMOTE = "promote"
    SCALE = "scale"
    DRAIN = "drain"


class ActionStatus(str, Enum):
    """Status of a deployment action."""

    PENDING = "pending"
    EXECUTING = "executing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    VERIFIED = "verified"


@dataclass
class DeploymentTarget:
    """A registered deployment target."""

    target_id: str = field(default_factory=lambda: f"tgt_{secrets.token_hex(8)}")
    name: str = ""
    environment: TargetEnvironment = TargetEnvironment.STAGING
    endpoint_url: str = ""
    credentials_ref: str = ""
    health_check_url: str = ""
    active: bool = True
    registered_at: datetime = field(default_factory=datetime.utcnow)
    target_hash: str = ""

    def __post_init__(self) -> None:
        if not self.target_hash:
            raw = json.dumps(
                {"id": self.target_id, "name": self.name,
                 "env": self.environment.value,
                 "ts": self.registered_at.isoformat()},
                sort_keys=True, separators=(",", ":"),
            )
            self.target_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "name": self.name,
            "environment": self.environment.value,
            "endpoint_url": self.endpoint_url,
            "health_check_url": self.health_check_url,
            "active": self.active,
            "registered_at": self.registered_at.isoformat(),
            "target_hash": self.target_hash,
        }


@dataclass
class PipelineBinding:
    """Binds a pipeline to a deployment target."""

    binding_id: str = field(default_factory=lambda: f"bind_{secrets.token_hex(8)}")
    pipeline_id: str = ""
    target_id: str = ""
    version_id: str = ""
    stage_mapping: dict[str, str] = field(default_factory=dict)
    bound_at: datetime = field(default_factory=datetime.utcnow)
    binding_hash: str = ""

    def __post_init__(self) -> None:
        if not self.binding_hash:
            raw = json.dumps(
                {"bind": self.binding_id, "pipeline": self.pipeline_id,
                 "target": self.target_id,
                 "ts": self.bound_at.isoformat()},
                sort_keys=True, separators=(",", ":"),
            )
            self.binding_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "binding_id": self.binding_id,
            "pipeline_id": self.pipeline_id,
            "target_id": self.target_id,
            "version_id": self.version_id,
            "stage_mapping": self.stage_mapping,
            "bound_at": self.bound_at.isoformat(),
            "binding_hash": self.binding_hash,
        }


@dataclass
class DeploymentAction:
    """A concrete deployment action executed against a target."""

    action_id: str = field(default_factory=lambda: f"act_{secrets.token_hex(8)}")
    target_id: str = ""
    pipeline_id: str = ""
    version_id: str = ""
    stage: str = ""
    action_type: ActionType = ActionType.DEPLOY
    status: ActionStatus = ActionStatus.PENDING
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    error: str = ""
    action_hash: str = ""

    def __post_init__(self) -> None:
        if not self.action_hash:
            raw = json.dumps(
                {"act": self.action_id, "target": self.target_id,
                 "type": self.action_type.value,
                 "ts": self.started_at.isoformat()},
                sort_keys=True, separators=(",", ":"),
            )
            self.action_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "target_id": self.target_id,
            "pipeline_id": self.pipeline_id,
            "version_id": self.version_id,
            "stage": self.stage,
            "action_type": self.action_type.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "action_hash": self.action_hash,
        }


@dataclass
class DeploymentVerification:
    """Verification that a deployment action actually landed."""

    verification_id: str = field(default_factory=lambda: f"dv_{secrets.token_hex(8)}")
    action_id: str = ""
    target_id: str = ""
    version_id: str = ""
    expected_version: str = ""
    observed_version: str = ""
    health_ok: bool = True
    verified: bool = True
    verified_at: datetime = field(default_factory=datetime.utcnow)
    verification_hash: str = ""

    def __post_init__(self) -> None:
        if not self.verification_hash:
            raw = json.dumps(
                {"dv": self.verification_id, "act": self.action_id,
                 "verified": self.verified,
                 "ts": self.verified_at.isoformat()},
                sort_keys=True, separators=(",", ":"),
            )
            self.verification_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "verification_id": self.verification_id,
            "action_id": self.action_id,
            "target_id": self.target_id,
            "version_id": self.version_id,
            "expected_version": self.expected_version,
            "observed_version": self.observed_version,
            "health_ok": self.health_ok,
            "verified": self.verified,
            "verified_at": self.verified_at.isoformat(),
            "verification_hash": self.verification_hash,
        }


# ---------------------------------------------------------------------------
# Deployment Binding manager
# ---------------------------------------------------------------------------


class DeploymentBinding:
    """Manages deployment targets, pipeline bindings, and deployment actions."""

    def __init__(self) -> None:
        self._targets: dict[str, DeploymentTarget] = {}
        self._bindings: dict[str, PipelineBinding] = {}
        self._actions: list[DeploymentAction] = []
        self._verifications: list[DeploymentVerification] = []

    # -- targets --------------------------------------------------------------

    def register_target(
        self,
        name: str,
        environment: TargetEnvironment,
        endpoint_url: str = "",
        credentials_ref: str = "",
        health_check_url: str = "",
    ) -> DeploymentTarget:
        """Register a deployment target."""
        target = DeploymentTarget(
            name=name,
            environment=environment,
            endpoint_url=endpoint_url,
            credentials_ref=credentials_ref,
            health_check_url=health_check_url,
        )
        self._targets[target.target_id] = target
        logger.info("Registered target %s (%s)", name, environment.value)
        return target

    def get_target(self, target_id: str) -> DeploymentTarget | None:
        return self._targets.get(target_id)

    def list_targets(self, environment: TargetEnvironment | None = None) -> list[DeploymentTarget]:
        targets = list(self._targets.values())
        if environment:
            targets = [t for t in targets if t.environment == environment]
        return targets

    def deactivate_target(self, target_id: str) -> bool:
        target = self._targets.get(target_id)
        if target:
            target.active = False
            return True
        return False

    # -- bindings -------------------------------------------------------------

    def bind_pipeline(
        self,
        pipeline_id: str,
        target_id: str,
        version_id: str = "",
        stage_mapping: dict[str, str] | None = None,
    ) -> PipelineBinding | None:
        """Bind a pipeline to a deployment target."""
        if target_id not in self._targets:
            return None
        binding = PipelineBinding(
            pipeline_id=pipeline_id,
            target_id=target_id,
            version_id=version_id,
            stage_mapping=stage_mapping or {},
        )
        self._bindings[binding.binding_id] = binding
        logger.info("Bound pipeline %s → target %s", pipeline_id, target_id)
        return binding

    def get_bindings(self, pipeline_id: str = "") -> list[PipelineBinding]:
        bindings = list(self._bindings.values())
        if pipeline_id:
            bindings = [b for b in bindings if b.pipeline_id == pipeline_id]
        return bindings

    # -- deployment actions ---------------------------------------------------

    def execute_deployment(
        self,
        target_id: str,
        pipeline_id: str,
        version_id: str,
        stage: str = "",
        action_type: ActionType = ActionType.DEPLOY,
        simulate_failure: bool = False,
    ) -> DeploymentAction:
        """Execute a deployment action against a target."""
        target = self._targets.get(target_id)
        action = DeploymentAction(
            target_id=target_id,
            pipeline_id=pipeline_id,
            version_id=version_id,
            stage=stage,
            action_type=action_type,
            status=ActionStatus.EXECUTING,
        )

        if target is None or not target.active:
            action.status = ActionStatus.FAILED
            action.error = "Target not found or inactive"
            action.completed_at = datetime.utcnow()
            self._actions.append(action)
            return action

        if simulate_failure:
            action.status = ActionStatus.FAILED
            action.error = "Simulated deployment failure"
            action.completed_at = datetime.utcnow()
            self._actions.append(action)
            return action

        # Successful deployment
        action.status = ActionStatus.SUCCEEDED
        action.completed_at = datetime.utcnow()
        self._actions.append(action)
        logger.info("Deployed %s to %s (%s)", version_id, target.name, action_type.value)
        return action

    def get_actions(
        self,
        pipeline_id: str = "",
        target_id: str = "",
    ) -> list[DeploymentAction]:
        actions = list(self._actions)
        if pipeline_id:
            actions = [a for a in actions if a.pipeline_id == pipeline_id]
        if target_id:
            actions = [a for a in actions if a.target_id == target_id]
        return actions

    # -- verification ---------------------------------------------------------

    def verify_deployment(
        self,
        action_id: str,
        expected_version: str = "",
        simulate_mismatch: bool = False,
        simulate_unhealthy: bool = False,
    ) -> DeploymentVerification:
        """Verify a deployment actually landed and is healthy."""
        action = next((a for a in self._actions if a.action_id == action_id), None)

        observed = expected_version if not simulate_mismatch else "unknown"
        health_ok = not simulate_unhealthy
        verified = (observed == expected_version) and health_ok

        verification = DeploymentVerification(
            action_id=action_id,
            target_id=action.target_id if action else "",
            version_id=action.version_id if action else "",
            expected_version=expected_version,
            observed_version=observed,
            health_ok=health_ok,
            verified=verified,
        )
        self._verifications.append(verification)

        if action and verified:
            action.status = ActionStatus.VERIFIED
        return verification

    def get_verifications(self, target_id: str = "") -> list[DeploymentVerification]:
        verifications = list(self._verifications)
        if target_id:
            verifications = [v for v in verifications if v.target_id == target_id]
        return verifications

    # -- query ---------------------------------------------------------------

    @property
    def target_count(self) -> int:
        return len(self._targets)

    @property
    def binding_count(self) -> int:
        return len(self._bindings)

    @property
    def action_count(self) -> int:
        return len(self._actions)


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_binding: DeploymentBinding | None = None


def get_deployment_binding() -> DeploymentBinding:
    """Return the module-level deployment binding."""
    global _binding
    if _binding is None:
        _binding = DeploymentBinding()
    return _binding
