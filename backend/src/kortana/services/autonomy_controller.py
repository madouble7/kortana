"""
KOR'TANA autonomy controller.

Builds an operational self-model from self-awareness, learner insights,
goal state, and operator directives, then recommends runtime controls for
the always-on daemon.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any

from src.kortana.logger import get_logger
from src.kortana.services.adaptive_learner import get_adaptive_learner
from src.kortana.services.goal_manager import GoalManager, get_goal_manager
from src.kortana.services.operator_directive_service import (
    DirectiveSummary,
    get_active_operator_summary,
)
from src.kortana.services.self_awareness import get_self_awareness

logger = get_logger(__name__)


class AutonomyController:
    """Closed-loop runtime controller for always-on autonomy."""

    def __init__(self, orchestrator: Any | None = None) -> None:
        self.orchestrator = orchestrator
        self.is_diagnosing = False
        self._last_reflection: dict[str, Any] | None = None
        self._history: list[dict[str, Any]] = []

    async def reflect(
        self,
        current_controls: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        controls = {
            "max_tasks_per_cycle": int((current_controls or {}).get("max_tasks_per_cycle", 3)),
            "dry_run_mode": bool((current_controls or {}).get("dry_run_mode", False)),
        }
        assessment = await get_self_awareness().assess()
        learner = await get_adaptive_learner()
        insights = [asdict(item) for item in learner.generate_insights()]
        goal_manager = get_goal_manager()
        await goal_manager.ensure_loaded()
        operator_summary = await get_active_operator_summary()

        recommended_controls = self._recommend_controls(
            assessment=assessment,
            insights=insights,
            current_controls=controls,
            operator_summary=operator_summary,
        )
        current_focus = self._select_focus(
            goal_manager=goal_manager,
            assessment=assessment,
            operator_summary=operator_summary,
        )
        constraints = self._derive_constraints(assessment, operator_summary)
        autonomy_index = self._compute_autonomy_index(
            assessment=assessment,
            insights=insights,
            operator_summary=operator_summary,
        )

        reflection = {
            "generated_at": datetime.utcnow().isoformat(),
            "autonomy_index": autonomy_index,
            "assessment": assessment,
            "insights": insights,
            "recommended_controls": recommended_controls,
            "current_focus": current_focus,
            "constraints": constraints,
            "operator_guidance": {
                "protocol_version": operator_summary.protocol_version,
                "active_count": operator_summary.active_count,
                "pause_requested": operator_summary.pause_requested,
                "focus_topics": operator_summary.focus_topics,
                "avoid_topics": operator_summary.avoid_topics,
                "max_tasks_override": operator_summary.max_tasks_override,
                "execution_mode": operator_summary.execution_mode,
                "approval_mode": operator_summary.approval_mode,
                "approval_required": operator_summary.approval_required,
                "handoff_rules": operator_summary.handoff_rules,
                "override_mode": operator_summary.override_mode,
            },
            "goal_status": goal_manager.get_status(),
        }
        self._last_reflection = reflection
        self._history.append(reflection)
        self._history = self._history[-20:]
        return reflection

    def handle_system_failure(self, failure_context: dict[str, Any]) -> None:
        if self.is_diagnosing:
            return

        self.is_diagnosing = True
        try:
            if self.orchestrator:
                self.orchestrator.remediate(failure_context)
        finally:
            self.is_diagnosing = False

    def get_status(self) -> dict[str, Any]:
        return {
            "last_reflection": self._last_reflection,
            "reflections_recorded": len(self._history),
            "is_diagnosing": self.is_diagnosing,
            "history": self._history[-5:],
        }

    @staticmethod
    def _recommend_controls(
        *,
        assessment: dict[str, Any],
        insights: list[dict[str, Any]],
        current_controls: dict[str, Any],
        operator_summary: DirectiveSummary,
    ) -> dict[str, Any]:
        state = str(assessment.get("state", "nominal"))
        snapshot = assessment.get("snapshot", {})
        corrections = assessment.get("corrections", [])

        max_tasks = max(1, int(current_controls.get("max_tasks_per_cycle", 3)))
        dry_run_mode = bool(current_controls.get("dry_run_mode", False))
        focus_mode = "execute"

        if operator_summary.pause_requested:
            return {
                "dry_run_mode": True,
                "max_tasks_per_cycle": 1,
                "focus_mode": "observe",
            }
        if operator_summary.override_mode == "halt":
            return {
                "dry_run_mode": True,
                "max_tasks_per_cycle": 1,
                "focus_mode": "observe",
            }

        if state == "critical":
            max_tasks = 1
            dry_run_mode = True
            focus_mode = "stabilize"
        elif state == "degraded":
            max_tasks = min(max_tasks, 2)
            dry_run_mode = dry_run_mode or any(
                correction.get("action") == "enable_dry_run_mode"
                for correction in corrections
            )
            focus_mode = "stabilize"
        else:
            backlog = int(snapshot.get("pending_tasks", 0) or 0)
            fast_path = any(
                insight.get("category") == "timing"
                and "Increase concurrency" in str(insight.get("recommendation", ""))
                for insight in insights
            )
            if backlog >= max_tasks and fast_path:
                max_tasks = max(max_tasks + 1, 3)
            elif backlog > 0:
                max_tasks = max(max_tasks, 2)
            dry_run_mode = False
            focus_mode = "execute"

        if operator_summary.max_tasks_override is not None:
            max_tasks = max(1, int(operator_summary.max_tasks_override))
        if operator_summary.execution_mode == "observe":
            dry_run_mode = True
            focus_mode = "observe"
        elif operator_summary.execution_mode == "plan":
            dry_run_mode = True
            focus_mode = "plan"
        elif operator_summary.approval_required:
            dry_run_mode = True
            focus_mode = "review"

        return {
            "dry_run_mode": dry_run_mode,
            "max_tasks_per_cycle": max_tasks,
            "focus_mode": focus_mode,
        }

    @staticmethod
    def _select_focus(
        *,
        goal_manager: GoalManager,
        assessment: dict[str, Any],
        operator_summary: DirectiveSummary,
    ) -> dict[str, Any]:
        state = str(assessment.get("state", "nominal"))
        snapshot = assessment.get("snapshot", {})

        if operator_summary.pause_requested:
            return {
                "title": "Hold autonomous execution",
                "mode": "observe",
                "reason": "Operator pause directive is active",
            }
        if operator_summary.override_mode == "halt":
            return {
                "title": "Hold autonomous execution",
                "mode": "observe",
                "reason": "Operator override halt is active",
            }
        if operator_summary.execution_mode == "plan":
            return {
                "title": "Plan work without execution",
                "mode": "plan",
                "reason": "Operator requested plan-only mode",
            }
        if operator_summary.approval_required:
            return {
                "title": "Stage work for operator review",
                "mode": "review",
                "reason": "Operator approval is required before execution",
            }
        if state in {"critical", "degraded"}:
            return {
                "title": "Stabilize autonomous runtime",
                "mode": "stabilize",
                "reason": "System health requires protective controls",
            }
        if operator_summary.focus_topics:
            return {
                "title": "Execute operator-directed focus backlog",
                "mode": "execute",
                "reason": "Operator steering is active",
                "topics": operator_summary.focus_topics,
            }
        next_goal = goal_manager.next_goal()
        if int(snapshot.get("pending_tasks", 0) or 0) > 0:
            return {
                "title": "Process autonomous task backlog",
                "mode": "execute",
                "reason": "Healthy runtime with pending work",
                "goal": asdict(next_goal) if next_goal else None,
            }
        if next_goal is not None:
            return {
                "title": next_goal.title,
                "mode": "execute",
                "reason": "Highest-priority active goal",
                "goal": asdict(next_goal),
            }
        return {
            "title": "Maintain autonomous readiness",
            "mode": "observe",
            "reason": "No active backlog detected",
        }

    @staticmethod
    def _derive_constraints(
        assessment: dict[str, Any],
        operator_summary: DirectiveSummary,
    ) -> list[str]:
        constraints: list[str] = []
        state = str(assessment.get("state", "nominal"))
        corrections = assessment.get("corrections", [])

        if state == "critical":
            constraints.append("System is in a critical state; live mutation should be minimized.")
        elif state == "degraded":
            constraints.append("System is degraded; throttle concurrency and prefer reversible work.")

        for correction in corrections:
            reason = correction.get("reason")
            if reason:
                constraints.append(str(reason))

        if operator_summary.avoid_topics:
            constraints.append(
                "Avoid topics: " + ", ".join(operator_summary.avoid_topics) + "."
            )
        if operator_summary.execution_mode == "observe":
            constraints.append("Observe-only mode is active; do not execute tasks.")
        if operator_summary.execution_mode == "plan":
            constraints.append("Plan-only mode is active; generate plans without execution.")
        if operator_summary.approval_required:
            constraints.append("Manual approval is required before execution.")
        if operator_summary.pause_requested:
            constraints.append("Execution is paused by operator directive.")

        return constraints

    @staticmethod
    def _compute_autonomy_index(
        *,
        assessment: dict[str, Any],
        insights: list[dict[str, Any]],
        operator_summary: DirectiveSummary,
    ) -> int:
        state = str(assessment.get("state", "nominal"))
        snapshot = assessment.get("snapshot", {})
        capabilities = assessment.get("capabilities", {})

        base = {
            "critical": 20,
            "degraded": 45,
            "recovering": 65,
            "nominal": 75,
        }.get(state, 60)

        success_rate = float(snapshot.get("success_rate", 0.0) or 0.0)
        capability_ratio = (
            sum(1 for value in capabilities.values() if value) / len(capabilities)
            if capabilities
            else 0.0
        )
        quality_bonus = min(8, len(insights) * 2)
        pause_penalty = 10 if operator_summary.pause_requested else 0
        focus_penalty = 3 if operator_summary.focus_topics or operator_summary.avoid_topics else 0

        index = (
            base
            + round((success_rate - 80.0) * 0.4)
            + round(capability_ratio * 12)
            + quality_bonus
            - pause_penalty
            - focus_penalty
        )
        return max(0, min(100, index))


controller = AutonomyController()


def get_autonomy_controller() -> AutonomyController:
    return controller
