"""V28B — goal crystallizer service.

converts mature desires into concrete goals. the bridge between
wanting (desire) and planning (goal). a desire becomes a goal when
it has persisted long enough, grown strong enough, and can be
translated into something actionable.

consumes: DesireFormation (mature desires)
produces: GoalBlueprint (specs for goal_manager to create)
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class CrystallizationOutcome(Enum):
    """result of attempting to crystallize a desire."""
    CRYSTALLIZED = "crystallized"
    TOO_WEAK = "too_weak"
    ALREADY_CRYSTALLIZED = "already_crystallized"
    NO_ACTIONABLE_FORM = "no_actionable_form"
    DUPLICATE_GOAL = "duplicate_goal"


@dataclass
class GoalBlueprint:
    """a specification for a goal to be created.

    not a goal itself — a blueprint that goal_manager can use
    to create a proper Goal with correct tier and priority.
    """
    blueprint_id: str
    source_desire_id: str
    source_desire_description: str
    title: str
    tier: str                          # STRATEGIC / TACTICAL / IMMEDIATE
    suggested_priority: float          # 0.0 to 1.0
    rationale: str
    success_criteria: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    accepted: bool = False             # was it accepted by goal_manager?
    accepted_goal_id: str | None = None
    blueprint_hash: str = ""

    def __post_init__(self) -> None:
        if not self.blueprint_hash:
            key = f"{self.source_desire_id}:{self.title}"
            self.blueprint_hash = hashlib.sha256(key.encode()).hexdigest()[:16]

    def mark_accepted(self, goal_id: str) -> None:
        self.accepted = True
        self.accepted_goal_id = goal_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "blueprint_id": self.blueprint_id,
            "source_desire_id": self.source_desire_id,
            "source_desire_description": self.source_desire_description,
            "title": self.title,
            "tier": self.tier,
            "suggested_priority": round(self.suggested_priority, 3),
            "rationale": self.rationale,
            "success_criteria": self.success_criteria,
            "created_at": self.created_at.isoformat(),
            "accepted": self.accepted,
            "accepted_goal_id": self.accepted_goal_id,
            "blueprint_hash": self.blueprint_hash,
        }


# ── source → tier mapping ────────────────────────────────────────────────────

_SOURCE_TIER_MAP: dict[str, str] = {
    "health_deficit": "TACTICAL",
    "learning_stagnation": "STRATEGIC",
    "pattern_insight": "TACTICAL",
    "deferral_frustration": "IMMEDIATE",
    "capability_gap": "STRATEGIC",
    "autonomy_drive": "STRATEGIC",
}

# ── source → title template ──────────────────────────────────────────────────

_SOURCE_TITLE_MAP: dict[str, str] = {
    "health_deficit": "restore {dimension} health to optimal range",
    "learning_stagnation": "increase learning velocity and lesson extraction",
    "pattern_insight": "act on recognized patterns in {dimension}",
    "deferral_frustration": "resolve persistent deferrals in {dimension}",
    "capability_gap": "expand capability to reduce {dimension} failures",
    "autonomy_drive": "maximize autonomous operation capacity",
}


class GoalCrystallizer:
    """converts mature desires into goal blueprints.

    a desire crystallizes when:
    1. it has reached MATURE state (intensity ≥ 0.7, persistence ≥ 3)
    2. it hasn't already been crystallized
    3. no duplicate goal already exists for the same need
    """

    MATURITY_INTENSITY = 0.7
    MATURITY_PERSISTENCE = 3

    def __init__(self) -> None:
        self._blueprints: dict[str, GoalBlueprint] = {}
        self._desire_to_blueprint: dict[str, str] = {}  # desire_id → blueprint_id
        self._active_goal_titles: set[str] = set()       # prevent duplicates
        self._cycle_count: int = 0

    def crystallize(
        self,
        desires: list[dict[str, Any]],
        cycle_number: int,
    ) -> list[GoalBlueprint]:
        """attempt to crystallize a batch of desires into goal blueprints.

        takes desire dicts (from Desire.to_dict()) and returns new blueprints.
        """
        self._cycle_count = cycle_number
        new_blueprints: list[GoalBlueprint] = []

        for desire_dict in desires:
            outcome, blueprint = self._try_crystallize(desire_dict, cycle_number)
            if outcome == CrystallizationOutcome.CRYSTALLIZED and blueprint is not None:
                new_blueprints.append(blueprint)

        return new_blueprints

    def _try_crystallize(
        self,
        desire: dict[str, Any],
        cycle_number: int,
    ) -> tuple[CrystallizationOutcome, GoalBlueprint | None]:
        """attempt to crystallize a single desire."""
        desire_id = desire.get("desire_id", "")

        # already crystallized?
        if desire_id in self._desire_to_blueprint:
            return CrystallizationOutcome.ALREADY_CRYSTALLIZED, None

        # strong enough?
        intensity = desire.get("intensity", 0)
        persistence = desire.get("persistence", 0)
        if intensity < self.MATURITY_INTENSITY or persistence < self.MATURITY_PERSISTENCE:
            return CrystallizationOutcome.TOO_WEAK, None

        # build the goal title
        source = desire.get("source", "")
        dimension = desire.get("source_dimension", "system")
        title_template = _SOURCE_TITLE_MAP.get(source, "address {dimension} needs")
        title = title_template.format(dimension=dimension)

        # duplicate goal?
        if title in self._active_goal_titles:
            return CrystallizationOutcome.DUPLICATE_GOAL, None

        # crystallize
        tier = _SOURCE_TIER_MAP.get(source, "TACTICAL")
        priority = min(1.0, intensity * 0.8 + (persistence / 20.0))

        blueprint = GoalBlueprint(
            blueprint_id=str(uuid.uuid4()),
            source_desire_id=desire_id,
            source_desire_description=desire.get("description", ""),
            title=title,
            tier=tier,
            suggested_priority=priority,
            rationale=(
                f"desire '{desire.get('description', '')}' has persisted for "
                f"{persistence} cycles at intensity {intensity:.2f}"
            ),
            success_criteria=self._generate_success_criteria(source, dimension, desire),
        )

        self._blueprints[blueprint.blueprint_id] = blueprint
        self._desire_to_blueprint[desire_id] = blueprint.blueprint_id
        self._active_goal_titles.add(title)

        return CrystallizationOutcome.CRYSTALLIZED, blueprint

    def _generate_success_criteria(
        self, source: str, dimension: str, desire: dict[str, Any]
    ) -> str:
        """generate success criteria based on desire source."""
        criteria_map = {
            "health_deficit": f"{dimension} health score above 70",
            "learning_stagnation": "learning velocity above 1.0 for 3 consecutive cycles",
            "pattern_insight": f"all actionable {dimension} patterns addressed",
            "deferral_frustration": f"pending {dimension} deferrals reduced to zero",
            "capability_gap": f"{dimension} failure rate below 10%",
            "autonomy_drive": "autonomous operation rate above 90%",
        }
        return criteria_map.get(source, f"{dimension} needs resolved")

    def accept_blueprint(self, blueprint_id: str, goal_id: str) -> bool:
        """mark a blueprint as accepted — goal_manager created the goal."""
        bp = self._blueprints.get(blueprint_id)
        if bp is None:
            return False
        bp.mark_accepted(goal_id)
        return True

    def register_active_goal(self, title: str) -> None:
        """register an existing goal title to prevent duplicates."""
        self._active_goal_titles.add(title)

    def unregister_goal(self, title: str) -> None:
        """remove a goal title when it's completed or abandoned."""
        self._active_goal_titles.discard(title)

    # ── retrieval ────────────────────────────────────────────────────────────

    def get_blueprint(self, blueprint_id: str) -> GoalBlueprint | None:
        return self._blueprints.get(blueprint_id)

    def get_by_desire(self, desire_id: str) -> GoalBlueprint | None:
        bp_id = self._desire_to_blueprint.get(desire_id)
        if bp_id is None:
            return None
        return self._blueprints.get(bp_id)

    def get_accepted(self) -> list[GoalBlueprint]:
        return [bp for bp in self._blueprints.values() if bp.accepted]

    def get_pending(self) -> list[GoalBlueprint]:
        return [bp for bp in self._blueprints.values() if not bp.accepted]

    def get_recent(self, n: int = 10) -> list[GoalBlueprint]:
        return sorted(
            self._blueprints.values(),
            key=lambda bp: bp.created_at,
            reverse=True,
        )[:n]

    # ── properties ───────────────────────────────────────────────────────────

    @property
    def blueprint_count(self) -> int:
        return len(self._blueprints)

    @property
    def accepted_count(self) -> int:
        return len(self.get_accepted())

    @property
    def pending_count(self) -> int:
        return len(self.get_pending())

    @property
    def crystallization_rate(self) -> float:
        """ratio of accepted to total blueprints."""
        if not self._blueprints:
            return 0.0
        return self.accepted_count / len(self._blueprints)

    def get_summary(self) -> dict[str, Any]:
        return {
            "blueprint_count": self.blueprint_count,
            "accepted_count": self.accepted_count,
            "pending_count": self.pending_count,
            "crystallization_rate": round(self.crystallization_rate, 3),
            "active_goal_titles": len(self._active_goal_titles),
            "desire_to_blueprint_mappings": len(self._desire_to_blueprint),
        }


_instance: GoalCrystallizer | None = None


def get_goal_crystallizer() -> GoalCrystallizer:
    global _instance
    if _instance is None:
        _instance = GoalCrystallizer()
    return _instance
