"""
KOR'TANA Goal Manager

Gives KOR'TANA hierarchical, persistent goals with autonomous prioritisation:

  - Strategic goals (long-term vision, e.g. "100% test coverage")
  - Tactical goals (medium-term, e.g. "fix all open P1 bugs")
  - Immediate goals (derived from GitHub issues & daemon cycles)

Each goal tracks progress, dependencies, and completion criteria.
The manager re-prioritises every cycle based on Self-Awareness state
and Adaptive Learner insights.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import select

from src.kortana.logger import get_logger

logger = get_logger(__name__)


def _parse_iso_datetime(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class GoalTier(str, Enum):
    STRATEGIC = "strategic"
    TACTICAL = "tactical"
    IMMEDIATE = "immediate"


class GoalStatus(str, Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass
class Goal:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    tier: GoalTier = GoalTier.IMMEDIATE
    status: GoalStatus = GoalStatus.ACTIVE
    description: str = ""
    success_criteria: str = ""
    progress: float = 0.0  # 0.0 – 1.0
    priority: int = 50  # 0 = lowest, 100 = highest
    parent_id: str | None = None
    depends_on: list[str] = field(default_factory=list)
    linked_tasks: list[str] = field(default_factory=list)  # GitHubTask IDs
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------


class GoalManager:
    """Hierarchical goal tracking and autonomous prioritisation."""

    # Kor'tana's canonical sacred values — used to align goal prioritisation with identity
    IDENTITY_VALUES: list[str] = [
        "love",
        "unity",
        "cohesiveness",
        "knowledge",
        "humility",
        "truthfulness",
        "stewardship",
        "interconnectedness",
    ]

    def __init__(self) -> None:
        self._goals: dict[str, Goal] = {}

    # ----- persistence (async) -----

    @staticmethod
    def _normalize_goal_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
        out = dict(kwargs)
        if "tier" in out and isinstance(out["tier"], str):
            out["tier"] = GoalTier(out["tier"])
        if "status" in out and isinstance(out["status"], str):
            out["status"] = GoalStatus(out["status"])
        return out

    def _goal_from_row(self, row: Any) -> Goal:
        """Hydrate a Goal dataclass from an AutonomyGoal ORM row."""
        r = row
        ca = r.created_at.isoformat() if r.created_at else datetime.utcnow().isoformat()
        ua = r.updated_at.isoformat() if r.updated_at else datetime.utcnow().isoformat()
        comp = r.completed_at.isoformat() if r.completed_at else None
        return Goal(
            id=str(r.id),
            title=str(r.title),
            tier=GoalTier(str(r.tier)),
            status=GoalStatus(str(r.status)),
            description=str(r.description or ""),
            success_criteria=str(r.success_criteria or ""),
            progress=float(r.progress or 0.0),
            priority=int(r.priority),
            parent_id=r.parent_id,
            depends_on=list(r.depends_on or []),
            linked_tasks=list(r.linked_tasks or []),
            created_at=ca,
            updated_at=ua,
            completed_at=comp,
            metadata=dict(getattr(r, "goal_metadata", None) or {}),
        )

    def _goals_in_persist_order(self) -> list[Goal]:
        """Parents before children so FK inserts succeed."""
        goals = list(self._goals.values())
        ids = {g.id for g in goals}
        remaining: dict[str, Goal] = {g.id: g for g in goals}
        ordered: list[Goal] = []
        while remaining:
            ready = [
                g
                for g in remaining.values()
                if g.parent_id is None
                or g.parent_id not in ids
                or g.parent_id not in remaining
            ]
            if not ready:
                ready = list(remaining.values())
            for g in sorted(ready, key=lambda x: x.id):
                ordered.append(g)
                del remaining[g.id]
        return ordered

    async def persist_goal(self, goal: Goal) -> None:
        """Upsert one goal row."""
        from src.kortana.database import get_db_manager
        from src.kortana.models import AutonomyGoal as AG

        db = get_db_manager()
        async with db.session_scope() as session:
            result = await session.execute(select(AG).where(AG.id == goal.id))
            existing = result.scalar_one_or_none()
            is_new = existing is None
            ag: Any
            if is_new:
                ag = AG(id=goal.id)
                session.add(ag)
            else:
                ag = existing
            ag.title = goal.title
            ag.tier = goal.tier.value
            ag.status = goal.status.value
            ag.description = goal.description
            ag.success_criteria = goal.success_criteria
            ag.progress = goal.progress
            ag.priority = goal.priority
            ag.parent_id = goal.parent_id
            ag.depends_on = goal.depends_on
            ag.linked_tasks = goal.linked_tasks
            ag.goal_metadata = goal.metadata
            ag.completed_at = _parse_iso_datetime(goal.completed_at)
            ag.updated_at = datetime.utcnow()
            if is_new:
                ag.created_at = _parse_iso_datetime(goal.created_at) or datetime.utcnow()

    async def persist_all_goals(self) -> None:
        """Persist every in-memory goal (e.g. after reprioritise or bootstrap)."""
        for g in self._goals_in_persist_order():
            await self.persist_goal(g)

    async def load_from_db(self) -> None:
        """Load goals from DB or seed defaults and persist."""
        from src.kortana.database import get_db_manager
        from src.kortana.models import AutonomyGoal as AG

        db = get_db_manager()
        try:
            async with db.session_scope() as session:
                result = await session.execute(select(AG))
                rows = list(result.scalars().all())
        except Exception as exc:
            logger.warning(f"Goal load_from_db failed: {exc}")
            return

        if not rows:
            self._goals.clear()
            self.bootstrap_defaults()
            await self.persist_all_goals()
            logger.info("Goals: empty DB — bootstrapped defaults and persisted")
            return

        self._goals.clear()
        for row in rows:
            g = self._goal_from_row(row)
            self._goals[g.id] = g
        logger.info(f"Goals: loaded {len(self._goals)} rows from database")

    async def ensure_loaded(self) -> None:
        """Guarantee the in-memory graph is hydrated before async reads/writes."""
        if self._goals:
            return
        await self.load_from_db()

    # ----- CRUD -----

    def create(self, **kwargs: Any) -> Goal:
        kwargs = self._normalize_goal_kwargs(kwargs)
        goal = Goal(**kwargs)
        self._goals[goal.id] = goal
        logger.info(f"Goal created: [{goal.tier.value}] {goal.title} (id={goal.id})")
        return goal

    def get(self, goal_id: str) -> Goal | None:
        return self._goals.get(goal_id)

    def all(self) -> list[Goal]:
        """Return every goal regardless of state."""
        return list(self._goals.values())

    def update(self, goal_id: str, **kwargs: Any) -> Goal | None:
        goal = self._goals.get(goal_id)
        if not goal:
            return None
        for k, v in kwargs.items():
            if hasattr(goal, k):
                setattr(goal, k, v)
        goal.updated_at = datetime.utcnow().isoformat()
        return goal

    def complete(self, goal_id: str) -> Goal | None:
        goal = self._goals.get(goal_id)
        if not goal:
            return None
        goal.status = GoalStatus.COMPLETED
        goal.progress = 1.0
        goal.completed_at = datetime.utcnow().isoformat()
        goal.updated_at = goal.completed_at
        logger.info(f"Goal completed: {goal.title} (id={goal.id})")
        # Auto-advance parent progress
        if goal.parent_id:
            self._recalc_parent_progress(goal.parent_id)
        return goal

    def abandon(self, goal_id: str, reason: str = "") -> Goal | None:
        goal = self._goals.get(goal_id)
        if not goal:
            return None
        goal.status = GoalStatus.ABANDONED
        goal.metadata["abandon_reason"] = reason
        goal.updated_at = datetime.utcnow().isoformat()
        logger.info(f"Goal abandoned: {goal.title} — {reason}")
        return goal

    # ----- queries -----

    def active(self, tier: GoalTier | None = None) -> list[Goal]:
        goals = [g for g in self._goals.values() if g.status == GoalStatus.ACTIVE]
        if tier:
            goals = [g for g in goals if g.tier == tier]
        return sorted(goals, key=lambda g: g.priority, reverse=True)

    def by_tier(self, tier: GoalTier) -> list[Goal]:
        return [g for g in self._goals.values() if g.tier == tier]

    def children(self, parent_id: str) -> list[Goal]:
        return [g for g in self._goals.values() if g.parent_id == parent_id]

    def blocked(self) -> list[Goal]:
        return [g for g in self._goals.values() if g.status == GoalStatus.BLOCKED]

    def next_goal(self) -> Goal | None:
        """Return the highest-priority unblocked active goal."""
        candidates = [
            g
            for g in self._goals.values()
            if g.status == GoalStatus.ACTIVE and self._dependencies_met(g)
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda g: g.priority)

    # ----- prioritisation -----

    def reprioritise(
        self,
        system_state: str = "nominal",
        insights: list[dict[str, Any]] | None = None,
        identity_values: list[str] | None = None,
    ) -> None:
        """Re-score all active goals based on system state, learner insights, and identity.

        Called each autonomy cycle to keep priorities fresh.

        *identity_values* — kor'tana's core_values list (e.g. ``["love", "unity",
        "stewardship"]``).  Goals whose title or description contain any value word
        receive a small +2 alignment boost, reinforcing identity-consistent work.
        """
        state_boost = {"nominal": 0, "degraded": -10, "critical": -20, "recovering": -5}
        boost = state_boost.get(system_state, 0)

        # Normalise identity values once for this cycle
        _identity_words: set[str] = {
            v.lower().strip() for v in (identity_values or []) if v.strip()
        }

        for goal in self._goals.values():
            if goal.status != GoalStatus.ACTIVE:
                continue

            # Base priority stays; apply modifiers
            modifier = boost

            # Boost goals that match learner insights
            if insights:
                for insight in insights:
                    if (
                        insight.get("category") == "quality"
                        and goal.tier == GoalTier.TACTICAL
                    ):
                        modifier += 5
                    if insight.get("category") == "provider_preference":
                        modifier += 2

            # Identity alignment boost — small nudge toward values-consistent goals
            if _identity_words:
                goal_text = f"{goal.title} {getattr(goal, 'description', '')}".lower()
                if any(word in goal_text for word in _identity_words):
                    modifier += 2

            # Immediate goals under critical system get deprioritised
            if system_state == "critical" and goal.tier == GoalTier.IMMEDIATE:
                modifier -= 15

            # Strategic goals are stable
            if goal.tier == GoalTier.STRATEGIC:
                modifier = modifier // 2  # dampen swings

            goal.priority = max(0, min(100, goal.priority + modifier))

        # Check for newly blocked goals
        for goal in self._goals.values():
            if goal.status == GoalStatus.ACTIVE and not self._dependencies_met(goal):
                goal.status = GoalStatus.BLOCKED
            elif goal.status == GoalStatus.BLOCKED and self._dependencies_met(goal):
                goal.status = GoalStatus.ACTIVE

        logger.info(
            f"Reprioritised {len(self.active())} active goals (state={system_state})"
        )

    # ----- task linking -----

    def link_task(self, goal_id: str, task_id: str) -> None:
        goal = self._goals.get(goal_id)
        if goal and task_id not in goal.linked_tasks:
            goal.linked_tasks.append(task_id)

    def update_progress_from_tasks(
        self, goal_id: str, completed_tasks: int, total_tasks: int
    ) -> None:
        goal = self._goals.get(goal_id)
        if goal and total_tasks > 0:
            goal.progress = round(completed_tasks / total_tasks, 3)
            goal.updated_at = datetime.utcnow().isoformat()
            if goal.progress >= 1.0:
                self.complete(goal_id)

    # ----- internals -----

    def _dependencies_met(self, goal: Goal) -> bool:
        for dep_id in goal.depends_on:
            dep = self._goals.get(dep_id)
            if not dep or dep.status != GoalStatus.COMPLETED:
                return False
        return True

    def _recalc_parent_progress(self, parent_id: str) -> None:
        kids = self.children(parent_id)
        if not kids:
            return
        avg = sum(k.progress for k in kids) / len(kids)
        parent = self._goals.get(parent_id)
        if parent:
            parent.progress = round(avg, 3)
            parent.updated_at = datetime.utcnow().isoformat()
            if parent.progress >= 1.0:
                self.complete(parent_id)

    # ----- bootstrap default goals -----

    def bootstrap_defaults(self) -> None:
        """Create KOR'TANA's standing strategic goals if not already set."""
        if any(g.tier == GoalTier.STRATEGIC for g in self._goals.values()):
            return  # Already bootstrapped

        self.create(
            title="Achieve full autonomous operation",
            tier=GoalTier.STRATEGIC,
            description="KOR'TANA operates without human intervention for all AUTO-classified tasks",
            success_criteria="30 consecutive autonomous cycles with 0 failures",
            priority=90,
        )
        self.create(
            title="Maintain 95%+ task success rate",
            tier=GoalTier.STRATEGIC,
            description="Rolling 7-day success rate across all autonomous task types",
            success_criteria="success_rate >= 0.95 over 100+ tasks",
            priority=85,
        )
        self.create(
            title="Resolve all open GitHub issues autonomously",
            tier=GoalTier.TACTICAL,
            description="Process every open issue through the analyze->plan->execute pipeline",
            success_criteria="0 pending GitHub tasks",
            priority=70,
        )
        logger.info("Goal manager bootstrapped with default strategic/tactical goals")

    async def bootstrap_from_db(self) -> None:
        """Read persistent cycle/task stats from DB and update goal progress.

        Called once at daemon startup so progress survives container restarts.
        Goals that meet their criteria are automatically marked COMPLETED.
        """
        try:
            from sqlalchemy import text

            from src.kortana.database import get_db_manager

            await self.ensure_loaded()
            db = get_db_manager()

            async with db.session_scope() as session:
                # --- 1. Consecutive clean cycles (autonomy_cycle_memory) ---
                result = await session.execute(
                    text(
                        "SELECT COUNT(*) as total, "
                        "SUM(CASE WHEN errors_encountered = 0 OR errors_encountered IS NULL THEN 1 ELSE 0 END) as clean "
                        "FROM autonomy_cycle_memory"
                    )
                )
                row = result.fetchone()
                total_cycles = int(row[0] or 0) if row else 0
                clean_cycles = int(row[1] or 0) if row else 0

                # --- 2. Task success rate (github_tasks) ---
                result2 = await session.execute(
                    text(
                        "SELECT COUNT(*) as total, "
                        "SUM(CASE WHEN status IN ('executed', 'completed') THEN 1 ELSE 0 END) as succeeded "
                        "FROM github_tasks"
                    )
                )
                task_row = result2.fetchone()
                total_tasks = int(task_row[0] or 0) if task_row else 0
                success_rate = (
                    (int(task_row[1] or 0) if task_row else 0) / total_tasks
                    if total_tasks > 0
                    else 0.0
                )

            # Update goal progress
            CONSECUTIVE_TARGET = 30
            for goal in self._goals.values():
                if "autonomous operation" in goal.title.lower():
                    progress = min(1.0, clean_cycles / CONSECUTIVE_TARGET)
                    goal.progress = round(progress, 3)
                    goal.metadata["clean_cycles"] = clean_cycles
                    goal.metadata["total_cycles"] = total_cycles
                    if clean_cycles >= CONSECUTIVE_TARGET:
                        self.complete(goal.id)
                    logger.info(
                        f"[goals] autonomous_operation: {clean_cycles}/{CONSECUTIVE_TARGET} "
                        f"clean cycles → progress={goal.progress}"
                    )

                elif "95%" in goal.title or "success rate" in goal.title.lower():
                    goal.progress = round(success_rate, 3)
                    goal.metadata["success_rate"] = success_rate
                    goal.metadata["total_tasks"] = total_tasks
                    if success_rate >= 0.95 and total_tasks >= 100:
                        self.complete(goal.id)
                    logger.info(
                        f"[goals] success_rate: {success_rate:.1%} over {total_tasks} tasks "
                        f"→ progress={goal.progress}"
                    )

            await self.persist_all_goals()

        except Exception as exc:
            logger.warning(f"Goal DB bootstrap failed (non-fatal): {exc}")

    # ----- status -----

    def get_status(self) -> dict[str, Any]:
        return {
            "total_goals": len(self._goals),
            "active": len(self.active()),
            "blocked": len(self.blocked()),
            "completed": len(
                [g for g in self._goals.values() if g.status == GoalStatus.COMPLETED]
            ),
            "by_tier": {tier.value: len(self.by_tier(tier)) for tier in GoalTier},
            "top_3": [
                {
                    "id": g.id,
                    "title": g.title,
                    "tier": g.tier.value,
                    "priority": g.priority,
                    "progress": g.progress,
                }
                for g in self.active()[:3]
            ],
            "next_goal": (lambda g: asdict(g) if g else None)(self.next_goal()),
        }


# Singleton
_manager: GoalManager | None = None


def get_goal_manager() -> GoalManager:
    global _manager
    if _manager is None:
        _manager = GoalManager()
    return _manager


def reset_goal_manager_for_testing() -> None:
    """Clear singleton so tests receive a fresh GoalManager instance."""
    global _manager
    _manager = None
