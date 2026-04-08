"""V28C — pursuit engine service.

drives multi-cycle goal pursuit. once a desire crystallizes into a goal,
the pursuit engine tracks whether the system is actually making progress
toward it, detects stalls, and can escalate or redirect effort.

consumes: GoalCrystallizer (accepted blueprints), goal_manager (goal status)
produces: PursuitReport (progress tracking across cycles)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class PursuitState(Enum):
    """lifecycle of a goal pursuit."""
    INITIATED = "initiated"      # pursuit just started
    ADVANCING = "advancing"      # making progress
    STALLED = "stalled"          # no progress for several cycles
    ACCELERATING = "accelerating"  # progress increasing
    ACHIEVED = "achieved"        # goal was completed
    ABANDONED = "abandoned"      # pursuit was dropped


@dataclass
class PursuitCheckpoint:
    """a single progress observation for a pursuit."""
    cycle_number: int
    progress_delta: float        # change in progress since last checkpoint
    cumulative_progress: float   # total progress so far (0.0 to 1.0)
    notes: str = ""
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle_number": self.cycle_number,
            "progress_delta": round(self.progress_delta, 3),
            "cumulative_progress": round(self.cumulative_progress, 3),
            "notes": self.notes,
            "recorded_at": self.recorded_at.isoformat(),
        }


@dataclass
class Pursuit:
    """tracks the multi-cycle pursuit of a goal.

    a pursuit connects a crystallized desire to an active goal
    and monitors whether the system is actually making progress.
    """
    pursuit_id: str
    goal_id: str
    source_desire_id: str
    source_blueprint_id: str
    state: PursuitState
    goal_title: str
    started_cycle: int
    current_progress: float            # 0.0 to 1.0
    checkpoints: list[PursuitCheckpoint] = field(default_factory=list)
    stall_count: int = 0               # consecutive cycles with no progress
    stall_threshold: int = 5           # cycles before declaring stalled
    escalated: bool = False
    redirected: bool = False
    redirect_reason: str = ""
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: datetime | None = None

    def add_checkpoint(
        self, cycle_number: int, progress: float, notes: str = ""
    ) -> PursuitCheckpoint:
        """record a progress observation."""
        delta = progress - self.current_progress
        self.current_progress = max(0.0, min(1.0, progress))

        checkpoint = PursuitCheckpoint(
            cycle_number=cycle_number,
            progress_delta=delta,
            cumulative_progress=self.current_progress,
            notes=notes,
        )
        self.checkpoints.append(checkpoint)

        # update state based on progress
        if delta <= 0:
            self.stall_count += 1
        else:
            self.stall_count = 0

        self._update_state()
        return checkpoint

    def _update_state(self) -> None:
        if self.state in (PursuitState.ACHIEVED, PursuitState.ABANDONED):
            return

        if self.current_progress >= 1.0:
            self.state = PursuitState.ACHIEVED
            self.resolved_at = datetime.now(timezone.utc)
        elif self.stall_count >= self.stall_threshold:
            self.state = PursuitState.STALLED
        elif len(self.checkpoints) >= 2:
            recent = self.checkpoints[-2:]
            if all(cp.progress_delta > 0 for cp in recent):
                if recent[-1].progress_delta > recent[-2].progress_delta:
                    self.state = PursuitState.ACCELERATING
                else:
                    self.state = PursuitState.ADVANCING
            else:
                self.state = PursuitState.ADVANCING
        else:
            self.state = PursuitState.INITIATED

    def abandon(self, reason: str = "") -> None:
        self.state = PursuitState.ABANDONED
        self.resolved_at = datetime.now(timezone.utc)
        self.redirect_reason = reason

    def escalate(self) -> None:
        self.escalated = True

    def redirect(self, reason: str) -> None:
        self.redirected = True
        self.redirect_reason = reason

    @property
    def duration_cycles(self) -> int:
        if not self.checkpoints:
            return 0
        return self.checkpoints[-1].cycle_number - self.started_cycle

    @property
    def velocity(self) -> float:
        """progress per cycle."""
        if not self.checkpoints or self.duration_cycles == 0:
            return 0.0
        return self.current_progress / self.duration_cycles

    @property
    def is_active(self) -> bool:
        return self.state not in (PursuitState.ACHIEVED, PursuitState.ABANDONED)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pursuit_id": self.pursuit_id,
            "goal_id": self.goal_id,
            "source_desire_id": self.source_desire_id,
            "source_blueprint_id": self.source_blueprint_id,
            "state": self.state.value,
            "goal_title": self.goal_title,
            "started_cycle": self.started_cycle,
            "current_progress": round(self.current_progress, 3),
            "stall_count": self.stall_count,
            "escalated": self.escalated,
            "redirected": self.redirected,
            "duration_cycles": self.duration_cycles,
            "velocity": round(self.velocity, 4),
            "checkpoint_count": len(self.checkpoints),
            "started_at": self.started_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class PursuitEngine:
    """drives multi-cycle goal pursuit.

    creates pursuit objects when blueprints are accepted,
    tracks progress each cycle, detects stalls, and manages
    pursuit lifecycle.
    """

    STALL_THRESHOLD = 5                # cycles without progress → stalled
    AUTO_ABANDON_THRESHOLD = 15        # cycles stalled → auto-abandon

    def __init__(self) -> None:
        self._pursuits: dict[str, Pursuit] = {}
        self._goal_to_pursuit: dict[str, str] = {}  # goal_id → pursuit_id
        self._cycle_count: int = 0

    def begin_pursuit(
        self,
        goal_id: str,
        goal_title: str,
        desire_id: str,
        blueprint_id: str,
        cycle_number: int,
    ) -> Pursuit:
        """start pursuing a crystallized goal."""
        # check for existing pursuit of same goal
        if goal_id in self._goal_to_pursuit:
            existing_id = self._goal_to_pursuit[goal_id]
            existing = self._pursuits.get(existing_id)
            if existing and existing.is_active:
                return existing

        pursuit = Pursuit(
            pursuit_id=str(uuid.uuid4()),
            goal_id=goal_id,
            source_desire_id=desire_id,
            source_blueprint_id=blueprint_id,
            state=PursuitState.INITIATED,
            goal_title=goal_title,
            started_cycle=cycle_number,
            current_progress=0.0,
            stall_threshold=self.STALL_THRESHOLD,
        )
        self._pursuits[pursuit.pursuit_id] = pursuit
        self._goal_to_pursuit[goal_id] = pursuit.pursuit_id
        return pursuit

    def update_progress(
        self,
        goal_id: str,
        progress: float,
        cycle_number: int,
        notes: str = "",
    ) -> PursuitCheckpoint | None:
        """report progress on a goal pursuit."""
        self._cycle_count = cycle_number
        pursuit_id = self._goal_to_pursuit.get(goal_id)
        if pursuit_id is None:
            return None

        pursuit = self._pursuits.get(pursuit_id)
        if pursuit is None or not pursuit.is_active:
            return None

        checkpoint = pursuit.add_checkpoint(cycle_number, progress, notes)

        # auto-escalate stalled pursuits
        if pursuit.state == PursuitState.STALLED and not pursuit.escalated:
            pursuit.escalate()

        # auto-abandon long-stalled pursuits
        if pursuit.stall_count >= self.AUTO_ABANDON_THRESHOLD:
            pursuit.abandon(
                f"auto-abandoned after {pursuit.stall_count} cycles without progress"
            )

        return checkpoint

    def complete_pursuit(self, goal_id: str) -> bool:
        """mark a pursuit as achieved."""
        pursuit_id = self._goal_to_pursuit.get(goal_id)
        if pursuit_id is None:
            return False
        pursuit = self._pursuits.get(pursuit_id)
        if pursuit is None:
            return False
        pursuit.current_progress = 1.0
        pursuit.state = PursuitState.ACHIEVED
        pursuit.resolved_at = datetime.now(timezone.utc)
        return True

    def abandon_pursuit(self, goal_id: str, reason: str = "") -> bool:
        """abandon a pursuit."""
        pursuit_id = self._goal_to_pursuit.get(goal_id)
        if pursuit_id is None:
            return False
        pursuit = self._pursuits.get(pursuit_id)
        if pursuit is None:
            return False
        pursuit.abandon(reason)
        return True

    def tick_cycle(self, cycle_number: int) -> list[Pursuit]:
        """advance all active pursuits by one cycle.

        returns list of pursuits that changed state this cycle.
        """
        self._cycle_count = cycle_number
        changed: list[Pursuit] = []

        for pursuit in self._pursuits.values():
            if not pursuit.is_active:
                continue

            old_state = pursuit.state

            # if no checkpoint was added this cycle, count as zero progress
            if not pursuit.checkpoints or pursuit.checkpoints[-1].cycle_number < cycle_number:
                pursuit.stall_count += 1
                pursuit._update_state()

            if pursuit.state != old_state:
                changed.append(pursuit)

            # auto-abandon
            if pursuit.stall_count >= self.AUTO_ABANDON_THRESHOLD:
                pursuit.abandon(
                    f"auto-abandoned after {pursuit.stall_count} cycles without progress"
                )
                if pursuit not in changed:
                    changed.append(pursuit)

        return changed

    # ── retrieval ────────────────────────────────────────────────────────────

    def get_pursuit(self, pursuit_id: str) -> Pursuit | None:
        return self._pursuits.get(pursuit_id)

    def get_by_goal(self, goal_id: str) -> Pursuit | None:
        pursuit_id = self._goal_to_pursuit.get(goal_id)
        if pursuit_id is None:
            return None
        return self._pursuits.get(pursuit_id)

    def get_active(self) -> list[Pursuit]:
        return [p for p in self._pursuits.values() if p.is_active]

    def get_stalled(self) -> list[Pursuit]:
        return [p for p in self._pursuits.values() if p.state == PursuitState.STALLED]

    def get_achieved(self) -> list[Pursuit]:
        return [p for p in self._pursuits.values() if p.state == PursuitState.ACHIEVED]

    def get_abandoned(self) -> list[Pursuit]:
        return [p for p in self._pursuits.values() if p.state == PursuitState.ABANDONED]

    def get_by_state(self, state: PursuitState) -> list[Pursuit]:
        return [p for p in self._pursuits.values() if p.state == state]

    def get_recent(self, n: int = 10) -> list[Pursuit]:
        return sorted(
            self._pursuits.values(),
            key=lambda p: p.started_at,
            reverse=True,
        )[:n]

    # ── properties ───────────────────────────────────────────────────────────

    @property
    def pursuit_count(self) -> int:
        return len(self._pursuits)

    @property
    def active_count(self) -> int:
        return len(self.get_active())

    @property
    def stalled_count(self) -> int:
        return len(self.get_stalled())

    @property
    def achieved_count(self) -> int:
        return len(self.get_achieved())

    @property
    def abandoned_count(self) -> int:
        return len(self.get_abandoned())

    @property
    def completion_rate(self) -> float:
        finished = self.achieved_count + self.abandoned_count
        if finished == 0:
            return 0.0
        return self.achieved_count / finished

    @property
    def average_velocity(self) -> float:
        active = self.get_active()
        if not active:
            return 0.0
        return sum(p.velocity for p in active) / len(active)

    def get_summary(self) -> dict[str, Any]:
        return {
            "pursuit_count": self.pursuit_count,
            "active_count": self.active_count,
            "stalled_count": self.stalled_count,
            "achieved_count": self.achieved_count,
            "abandoned_count": self.abandoned_count,
            "completion_rate": round(self.completion_rate, 3),
            "average_velocity": round(self.average_velocity, 4),
        }


_instance: PursuitEngine | None = None


def get_pursuit_engine() -> PursuitEngine:
    global _instance
    if _instance is None:
        _instance = PursuitEngine()
    return _instance
