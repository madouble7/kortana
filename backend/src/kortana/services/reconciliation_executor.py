"""V18C — Reconciliation Executor: plan execution with retry & escalation."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from src.kortana.services.reconciliation_planner import (
    ReconciliationPlan,
    ReconciliationAction,
    ReconciliationActionType,
    PlanStatus,
)


# ── Enums ─────────────────────────────────────────────────────────────────


class ExecutionStatus(Enum):
    """Status of a reconciliation execution."""

    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    ESCALATED = "escalated"


class StepOutcome(Enum):
    """Outcome of a single reconciliation step."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


# ── Data structures ───────────────────────────────────────────────────────


@dataclass
class ReconciliationStepResult:
    """Result of executing a single reconciliation action."""

    step_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    action_id: str = ""
    action_type: ReconciliationActionType = ReconciliationActionType.FORCE_HEALTH_CHECK
    target_provider: str = ""
    outcome: StepOutcome = StepOutcome.SUCCESS
    attempts: int = 1
    max_attempts: int = 3
    error_message: str = ""
    executed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    result_hash: str = ""

    def __post_init__(self) -> None:
        if not self.result_hash:
            raw = f"{self.step_id}:{self.action_id}:{self.outcome.value}:{self.attempts}:{self.executed_at}"
            self.result_hash = hashlib.sha256(raw.encode()).hexdigest()

    @property
    def can_retry(self) -> bool:
        return self.attempts < self.max_attempts and self.outcome == StepOutcome.FAILURE

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "target_provider": self.target_provider,
            "outcome": self.outcome.value,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "can_retry": self.can_retry,
            "error_message": self.error_message,
            "executed_at": self.executed_at,
            "result_hash": self.result_hash,
        }


@dataclass
class ReconciliationExecution:
    """A full execution of a reconciliation plan."""

    execution_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    plan_id: str = ""
    status: ExecutionStatus = ExecutionStatus.PENDING
    step_results: list[ReconciliationStepResult] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""
    execution_hash: str = ""

    def __post_init__(self) -> None:
        if not self.execution_hash:
            raw = f"{self.execution_id}:{self.plan_id}:{self.status.value}"
            self.execution_hash = hashlib.sha256(raw.encode()).hexdigest()

    @property
    def success_count(self) -> int:
        return sum(1 for s in self.step_results if s.outcome == StepOutcome.SUCCESS)

    @property
    def failure_count(self) -> int:
        return sum(1 for s in self.step_results if s.outcome == StepOutcome.FAILURE)

    @property
    def all_succeeded(self) -> bool:
        return len(self.step_results) > 0 and all(s.outcome == StepOutcome.SUCCESS for s in self.step_results)

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "plan_id": self.plan_id,
            "status": self.status.value,
            "step_results": [s.to_dict() for s in self.step_results],
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "all_succeeded": self.all_succeeded,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "execution_hash": self.execution_hash,
        }


# ── Reconciliation Executor ──────────────────────────────────────────────


class ReconciliationExecutor:
    """Executes reconciliation plans step-by-step with retry and escalation."""

    def __init__(self, max_attempts: int = 3) -> None:
        self._executions: list[ReconciliationExecution] = []
        self._max_attempts = max_attempts
        self._simulate_failures: set[str] = set()

    def set_simulate_failure(self, action_type: str) -> None:
        """Test helper: make a specific action type fail on next execution."""
        self._simulate_failures.add(action_type)

    def clear_simulate_failures(self) -> None:
        self._simulate_failures.clear()

    def execute_plan(
        self,
        plan: ReconciliationPlan,
        simulate_failure: bool = False,
    ) -> ReconciliationExecution:
        """Execute all actions in a reconciliation plan."""
        execution = ReconciliationExecution(
            plan_id=plan.plan_id,
            status=ExecutionStatus.EXECUTING,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        plan.status = PlanStatus.EXECUTING

        for action in plan.actions:
            should_fail = simulate_failure or action.action_type.value in self._simulate_failures
            step = self._execute_action(action, should_fail)
            execution.step_results.append(step)

        # Determine final status
        if execution.all_succeeded:
            execution.status = ExecutionStatus.COMPLETED
            plan.status = PlanStatus.COMPLETED
        elif execution.failure_count > 0:
            # Check if any failures can be retried
            has_retryable = any(s.can_retry for s in execution.step_results)
            if has_retryable:
                execution.status = ExecutionStatus.RETRYING
            else:
                execution.status = ExecutionStatus.FAILED
                plan.status = PlanStatus.FAILED
        execution.completed_at = datetime.now(timezone.utc).isoformat()

        self._executions.append(execution)
        return execution

    def execute_step(
        self,
        execution_id: str,
        action: ReconciliationAction,
        simulate_failure: bool = False,
    ) -> ReconciliationStepResult:
        """Execute a single action and append to an existing execution."""
        execution = self.get_execution(execution_id)
        if execution is None:
            return ReconciliationStepResult(
                action_id=action.action_id,
                outcome=StepOutcome.FAILURE,
                error_message="Execution not found",
            )
        step = self._execute_action(action, simulate_failure)
        execution.step_results.append(step)
        return step

    def retry_step(self, execution_id: str, step_id: str) -> ReconciliationStepResult | None:
        """Retry a failed step within an execution."""
        execution = self.get_execution(execution_id)
        if execution is None:
            return None

        for i, step in enumerate(execution.step_results):
            if step.step_id == step_id and step.can_retry:
                new_step = ReconciliationStepResult(
                    step_id=step.step_id,
                    action_id=step.action_id,
                    action_type=step.action_type,
                    target_provider=step.target_provider,
                    outcome=StepOutcome.SUCCESS,
                    attempts=step.attempts + 1,
                    max_attempts=step.max_attempts,
                )
                execution.step_results[i] = new_step

                # Re-evaluate execution status
                if execution.all_succeeded:
                    execution.status = ExecutionStatus.COMPLETED
                return new_step
        return None

    def escalate_step(self, execution_id: str, step_id: str, reason: str = "") -> ReconciliationStepResult | None:
        """Escalate a failed step to human intervention."""
        execution = self.get_execution(execution_id)
        if execution is None:
            return None

        for i, step in enumerate(execution.step_results):
            if step.step_id == step_id and step.outcome == StepOutcome.FAILURE:
                escalated = ReconciliationStepResult(
                    step_id=step.step_id,
                    action_id=step.action_id,
                    action_type=ReconciliationActionType.ESCALATE_HUMAN,
                    target_provider=step.target_provider,
                    outcome=StepOutcome.SKIPPED,
                    attempts=step.attempts,
                    max_attempts=step.max_attempts,
                    error_message=f"Escalated: {reason}" if reason else f"Escalated from {step.action_type.value}",
                )
                execution.step_results[i] = escalated
                execution.status = ExecutionStatus.ESCALATED
                return escalated
        return None

    # ── queries ───────────────────────────────────────────────────────

    def get_execution(self, execution_id: str) -> ReconciliationExecution | None:
        for e in self._executions:
            if e.execution_id == execution_id:
                return e
        return None

    def get_executions(
        self,
        plan_id: str = "",
        status: ExecutionStatus | None = None,
    ) -> list[ReconciliationExecution]:
        results = self._executions
        if plan_id:
            results = [e for e in results if e.plan_id == plan_id]
        if status is not None:
            results = [e for e in results if e.status == status]
        return results

    @property
    def execution_count(self) -> int:
        return len(self._executions)

    # ── helpers ───────────────────────────────────────────────────────

    def _execute_action(
        self,
        action: ReconciliationAction,
        simulate_failure: bool = False,
    ) -> ReconciliationStepResult:
        if simulate_failure:
            return ReconciliationStepResult(
                action_id=action.action_id,
                action_type=action.action_type,
                target_provider=action.target_provider,
                outcome=StepOutcome.FAILURE,
                max_attempts=self._max_attempts,
                error_message=f"Simulated failure for {action.action_type.value}",
            )
        return ReconciliationStepResult(
            action_id=action.action_id,
            action_type=action.action_type,
            target_provider=action.target_provider,
            outcome=StepOutcome.SUCCESS,
            max_attempts=self._max_attempts,
        )


# ── Module singleton ──────────────────────────────────────────────────────

_reconciliation_executor: ReconciliationExecutor | None = None


def get_reconciliation_executor() -> ReconciliationExecutor:
    global _reconciliation_executor
    if _reconciliation_executor is None:
        _reconciliation_executor = ReconciliationExecutor()
    return _reconciliation_executor
