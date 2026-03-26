"""
KOR'TANA Autonomy Controller

Closes the loop between introspection, learning, goals, and daemon controls.
It does not claim sentience; it maintains an operational self-model that the
runtime can use to tune its own behavior.
"""

from __future__ import annotations

import inspect
import os
from dataclasses import asdict
from datetime import datetime
from typing import Any

from src.kortana.logger import get_logger
from src.kortana.services.adaptive_learner import get_adaptive_learner
from src.kortana.services.goal_manager import Goal, GoalStatus, GoalTier, get_goal_manager
from src.kortana.services.operator_directive_service import (
    DirectiveSummary,
    get_active_operator_summary,
)
from src.kortana.services.self_awareness import get_self_awareness

logger = get_logger(__name__)

_MANAGED_BY = "autonomy_controller"


class AutonomyController:
    """Maintains a live operational self-model and control recommendations."""

    def __init__(self) -> None:
        self._history: list[dict[str, Any]] = []
        self._last_reflection: dict[str, Any] | None = None
        self._max_history = int(os.getenv("AUTONOMY_REFLECTION_HISTORY", "50"))
        self._min_tasks = int(os.getenv("AUTONOMY_MIN_TASKS_PER_CYCLE", "1"))
        self._max_tasks_cap = int(os.getenv("AUTONOMY_MAX_TASKS_CAP", "6"))

    async def reflect(
        self, daemon_status: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Build a current self-model and recommend daemon controls."""
        if daemon_status is None:
            daemon_status = self._get_daemon_status()

        assessment = await get_self_awareness().assess()
        learner = await get_adaptive_learner()
        operator_summary = get_active_operator_summary()
        if inspect.isawaitable(operator_summary):
            operator_summary = await operator_summary
        operator_course = self._directive_summary_to_course(operator_summary)
        insights = [asdict(insight) for insight in learner.generate_insights()]
        goal_manager = get_goal_manager()

        self._sync_managed_goals(goal_manager, assessment["state"], assessment["snapshot"])
        self._sync_operator_goal(goal_manager, operator_course)
        goal_manager.reprioritise(assessment["state"], insights)
        current_focus = goal_manager.next_goal()
        controls = self._recommend_controls(
            assessment, insights, daemon_status, operator_course
        )
        constraints = self._derive_constraints(
            assessment, daemon_status, operator_course
        )
        autonomy_index = self._compute_autonomy_index(
            assessment=assessment,
            daemon_status=daemon_status,
            goal_status=goal_manager.get_status(),
        )

        reflection = {
            "timestamp": datetime.utcnow().isoformat(),
            "state": assessment["state"],
            "autonomy_index": autonomy_index,
            "current_focus": self._goal_to_dict(current_focus),
            "constraints": constraints,
            "recommended_controls": controls,
            "capabilities": assessment["capabilities"],
            "snapshot": assessment["snapshot"],
            "corrections": assessment["corrections"],
            "top_insights": insights[:3],
            "operator_course": operator_course,
            "goal_status": goal_manager.get_status(),
            "daemon": self._summarize_daemon_status(daemon_status),
        }

        self._last_reflection = reflection
        self._history.append(
            {
                "timestamp": reflection["timestamp"],
                "state": reflection["state"],
                "autonomy_index": reflection["autonomy_index"],
                "focus": (
                    reflection["current_focus"]["title"]
                    if reflection["current_focus"]
                    else None
                ),
                "recommended_controls": reflection["recommended_controls"],
            }
        )
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

        logger.info(
            "Autonomy reflection complete: "
            f"state={reflection['state']} "
            f"autonomy_index={reflection['autonomy_index']} "
            f"max_tasks={controls['max_tasks_per_cycle']} "
            f"dry_run={controls['dry_run_mode']}"
        )
        return reflection

    def get_status(self) -> dict[str, Any]:
        """Lightweight controller status."""
        return {
            "history_length": len(self._history),
            "min_tasks_per_cycle": self._min_tasks,
            "max_tasks_cap": self._max_tasks_cap,
            "last_reflection": self._last_reflection,
        }

    def get_history(self, limit: int = 10) -> list[dict[str, Any]]:
        return self._history[-limit:]

    def _recommend_controls(
        self,
        assessment: dict[str, Any],
        insights: list[dict[str, Any]],
        daemon_status: dict[str, Any],
        operator_course: dict[str, Any],
    ) -> dict[str, Any]:
        snapshot = assessment["snapshot"]
        current_max = int(daemon_status.get("max_tasks_per_cycle", 3) or 3)
        max_tasks = current_max
        dry_run_mode = bool(daemon_status.get("dry_run_mode", False))
        focus_mode = "execute"
        rationale: list[str] = []

        state = assessment["state"]
        if operator_course.get("paused"):
            max_tasks = self._min_tasks
            dry_run_mode = True
            focus_mode = "hold"
            rationale.append("operator requested pause")

        if state == "critical":
            max_tasks = self._min_tasks
            dry_run_mode = True
            focus_mode = "stabilize"
            rationale.append("critical system state")
        elif state in {"degraded", "recovering"}:
            max_tasks = max(self._min_tasks, min(current_max, 2))
            focus_mode = "stabilize"
            rationale.append(f"{state} system state")
        else:
            dry_run_mode = False
            if (
                snapshot.get("cpu_percent", 100) < 65
                and snapshot.get("memory_percent", 100) < 75
                and snapshot.get("success_rate", 0) >= 90
            ):
                max_tasks = min(self._max_tasks_cap, max(current_max, 2) + 1)
                rationale.append("healthy runtime with strong success rate")

        for correction in assessment.get("corrections", []):
            action = correction.get("action")
            if action == "reduce_concurrent_tasks":
                max_tasks = min(
                    max_tasks,
                    int(correction.get("params", {}).get("max_tasks_per_cycle", 1)),
                )
                focus_mode = "stabilize"
                rationale.append(correction.get("reason", "reduce concurrency"))
            elif action == "enable_dry_run_mode":
                dry_run_mode = True
                focus_mode = "stabilize"
                rationale.append(correction.get("reason", "protective dry-run mode"))

        if snapshot.get("pending_tasks", 0) == 0 and focus_mode != "stabilize":
            focus_mode = "observe"
            rationale.append("no task backlog")
        elif (
            operator_course.get("latest_directive") is not None
            and focus_mode not in {"stabilize", "hold"}
        ):
            focus_mode = "align_with_operator"
            rationale.append("operator guidance is active")

        for insight in insights:
            if (
                insight.get("category") == "timing"
                and "Increase concurrency" in insight.get("recommendation", "")
                and state == "nominal"
                and not dry_run_mode
            ):
                max_tasks = min(self._max_tasks_cap, max_tasks + 1)
                rationale.append(insight["summary"])
                break

        max_tasks = max(self._min_tasks, min(self._max_tasks_cap, max_tasks))
        return {
            "max_tasks_per_cycle": max_tasks,
            "dry_run_mode": dry_run_mode,
            "focus_mode": focus_mode,
            "rationale": rationale[:4],
        }

    @staticmethod
    def _directive_summary_to_course(summary: DirectiveSummary) -> dict[str, Any]:
        latest = summary.directives[0] if summary.directives else None
        keywords = list(dict.fromkeys(summary.focus_topics + summary.avoid_topics))
        text_summary = summary.prompt_preamble or " | ".join(summary.notes[:3])
        return {
            "paused": summary.pause_requested,
            "directive_count": summary.active_count,
            "latest_directive": latest,
            "keywords": keywords,
            "summary": text_summary or "No active operator direction",
            "focus_topics": summary.focus_topics,
            "avoid_topics": summary.avoid_topics,
            "notes": summary.notes,
        }

    def _derive_constraints(
        self,
        assessment: dict[str, Any],
        daemon_status: dict[str, Any],
        operator_course: dict[str, Any],
    ) -> list[str]:
        snapshot = assessment["snapshot"]
        capabilities = assessment["capabilities"]
        constraints: list[str] = []

        if operator_course.get("paused"):
            constraints.append("Operator has paused forward execution")
        if not capabilities.get("github_integration"):
            constraints.append("GitHub integration is unavailable")
        if not capabilities.get("ai_providers"):
            constraints.append("No multi-provider AI routing is available")
        if snapshot.get("pending_tasks", 0) > max(
            3, int(daemon_status.get("max_tasks_per_cycle", 1) or 1) * 3
        ):
            constraints.append(
                f"Task backlog pressure: {snapshot['pending_tasks']} pending tasks"
            )
        for correction in assessment.get("corrections", []):
            constraints.append(correction.get("reason", "runtime correction required"))

        return constraints[:5]

    def _compute_autonomy_index(
        self,
        *,
        assessment: dict[str, Any],
        daemon_status: dict[str, Any],
        goal_status: dict[str, Any],
    ) -> float:
        snapshot = assessment["snapshot"]
        capabilities = assessment["capabilities"]

        capability_score = sum(1 for enabled in capabilities.values() if enabled) / max(
            len(capabilities), 1
        )
        success_score = min(float(snapshot.get("success_rate", 0)) / 100.0, 1.0)
        state_score = {
            "nominal": 1.0,
            "recovering": 0.75,
            "degraded": 0.45,
            "critical": 0.15,
        }.get(assessment["state"], 0.3)
        goal_score = goal_status.get("completed", 0) / max(goal_status.get("total_goals", 1), 1)
        queue_penalty = min(
            snapshot.get("pending_tasks", 0)
            / max(int(daemon_status.get("max_tasks_per_cycle", 1) or 1) * 10, 1),
            1.0,
        )

        score = (
            capability_score * 30
            + success_score * 35
            + state_score * 20
            + min(goal_score, 1.0) * 10
            + (1 - queue_penalty) * 5
        )
        return round(score, 1)

    def _sync_managed_goals(
        self, goal_manager: Any, state: str, snapshot: dict[str, Any]
    ) -> None:
        self._sync_stability_goal(goal_manager, state, snapshot)
        self._sync_backlog_goal(goal_manager, snapshot)

    def _sync_operator_goal(
        self, goal_manager: Any, operator_course: dict[str, Any]
    ) -> None:
        goal = self._find_managed_goal(goal_manager, "operator_direction")
        latest = operator_course.get("latest_directive")
        if latest is None:
            if goal is not None and goal.status == GoalStatus.ACTIVE:
                goal_manager.complete(goal.id)
            return

        description = latest.get("content") or operator_course.get("summary", "")
        metadata = {
            "managed_by": _MANAGED_BY,
            "kind": "operator_direction",
            "directive_id": latest.get("id"),
            "directive_mode": latest.get("directive_type"),
        }
        if goal is None:
            goal_manager.create(
                title="Follow operator direction",
                tier=GoalTier.IMMEDIATE,
                description=description,
                success_criteria="Operator direction is satisfied or superseded",
                progress=0.0,
                priority=99,
                metadata=metadata,
            )
        else:
            goal_manager.update(
                goal.id,
                description=description,
                priority=99,
                metadata={**goal.metadata, **metadata},
            )

    def _sync_stability_goal(
        self, goal_manager: Any, state: str, snapshot: dict[str, Any]
    ) -> None:
        goal = self._find_managed_goal(goal_manager, "stability")
        if state in {"critical", "degraded", "recovering"}:
            priority = 96 if state == "critical" else 88
            progress = {"critical": 0.05, "degraded": 0.35, "recovering": 0.7}[state]
            description = (
                "Keep the autonomous runtime healthy enough to continue self-directed work. "
                f"CPU={snapshot.get('cpu_percent', 0):.1f}% "
                f"MEM={snapshot.get('memory_percent', 0):.1f}% "
                f"success_rate={snapshot.get('success_rate', 0):.1f}%"
            )
            metadata = {
                "managed_by": _MANAGED_BY,
                "kind": "stability",
                "state": state,
            }
            if goal is None:
                goal_manager.create(
                    title="Stabilize autonomous runtime",
                    tier=GoalTier.TACTICAL,
                    description=description,
                    success_criteria="Return to nominal state with healthy success rate",
                    progress=progress,
                    priority=priority,
                    metadata=metadata,
                )
            else:
                goal_manager.update(
                    goal.id,
                    description=description,
                    progress=progress,
                    priority=priority,
                    metadata={**goal.metadata, **metadata},
                )
        elif goal is not None and goal.status == GoalStatus.ACTIVE:
            goal_manager.complete(goal.id)

    def _sync_backlog_goal(self, goal_manager: Any, snapshot: dict[str, Any]) -> None:
        goal = self._find_managed_goal(goal_manager, "backlog")
        pending = int(snapshot.get("pending_tasks", 0) or 0)
        completed = int(snapshot.get("completed_tasks", 0) or 0)
        failed = int(snapshot.get("failed_tasks", 0) or 0)
        total_seen = max(pending + completed + failed, 1)

        if pending > 0:
            progress = round(1 - (pending / total_seen), 3)
            priority = min(92, 72 + pending)
            description = f"Reduce pending GitHub backlog from {pending} task(s) toward zero."
            metadata = {
                "managed_by": _MANAGED_BY,
                "kind": "backlog",
                "pending_tasks": pending,
            }
            if goal is None:
                goal_manager.create(
                    title="Process autonomous task backlog",
                    tier=GoalTier.IMMEDIATE,
                    description=description,
                    success_criteria="pending_tasks == 0",
                    progress=progress,
                    priority=priority,
                    metadata=metadata,
                )
            else:
                goal_manager.update(
                    goal.id,
                    description=description,
                    progress=progress,
                    priority=priority,
                    metadata={**goal.metadata, **metadata},
                )
        elif goal is not None and goal.status == GoalStatus.ACTIVE:
            goal_manager.complete(goal.id)

    def _find_managed_goal(self, goal_manager: Any, kind: str) -> Goal | None:
        for goal in goal_manager.all():
            metadata = goal.metadata or {}
            if (
                metadata.get("managed_by") == _MANAGED_BY
                and metadata.get("kind") == kind
                and goal.status in {GoalStatus.ACTIVE, GoalStatus.BLOCKED}
            ):
                return goal
        return None

    def _get_daemon_status(self) -> dict[str, Any]:
        try:
            from src.kortana.services.autonomy_daemon import get_autonomy_daemon

            return get_autonomy_daemon().get_status()
        except Exception as exc:
            logger.debug(f"Autonomy controller could not read daemon status: {exc}")
            return {}

    @staticmethod
    def _goal_to_dict(goal: Goal | None) -> dict[str, Any] | None:
        return asdict(goal) if goal is not None else None

    @staticmethod
    def _summarize_daemon_status(daemon_status: dict[str, Any]) -> dict[str, Any]:
        return {
            "running": daemon_status.get("running", False),
            "cycle_interval_seconds": daemon_status.get("cycle_interval_seconds"),
            "max_tasks_per_cycle": daemon_status.get("max_tasks_per_cycle"),
            "dry_run_mode": daemon_status.get("dry_run_mode", False),
            "cycles_completed": daemon_status.get("cycles_completed", 0),
            "tasks_processed": daemon_status.get("tasks_processed", 0),
        }


_controller: AutonomyController | None = None


def get_autonomy_controller() -> AutonomyController:
    global _controller
    if _controller is None:
        _controller = AutonomyController()
    return _controller
