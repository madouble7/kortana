"""V26B — cycle memory.

each heartbeat cycle records what it observed, decided, acted on, and deferred.
critically, it also records the context it bequeaths to the next cycle, so the
next beat inherits understanding rather than starting from scratch.

this is the difference between a process that repeats and a process that continues.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class CycleContext:
    """the context inherited from the previous cycle or bequeathed to the next."""

    pending_deferrals: list[str] = field(default_factory=list)
    active_concerns: list[str] = field(default_factory=list)
    recent_patterns: list[str] = field(default_factory=list)
    priority_shift: str = ""
    health_state: str = "unknown"
    degradation_mode: str = "full_operation"
    notes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pending_deferrals": self.pending_deferrals,
            "active_concerns": self.active_concerns,
            "recent_patterns": self.recent_patterns,
            "priority_shift": self.priority_shift,
            "health_state": self.health_state,
            "degradation_mode": self.degradation_mode,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CycleContext:
        return cls(
            pending_deferrals=data.get("pending_deferrals", []),
            active_concerns=data.get("active_concerns", []),
            recent_patterns=data.get("recent_patterns", []),
            priority_shift=data.get("priority_shift", ""),
            health_state=data.get("health_state", "unknown"),
            degradation_mode=data.get("degradation_mode", "full_operation"),
            notes=data.get("notes", {}),
        )


@dataclass
class CycleRecord:
    """a complete record of one cycle — what happened and what carries forward."""

    cycle_id: str = ""
    cycle_number: int = 0
    started_at: str = ""
    ended_at: str = ""
    duration_ms: float = 0.0
    observations: list[str] = field(default_factory=list)
    decisions_made: list[str] = field(default_factory=list)
    actions_taken: list[str] = field(default_factory=list)
    deferrals: list[str] = field(default_factory=list)
    reflections: list[str] = field(default_factory=list)
    context_inherited: CycleContext = field(default_factory=CycleContext)
    context_bequeathed: CycleContext = field(default_factory=CycleContext)
    finalized: bool = False
    cycle_hash: str = ""

    def __post_init__(self) -> None:
        if not self.cycle_id:
            self.cycle_id = f"cycle-{uuid.uuid4().hex[:12]}"
        if not self.started_at:
            self.started_at = datetime.now(timezone.utc).isoformat()
        if not self.cycle_hash:
            raw = f"{self.cycle_id}:{self.cycle_number}:{self.started_at}"
            self.cycle_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "cycle_number": self.cycle_number,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_ms": self.duration_ms,
            "observations": self.observations,
            "decisions_made": self.decisions_made,
            "actions_taken": self.actions_taken,
            "deferrals": self.deferrals,
            "reflections": self.reflections,
            "context_inherited": self.context_inherited.to_dict(),
            "context_bequeathed": self.context_bequeathed.to_dict(),
            "finalized": self.finalized,
            "cycle_hash": self.cycle_hash,
        }


class CycleMemory:
    """persistent memory across heartbeat cycles.

    each cycle inherits context from the previous one and bequeaths context
    to the next. this creates continuity — the system does not start fresh
    each beat but carries forward what it has learned, deferred, and observed.
    """

    def __init__(self) -> None:
        self._cycles: list[CycleRecord] = []
        self._cycle_counter: int = 0

    # ── lifecycle ────────────────────────────────────────────────────────

    def begin_cycle(self) -> CycleRecord:
        """start a new cycle, inheriting context from the previous one."""
        self._cycle_counter += 1
        inherited = CycleContext()

        # inherit from previous cycle
        if self._cycles:
            prev = self._cycles[-1]
            if prev.finalized:
                inherited = CycleContext(
                    pending_deferrals=list(prev.context_bequeathed.pending_deferrals),
                    active_concerns=list(prev.context_bequeathed.active_concerns),
                    recent_patterns=list(prev.context_bequeathed.recent_patterns),
                    priority_shift=prev.context_bequeathed.priority_shift,
                    health_state=prev.context_bequeathed.health_state,
                    degradation_mode=prev.context_bequeathed.degradation_mode,
                    notes=dict(prev.context_bequeathed.notes),
                )
            else:
                # previous cycle didn't finalize — carry forward its deferrals
                inherited = CycleContext(
                    pending_deferrals=list(prev.deferrals),
                    active_concerns=["previous cycle did not finalize"],
                    health_state="unknown",
                )

        record = CycleRecord(
            cycle_number=self._cycle_counter,
            context_inherited=inherited,
        )
        self._cycles.append(record)
        return record

    def end_cycle(self, cycle_id: str,
                  bequeathed: CycleContext | None = None) -> bool:
        """finalize a cycle and set the context to bequeath to the next."""
        rec = self.get_cycle(cycle_id)
        if rec is None or rec.finalized:
            return False

        rec.ended_at = datetime.now(timezone.utc).isoformat()
        start = datetime.fromisoformat(rec.started_at)
        end = datetime.fromisoformat(rec.ended_at)
        rec.duration_ms = (end - start).total_seconds() * 1000

        if bequeathed:
            rec.context_bequeathed = bequeathed
        else:
            # auto-bequeath: carry forward deferrals as pending
            rec.context_bequeathed = CycleContext(
                pending_deferrals=list(rec.deferrals),
                active_concerns=list(rec.context_inherited.active_concerns),
                recent_patterns=list(rec.context_inherited.recent_patterns),
                health_state=rec.context_inherited.health_state,
                degradation_mode=rec.context_inherited.degradation_mode,
            )

        rec.finalized = True
        return True

    # ── recording ────────────────────────────────────────────────────────

    def record_observation(self, cycle_id: str, observation: str) -> bool:
        """record an observation in the current cycle."""
        rec = self.get_cycle(cycle_id)
        if rec is None or rec.finalized:
            return False
        rec.observations.append(observation)
        return True

    def record_decision(self, cycle_id: str, decision: str) -> bool:
        """record a decision made in the current cycle."""
        rec = self.get_cycle(cycle_id)
        if rec is None or rec.finalized:
            return False
        rec.decisions_made.append(decision)
        return True

    def record_action(self, cycle_id: str, action: str) -> bool:
        """record an action taken in the current cycle."""
        rec = self.get_cycle(cycle_id)
        if rec is None or rec.finalized:
            return False
        rec.actions_taken.append(action)
        return True

    def record_deferral(self, cycle_id: str, deferral: str) -> bool:
        """record something deferred to a future cycle."""
        rec = self.get_cycle(cycle_id)
        if rec is None or rec.finalized:
            return False
        rec.deferrals.append(deferral)
        return True

    def record_reflection(self, cycle_id: str, reflection: str) -> bool:
        """record a reflection from the current cycle."""
        rec = self.get_cycle(cycle_id)
        if rec is None or rec.finalized:
            return False
        rec.reflections.append(reflection)
        return True

    # ── queries ──────────────────────────────────────────────────────────

    def get_cycle(self, cycle_id: str) -> CycleRecord | None:
        """retrieve a specific cycle by id."""
        for c in self._cycles:
            if c.cycle_id == cycle_id:
                return c
        return None

    def get_recent(self, n: int = 10) -> list[CycleRecord]:
        """get the most recent n cycles."""
        return list(reversed(self._cycles[-n:]))

    @property
    def last_cycle(self) -> CycleRecord | None:
        """the most recent cycle."""
        return self._cycles[-1] if self._cycles else None

    @property
    def cycle_count(self) -> int:
        return len(self._cycles)

    @property
    def total_observations(self) -> int:
        return sum(len(c.observations) for c in self._cycles)

    @property
    def total_decisions(self) -> int:
        return sum(len(c.decisions_made) for c in self._cycles)

    @property
    def total_deferrals(self) -> int:
        return sum(len(c.deferrals) for c in self._cycles)

    def get_inherited_context(self) -> CycleContext | None:
        """get the context that would be inherited by the next cycle."""
        if not self._cycles:
            return None
        last = self._cycles[-1]
        if last.finalized:
            return last.context_bequeathed
        return None

    def get_deferral_streak(self, deferral_pattern: str) -> int:
        """count consecutive cycles where a deferral pattern appeared."""
        streak = 0
        for c in reversed(self._cycles):
            if any(deferral_pattern.lower() in d.lower() for d in c.deferrals):
                streak += 1
            else:
                break
        return streak

    def get_summary(self) -> dict[str, Any]:
        """summary of cycle memory."""
        finalized = [c for c in self._cycles if c.finalized]
        avg_duration = 0.0
        if finalized:
            avg_duration = sum(c.duration_ms for c in finalized) / len(finalized)
        return {
            "cycle_count": self.cycle_count,
            "finalized_cycles": len(finalized),
            "total_observations": self.total_observations,
            "total_decisions": self.total_decisions,
            "total_deferrals": self.total_deferrals,
            "avg_duration_ms": round(avg_duration, 2),
            "last_cycle_id": self._cycles[-1].cycle_id if self._cycles else None,
            "last_cycle_number": self._cycle_counter,
        }


# ── module singleton ─────────────────────────────────────────────────────

_cycle_memory: CycleMemory | None = None


def get_cycle_memory() -> CycleMemory:
    """get the module-level cycle memory singleton."""
    global _cycle_memory
    if _cycle_memory is None:
        _cycle_memory = CycleMemory()
    return _cycle_memory
