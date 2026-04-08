"""V17C — Feedback Policy Engine.

Probe results from V16D / V17B observations automatically feed rollback
or escalation policy.  Triggers define patterns (error-rate thresholds,
health failures, mismatches) and actions (ROLLBACK, ESCALATE, ALERT, HOLD).
The engine evaluates incoming signals, matches triggers, and produces
auditable feedback evaluations.
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

logger = logging.getLogger("kortana.feedback_policy_engine")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class FeedbackAction(str, Enum):
    """Action to take when a trigger matches."""

    ROLLBACK = "rollback"
    ESCALATE = "escalate"
    ALERT = "alert"
    HOLD = "hold"
    CANCEL = "cancel"
    PROCEED = "proceed"


class TriggerCondition(str, Enum):
    """Type of condition that activates a trigger."""

    ERROR_RATE_ABOVE = "error_rate_above"
    SUCCESS_RATE_BELOW = "success_rate_below"
    HEALTH_FAILED = "health_failed"
    PROBE_MISMATCHED = "probe_mismatched"
    LATENCY_ABOVE = "latency_above"
    CONSECUTIVE_FAILURES = "consecutive_failures"


class EvaluationOutcome(str, Enum):
    """Overall outcome of a feedback evaluation."""

    CLEAN = "clean"
    TRIGGERED = "triggered"
    ESCALATED = "escalated"
    ROLLED_BACK = "rolled_back"


# ---------------------------------------------------------------------------
# Data objects
# ---------------------------------------------------------------------------


@dataclass
class FeedbackTrigger:
    """A trigger that fires when conditions are met."""

    trigger_id: str = field(default_factory=lambda: f"trig_{secrets.token_hex(8)}")
    name: str = ""
    condition: TriggerCondition = TriggerCondition.ERROR_RATE_ABOVE
    threshold: float = 5.0
    action: FeedbackAction = FeedbackAction.ALERT
    pipeline_scope: str = ""
    provider_scope: str = ""
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    trigger_hash: str = ""

    def __post_init__(self) -> None:
        if not self.trigger_hash:
            raw = json.dumps(
                {"id": self.trigger_id, "name": self.name,
                 "condition": self.condition.value,
                 "threshold": self.threshold,
                 "action": self.action.value,
                 "ts": self.created_at.isoformat()},
                sort_keys=True, separators=(",", ":"),
            )
            self.trigger_hash = hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "trigger_id": self.trigger_id,
            "name": self.name,
            "condition": self.condition.value,
            "threshold": self.threshold,
            "action": self.action.value,
            "pipeline_scope": self.pipeline_scope,
            "provider_scope": self.provider_scope,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "trigger_hash": self.trigger_hash,
        }


@dataclass
class FeedbackSignal:
    """An incoming signal to evaluate against triggers."""

    signal_id: str = field(default_factory=lambda: f"sig_{secrets.token_hex(8)}")
    source: str = ""
    pipeline_id: str = ""
    provider_name: str = ""
    error_rate: float = 0.0
    success_rate: float = 100.0
    latency_ms: float = 0.0
    health_ok: bool = True
    probe_matched: bool = True
    consecutive_failures: int = 0
    received_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "source": self.source,
            "pipeline_id": self.pipeline_id,
            "provider_name": self.provider_name,
            "error_rate": self.error_rate,
            "success_rate": self.success_rate,
            "latency_ms": self.latency_ms,
            "health_ok": self.health_ok,
            "probe_matched": self.probe_matched,
            "consecutive_failures": self.consecutive_failures,
            "received_at": self.received_at.isoformat(),
        }


@dataclass
class TriggeredAction:
    """A specific action triggered by signal evaluation."""

    trigger_id: str = ""
    trigger_name: str = ""
    condition_met: str = ""
    action: FeedbackAction = FeedbackAction.ALERT
    measured_value: float = 0.0
    threshold: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "trigger_id": self.trigger_id,
            "trigger_name": self.trigger_name,
            "condition_met": self.condition_met,
            "action": self.action.value,
            "measured_value": self.measured_value,
            "threshold": self.threshold,
        }


@dataclass
class FeedbackEvaluation:
    """Result of evaluating signals against triggers."""

    evaluation_id: str = field(default_factory=lambda: f"eval_{secrets.token_hex(8)}")
    signal_id: str = ""
    triggered_actions: list[TriggeredAction] = field(default_factory=list)
    outcome: EvaluationOutcome = EvaluationOutcome.CLEAN
    evaluated_at: datetime = field(default_factory=datetime.utcnow)
    evaluation_hash: str = ""

    def __post_init__(self) -> None:
        if not self.evaluation_hash:
            raw = json.dumps(
                {"eval": self.evaluation_id, "signal": self.signal_id,
                 "outcome": self.outcome.value,
                 "triggers": len(self.triggered_actions),
                 "ts": self.evaluated_at.isoformat()},
                sort_keys=True, separators=(",", ":"),
            )
            self.evaluation_hash = hashlib.sha256(raw.encode()).hexdigest()

    @property
    def has_rollback(self) -> bool:
        return any(t.action == FeedbackAction.ROLLBACK for t in self.triggered_actions)

    @property
    def has_escalation(self) -> bool:
        return any(t.action == FeedbackAction.ESCALATE for t in self.triggered_actions)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "signal_id": self.signal_id,
            "outcome": self.outcome.value,
            "triggered_actions": [t.to_dict() for t in self.triggered_actions],
            "has_rollback": self.has_rollback,
            "has_escalation": self.has_escalation,
            "evaluated_at": self.evaluated_at.isoformat(),
            "evaluation_hash": self.evaluation_hash,
        }


# ---------------------------------------------------------------------------
# Feedback Policy Engine
# ---------------------------------------------------------------------------


class FeedbackPolicyEngine:
    """Evaluates feedback signals against policy triggers."""

    def __init__(self) -> None:
        self._triggers: dict[str, FeedbackTrigger] = {}
        self._evaluations: list[FeedbackEvaluation] = []
        self._signals: list[FeedbackSignal] = []

    def register_trigger(
        self,
        name: str,
        condition: TriggerCondition,
        threshold: float = 5.0,
        action: FeedbackAction = FeedbackAction.ALERT,
        pipeline_scope: str = "",
        provider_scope: str = "",
    ) -> FeedbackTrigger:
        """Register a feedback trigger."""
        trigger = FeedbackTrigger(
            name=name,
            condition=condition,
            threshold=threshold,
            action=action,
            pipeline_scope=pipeline_scope,
            provider_scope=provider_scope,
        )
        self._triggers[trigger.trigger_id] = trigger
        logger.info("Registered trigger %s: %s > %.1f → %s",
                     trigger.trigger_id, condition.value, threshold, action.value)
        return trigger

    def disable_trigger(self, trigger_id: str) -> bool:
        """Disable a trigger."""
        trigger = self._triggers.get(trigger_id)
        if trigger:
            trigger.enabled = False
            return True
        return False

    def enable_trigger(self, trigger_id: str) -> bool:
        """Enable a trigger."""
        trigger = self._triggers.get(trigger_id)
        if trigger:
            trigger.enabled = True
            return True
        return False

    def _check_trigger(self, trigger: FeedbackTrigger, signal: FeedbackSignal) -> TriggeredAction | None:
        """Check if a signal matches a trigger condition."""
        if not trigger.enabled:
            return None
        if trigger.pipeline_scope and signal.pipeline_id != trigger.pipeline_scope:
            return None
        if trigger.provider_scope and signal.provider_name != trigger.provider_scope:
            return None

        measured: float = 0.0
        matched = False

        if trigger.condition == TriggerCondition.ERROR_RATE_ABOVE:
            measured = signal.error_rate
            matched = measured > trigger.threshold
        elif trigger.condition == TriggerCondition.SUCCESS_RATE_BELOW:
            measured = signal.success_rate
            matched = measured < trigger.threshold
        elif trigger.condition == TriggerCondition.HEALTH_FAILED:
            measured = 0.0 if signal.health_ok else 1.0
            matched = not signal.health_ok
        elif trigger.condition == TriggerCondition.PROBE_MISMATCHED:
            measured = 0.0 if signal.probe_matched else 1.0
            matched = not signal.probe_matched
        elif trigger.condition == TriggerCondition.LATENCY_ABOVE:
            measured = signal.latency_ms
            matched = measured > trigger.threshold
        elif trigger.condition == TriggerCondition.CONSECUTIVE_FAILURES:
            measured = float(signal.consecutive_failures)
            matched = measured >= trigger.threshold

        if matched:
            return TriggeredAction(
                trigger_id=trigger.trigger_id,
                trigger_name=trigger.name,
                condition_met=trigger.condition.value,
                action=trigger.action,
                measured_value=measured,
                threshold=trigger.threshold,
            )
        return None

    def evaluate_signal(self, signal: FeedbackSignal) -> FeedbackEvaluation:
        """Evaluate a signal against all registered triggers."""
        self._signals.append(signal)
        triggered: list[TriggeredAction] = []

        for trigger in self._triggers.values():
            result = self._check_trigger(trigger, signal)
            if result is not None:
                triggered.append(result)

        # Determine outcome
        if not triggered:
            outcome = EvaluationOutcome.CLEAN
        elif any(t.action == FeedbackAction.ROLLBACK for t in triggered):
            outcome = EvaluationOutcome.ROLLED_BACK
        elif any(t.action == FeedbackAction.ESCALATE for t in triggered):
            outcome = EvaluationOutcome.ESCALATED
        else:
            outcome = EvaluationOutcome.TRIGGERED

        evaluation = FeedbackEvaluation(
            signal_id=signal.signal_id,
            triggered_actions=triggered,
            outcome=outcome,
        )
        self._evaluations.append(evaluation)
        logger.info("Evaluated signal %s: %s (%d triggers matched)",
                     signal.signal_id, outcome.value, len(triggered))
        return evaluation

    def evaluate_batch(self, signals: list[FeedbackSignal]) -> list[FeedbackEvaluation]:
        """Evaluate many signals at once."""
        return [self.evaluate_signal(s) for s in signals]

    # -- queries --------------------------------------------------------------

    def get_triggers(self, enabled_only: bool = False) -> list[FeedbackTrigger]:
        triggers = list(self._triggers.values())
        if enabled_only:
            triggers = [t for t in triggers if t.enabled]
        return triggers

    def get_evaluations(
        self,
        outcome: EvaluationOutcome | None = None,
    ) -> list[FeedbackEvaluation]:
        evals = list(self._evaluations)
        if outcome:
            evals = [e for e in evals if e.outcome == outcome]
        return evals

    def get_signals(self) -> list[FeedbackSignal]:
        return list(self._signals)

    @property
    def trigger_count(self) -> int:
        return len(self._triggers)

    @property
    def evaluation_count(self) -> int:
        return len(self._evaluations)


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_engine: FeedbackPolicyEngine | None = None


def get_feedback_policy_engine() -> FeedbackPolicyEngine:
    """Return the module-level feedback policy engine."""
    global _engine
    if _engine is None:
        _engine = FeedbackPolicyEngine()
    return _engine
