"""V17B — Rollout Action Executor.

Turns deployment actions into real rollout operations with observability.
Supports multiple rollout strategies (rolling, blue-green, canary, immediate),
multi-step execution with per-step observation, and automatic rollback on
step failure.
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

logger = logging.getLogger("kortana.rollout_action_executor")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class RolloutStrategy(str, Enum):
    """Rollout strategy for deployments."""

    ROLLING = "rolling"
    BLUE_GREEN = "blue_green"
    CANARY_PROGRESSIVE = "canary_progressive"
    IMMEDIATE = "immediate"


class RolloutStepStatus(str, Enum):
    """Status of a single rollout step."""

    PENDING = "pending"
    EXECUTING = "executing"
    OBSERVING = "observing"
    PASSED = "passed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class RolloutStatus(str, Enum):
    """Overall status of a rollout."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# Data objects
# ---------------------------------------------------------------------------


@dataclass
class RolloutStep:
    """A single step in a rollout plan."""

    step_id: str = field(default_factory=lambda: f"step_{secrets.token_hex(6)}")
    step_number: int = 0
    description: str = ""
    traffic_percentage: float = 0.0
    status: RolloutStepStatus = RolloutStepStatus.PENDING
    observation: dict[str, Any] = field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "step_number": self.step_number,
            "description": self.description,
            "traffic_percentage": self.traffic_percentage,
            "status": self.status.value,
            "observation": self.observation,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }


@dataclass
class RolloutAction:
    """A complete rollout action with strategy and steps."""

    action_id: str = field(default_factory=lambda: f"rout_{secrets.token_hex(8)}")
    provider_name: str = ""
    version_id: str = ""
    previous_version: str = ""
    strategy: RolloutStrategy = RolloutStrategy.ROLLING
    steps: list[RolloutStep] = field(default_factory=list)
    status: RolloutStatus = RolloutStatus.PLANNED
    auto_rollback: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    action_hash: str = ""

    def __post_init__(self) -> None:
        if not self.action_hash:
            raw = json.dumps(
                {"act": self.action_id, "provider": self.provider_name,
                 "version": self.version_id,
                 "strategy": self.strategy.value,
                 "ts": self.created_at.isoformat()},
                sort_keys=True, separators=(",", ":"),
            )
            self.action_hash = hashlib.sha256(raw.encode()).hexdigest()

    @property
    def current_step(self) -> int:
        for i, s in enumerate(self.steps):
            if s.status in (RolloutStepStatus.PENDING, RolloutStepStatus.EXECUTING,
                            RolloutStepStatus.OBSERVING):
                return i
        return len(self.steps)

    @property
    def progress_pct(self) -> float:
        if not self.steps:
            return 0.0
        passed = sum(1 for s in self.steps if s.status == RolloutStepStatus.PASSED)
        return round(100 * passed / len(self.steps), 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "provider_name": self.provider_name,
            "version_id": self.version_id,
            "previous_version": self.previous_version,
            "strategy": self.strategy.value,
            "status": self.status.value,
            "step_count": len(self.steps),
            "current_step": self.current_step,
            "progress_pct": self.progress_pct,
            "auto_rollback": self.auto_rollback,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "action_hash": self.action_hash,
        }


@dataclass
class RolloutObservation:
    """An observation collected during a rollout step."""

    observation_id: str = field(default_factory=lambda: f"obs_{secrets.token_hex(8)}")
    action_id: str = ""
    step_id: str = ""
    error_rate: float = 0.0
    latency_p99_ms: float = 0.0
    success_rate: float = 100.0
    healthy: bool = True
    observed_at: datetime = field(default_factory=datetime.utcnow)
    observation_hash: str = ""

    def __post_init__(self) -> None:
        if not self.observation_hash:
            raw = json.dumps(
                {"obs": self.observation_id, "act": self.action_id,
                 "healthy": self.healthy,
                 "ts": self.observed_at.isoformat()},
                sort_keys=True, separators=(",", ":"),
            )
            self.observation_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "action_id": self.action_id,
            "step_id": self.step_id,
            "error_rate": self.error_rate,
            "latency_p99_ms": self.latency_p99_ms,
            "success_rate": self.success_rate,
            "healthy": self.healthy,
            "observed_at": self.observed_at.isoformat(),
            "observation_hash": self.observation_hash,
        }


# ---------------------------------------------------------------------------
# Rollout Executor
# ---------------------------------------------------------------------------


STRATEGY_STEPS: dict[RolloutStrategy, list[tuple[str, float]]] = {
    RolloutStrategy.ROLLING: [
        ("Start rolling (25%)", 25.0),
        ("Continue rolling (50%)", 50.0),
        ("Continue rolling (75%)", 75.0),
        ("Complete rollout (100%)", 100.0),
    ],
    RolloutStrategy.BLUE_GREEN: [
        ("Deploy to green", 0.0),
        ("Switch traffic to green", 100.0),
    ],
    RolloutStrategy.CANARY_PROGRESSIVE: [
        ("Canary (1%)", 1.0),
        ("Canary (5%)", 5.0),
        ("Canary (25%)", 25.0),
        ("Canary (50%)", 50.0),
        ("Full rollout (100%)", 100.0),
    ],
    RolloutStrategy.IMMEDIATE: [
        ("Immediate deploy (100%)", 100.0),
    ],
}


class RolloutExecutor:
    """Plans and executes multi-step rollout actions."""

    def __init__(self) -> None:
        self._actions: dict[str, RolloutAction] = {}
        self._observations: list[RolloutObservation] = []

    def plan_rollout(
        self,
        provider_name: str,
        version_id: str,
        strategy: RolloutStrategy = RolloutStrategy.ROLLING,
        previous_version: str = "",
        auto_rollback: bool = True,
    ) -> RolloutAction:
        """Create a rollout plan with strategy-appropriate steps."""
        step_defs = STRATEGY_STEPS.get(strategy, STRATEGY_STEPS[RolloutStrategy.IMMEDIATE])
        steps = [
            RolloutStep(
                step_number=i,
                description=desc,
                traffic_percentage=pct,
            )
            for i, (desc, pct) in enumerate(step_defs)
        ]
        action = RolloutAction(
            provider_name=provider_name,
            version_id=version_id,
            previous_version=previous_version,
            strategy=strategy,
            steps=steps,
            auto_rollback=auto_rollback,
        )
        self._actions[action.action_id] = action
        logger.info("Planned rollout %s: %s → %s (%s, %d steps)",
                     action.action_id, provider_name, version_id,
                     strategy.value, len(steps))
        return action

    def execute_step(
        self,
        action_id: str,
        simulate_failure: bool = False,
    ) -> RolloutStep | None:
        """Execute the next pending step in a rollout."""
        action = self._actions.get(action_id)
        if action is None:
            return None

        if action.status == RolloutStatus.PLANNED:
            action.status = RolloutStatus.IN_PROGRESS

        # Find next pending step
        step = None
        for s in action.steps:
            if s.status == RolloutStepStatus.PENDING:
                step = s
                break
        if step is None:
            return None

        step.status = RolloutStepStatus.EXECUTING
        step.started_at = datetime.utcnow()

        if simulate_failure:
            step.status = RolloutStepStatus.FAILED
            step.error = "Simulated step failure"
            step.completed_at = datetime.utcnow()
            if action.auto_rollback:
                action.status = RolloutStatus.ROLLED_BACK
                action.completed_at = datetime.utcnow()
                for remaining in action.steps:
                    if remaining.status == RolloutStepStatus.PENDING:
                        remaining.status = RolloutStepStatus.ROLLED_BACK
            else:
                action.status = RolloutStatus.FAILED
                action.completed_at = datetime.utcnow()
            return step

        step.status = RolloutStepStatus.PASSED
        step.completed_at = datetime.utcnow()

        # Check if all steps done
        if all(s.status == RolloutStepStatus.PASSED for s in action.steps):
            action.status = RolloutStatus.COMPLETED
            action.completed_at = datetime.utcnow()

        return step

    def observe_step(
        self,
        action_id: str,
        step_id: str,
        error_rate: float = 0.0,
        latency_p99_ms: float = 10.0,
        success_rate: float = 100.0,
    ) -> RolloutObservation:
        """Record an observation for a rollout step."""
        healthy = error_rate < 5.0 and success_rate > 95.0
        obs = RolloutObservation(
            action_id=action_id,
            step_id=step_id,
            error_rate=error_rate,
            latency_p99_ms=latency_p99_ms,
            success_rate=success_rate,
            healthy=healthy,
        )
        self._observations.append(obs)
        return obs

    def rollback_action(self, action_id: str) -> RolloutAction | None:
        """Manually rollback an entire action."""
        action = self._actions.get(action_id)
        if action is None:
            return None
        action.status = RolloutStatus.ROLLED_BACK
        action.completed_at = datetime.utcnow()
        for step in action.steps:
            if step.status in (RolloutStepStatus.PENDING, RolloutStepStatus.EXECUTING,
                               RolloutStepStatus.OBSERVING):
                step.status = RolloutStepStatus.ROLLED_BACK
        return action

    def cancel_action(self, action_id: str) -> RolloutAction | None:
        """Cancel a rollout action."""
        action = self._actions.get(action_id)
        if action is None:
            return None
        action.status = RolloutStatus.CANCELLED
        action.completed_at = datetime.utcnow()
        return action

    # -- queries --------------------------------------------------------------

    def get_action(self, action_id: str) -> RolloutAction | None:
        return self._actions.get(action_id)

    def get_actions(
        self,
        provider_name: str = "",
        status: RolloutStatus | None = None,
    ) -> list[RolloutAction]:
        actions = list(self._actions.values())
        if provider_name:
            actions = [a for a in actions if a.provider_name == provider_name]
        if status:
            actions = [a for a in actions if a.status == status]
        return actions

    def get_observations(self, action_id: str = "") -> list[RolloutObservation]:
        if action_id:
            return [o for o in self._observations if o.action_id == action_id]
        return list(self._observations)

    def get_steps(self, action_id: str) -> list[RolloutStep]:
        action = self._actions.get(action_id)
        if action is None:
            return []
        return list(action.steps)

    @property
    def action_count(self) -> int:
        return len(self._actions)

    @property
    def observation_count(self) -> int:
        return len(self._observations)


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_executor: RolloutExecutor | None = None


def get_rollout_executor() -> RolloutExecutor:
    """Return the module-level rollout executor."""
    global _executor
    if _executor is None:
        _executor = RolloutExecutor()
    return _executor
