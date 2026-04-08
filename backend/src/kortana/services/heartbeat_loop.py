"""V26A — heartbeat loop.

the core living pulse of kor'tana. each heartbeat cycles through four phases:
observe (gather state), decide (choose actions), act (execute), reflect (record
what happened and what was deferred). this is what makes her a living process
rather than a dormant server.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class HeartbeatState(str, Enum):
    """the overall state of the heartbeat."""

    ALIVE = "alive"
    DEGRADED = "degraded"
    DORMANT = "dormant"
    RECOVERING = "recovering"


class HeartbeatPhase(str, Enum):
    """phases within a single heartbeat cycle."""

    OBSERVE = "observe"
    DECIDE = "decide"
    ACT = "act"
    REFLECT = "reflect"


@dataclass
class Observation:
    """something noticed during the observe phase."""

    source: str
    description: str
    severity: str = "info"  # info, warning, critical
    data: dict[str, Any] = field(default_factory=dict)
    observed_at: str = ""

    def __post_init__(self) -> None:
        if not self.observed_at:
            self.observed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "description": self.description,
            "severity": self.severity,
            "data": self.data,
            "observed_at": self.observed_at,
        }


@dataclass
class Decision:
    """a decision made during the decide phase."""

    action_type: str
    rationale: str
    priority: int = 0  # higher = more urgent
    deferred: bool = False
    defer_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "action_type": self.action_type,
            "rationale": self.rationale,
            "priority": self.priority,
            "deferred": self.deferred,
        }
        if self.deferred:
            d["defer_reason"] = self.defer_reason
        return d


@dataclass
class Heartbeat:
    """a single heartbeat — one complete cycle of observe/decide/act/reflect."""

    beat_id: str = ""
    cycle_number: int = 0
    state: HeartbeatState = HeartbeatState.ALIVE
    phase: HeartbeatPhase = HeartbeatPhase.OBSERVE
    started_at: str = ""
    ended_at: str = ""
    duration_ms: float = 0.0
    observations: list[Observation] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    actions_taken: list[str] = field(default_factory=list)
    deferrals: list[str] = field(default_factory=list)
    reflections: list[str] = field(default_factory=list)
    beat_hash: str = ""

    def __post_init__(self) -> None:
        if not self.beat_id:
            self.beat_id = f"beat-{uuid.uuid4().hex[:12]}"
        if not self.started_at:
            self.started_at = datetime.now(timezone.utc).isoformat()
        if not self.beat_hash:
            raw = f"{self.beat_id}:{self.cycle_number}:{self.started_at}"
            self.beat_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "beat_id": self.beat_id,
            "cycle_number": self.cycle_number,
            "state": self.state.value,
            "phase": self.phase.value,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_ms": self.duration_ms,
            "observations": [o.to_dict() for o in self.observations],
            "decisions": [d.to_dict() for d in self.decisions],
            "actions_taken": self.actions_taken,
            "deferrals": self.deferrals,
            "reflections": self.reflections,
            "beat_hash": self.beat_hash,
        }


class HeartbeatLoop:
    """the living pulse of kor'tana.

    each beat cycles: observe → decide → act → reflect.
    the loop tracks state across beats so each cycle inherits context from the last.
    """

    def __init__(self) -> None:
        self._beats: list[Heartbeat] = []
        self._cycle_counter: int = 0
        self._state: HeartbeatState = HeartbeatState.DORMANT
        self._started_at: str = datetime.now(timezone.utc).isoformat()

    # ── lifecycle ────────────────────────────────────────────────────────

    def begin_beat(self) -> Heartbeat:
        """start a new heartbeat cycle."""
        self._cycle_counter += 1
        if self._state == HeartbeatState.DORMANT:
            self._state = HeartbeatState.ALIVE
        beat = Heartbeat(
            cycle_number=self._cycle_counter,
            state=self._state,
            phase=HeartbeatPhase.OBSERVE,
        )
        self._beats.append(beat)
        return beat

    def complete_beat(self, beat_id: str) -> bool:
        """finalize a heartbeat after all phases complete."""
        beat = self.get_beat(beat_id)
        if beat is None:
            return False
        beat.phase = HeartbeatPhase.REFLECT
        beat.ended_at = datetime.now(timezone.utc).isoformat()
        # calculate duration
        start = datetime.fromisoformat(beat.started_at)
        end = datetime.fromisoformat(beat.ended_at)
        beat.duration_ms = (end - start).total_seconds() * 1000
        return True

    # ── phase methods ────────────────────────────────────────────────────

    def add_observation(self, beat_id: str, source: str, description: str,
                        severity: str = "info",
                        data: dict[str, Any] | None = None) -> Observation | None:
        """record an observation during the observe phase."""
        beat = self.get_beat(beat_id)
        if beat is None:
            return None
        obs = Observation(source=source, description=description,
                          severity=severity, data=data or {})
        beat.observations.append(obs)
        beat.phase = HeartbeatPhase.OBSERVE
        return obs

    def add_decision(self, beat_id: str, action_type: str, rationale: str,
                     priority: int = 0) -> Decision | None:
        """record a decision during the decide phase."""
        beat = self.get_beat(beat_id)
        if beat is None:
            return None
        dec = Decision(action_type=action_type, rationale=rationale,
                       priority=priority)
        beat.decisions.append(dec)
        beat.phase = HeartbeatPhase.DECIDE
        return dec

    def add_deferral(self, beat_id: str, action_type: str, reason: str) -> Decision | None:
        """record a deferred decision — something we chose NOT to do this cycle."""
        beat = self.get_beat(beat_id)
        if beat is None:
            return None
        dec = Decision(action_type=action_type, rationale=reason,
                       deferred=True, defer_reason=reason)
        beat.decisions.append(dec)
        beat.deferrals.append(f"{action_type}: {reason}")
        return dec

    def record_action(self, beat_id: str, action: str) -> bool:
        """record an action taken during the act phase."""
        beat = self.get_beat(beat_id)
        if beat is None:
            return False
        beat.actions_taken.append(action)
        beat.phase = HeartbeatPhase.ACT
        return True

    def add_reflection(self, beat_id: str, reflection: str) -> bool:
        """record a reflection during the reflect phase."""
        beat = self.get_beat(beat_id)
        if beat is None:
            return False
        beat.reflections.append(reflection)
        beat.phase = HeartbeatPhase.REFLECT
        return True

    # ── state management ─────────────────────────────────────────────────

    def set_state(self, state: HeartbeatState) -> HeartbeatState:
        """update the heartbeat state."""
        previous = self._state
        self._state = state
        return previous

    @property
    def current_state(self) -> HeartbeatState:
        """current heartbeat state."""
        return self._state

    @property
    def is_alive(self) -> bool:
        """true if heartbeat is in an active state."""
        return self._state in (HeartbeatState.ALIVE, HeartbeatState.RECOVERING)

    # ── queries ──────────────────────────────────────────────────────────

    def get_beat(self, beat_id: str) -> Heartbeat | None:
        """retrieve a specific heartbeat by id."""
        for b in self._beats:
            if b.beat_id == beat_id:
                return b
        return None

    def get_recent(self, n: int = 10) -> list[Heartbeat]:
        """get the most recent n heartbeats."""
        return list(reversed(self._beats[-n:]))

    @property
    def last_beat(self) -> Heartbeat | None:
        """the most recent heartbeat."""
        return self._beats[-1] if self._beats else None

    @property
    def beat_count(self) -> int:
        return len(self._beats)

    @property
    def cycle_number(self) -> int:
        return self._cycle_counter

    @property
    def uptime_beats(self) -> int:
        """number of beats where state was ALIVE."""
        return sum(1 for b in self._beats if b.state == HeartbeatState.ALIVE)

    @property
    def total_observations(self) -> int:
        return sum(len(b.observations) for b in self._beats)

    @property
    def total_deferrals(self) -> int:
        return sum(len(b.deferrals) for b in self._beats)

    def get_summary(self) -> dict[str, Any]:
        """summary of the heartbeat loop."""
        last = self.last_beat
        avg_duration = 0.0
        completed = [b for b in self._beats if b.ended_at]
        if completed:
            avg_duration = sum(b.duration_ms for b in completed) / len(completed)
        return {
            "state": self._state.value,
            "beat_count": self.beat_count,
            "cycle_number": self._cycle_counter,
            "uptime_beats": self.uptime_beats,
            "total_observations": self.total_observations,
            "total_deferrals": self.total_deferrals,
            "avg_duration_ms": round(avg_duration, 2),
            "last_beat_id": last.beat_id if last else None,
            "last_beat_at": last.started_at if last else None,
            "started_at": self._started_at,
        }


# ── module singleton ─────────────────────────────────────────────────────

_heartbeat_loop: HeartbeatLoop | None = None


def get_heartbeat_loop() -> HeartbeatLoop:
    """get the module-level heartbeat loop singleton."""
    global _heartbeat_loop
    if _heartbeat_loop is None:
        _heartbeat_loop = HeartbeatLoop()
    return _heartbeat_loop
