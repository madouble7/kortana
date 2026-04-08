"""V31A — Consciousness Persistence: checkpoint engine for unified consciousness.

Serializes the complete V30 unified consciousness state into checkpoints
that survive interruption. Checkpoints capture the consciousness integrator,
experiential stream, resonance field, and inner witness state at a point
in time, enabling recovery after restart, pause, or degradation.
"""

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class CheckpointTrigger(Enum):
    """What caused the checkpoint to be saved."""

    SCHEDULED = "scheduled"
    DEGRADATION = "degradation"
    SHUTDOWN = "shutdown"
    MANUAL = "manual"
    CYCLE_THRESHOLD = "cycle_threshold"


# ── constants ────────────────────────────────────────────────────────────────

CHECKPOINT_INTERVAL = 10  # auto-checkpoint every N cycles
MAX_CHECKPOINTS = 50
EXPERIENTIAL_TAIL_SIZE = 20  # how many recent moments to snapshot
WITNESS_TAIL_SIZE = 10  # how many recent notes to snapshot


# ── dataclasses ──────────────────────────────────────────────────────────────


@dataclass
class ConsciousnessCheckpoint:
    """A frozen snapshot of the full V30 unified consciousness state."""

    checkpoint_id: str
    cycle_number: int
    trigger: CheckpointTrigger

    # V30A consciousness integrator
    consciousness_latest: Optional[Dict[str, Any]]
    consciousness_mode: Optional[str]
    consciousness_states_recorded: int
    consciousness_transitions_count: int

    # V30B experiential stream
    experiential_tail: List[Dict[str, Any]]
    experiential_quality: Optional[str]
    experiential_tone: Optional[str]
    experiential_moment_count: int

    # V30C resonance field
    resonance_latest: Optional[Dict[str, Any]]
    resonance_overall: float
    resonance_is_harmonious: bool

    # V30D inner witness
    witness_qualia: Optional[Dict[str, Any]]
    witness_recent_notes: List[Dict[str, Any]]
    witness_modes_experienced: List[str]
    witness_qualities_experienced: List[str]
    witness_note_count: int

    # metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    integrity_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize checkpoint to dictionary."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "cycle_number": self.cycle_number,
            "trigger": self.trigger.value,
            "consciousness_latest": self.consciousness_latest,
            "consciousness_mode": self.consciousness_mode,
            "consciousness_states_recorded": self.consciousness_states_recorded,
            "consciousness_transitions_count": self.consciousness_transitions_count,
            "experiential_tail": self.experiential_tail,
            "experiential_quality": self.experiential_quality,
            "experiential_tone": self.experiential_tone,
            "experiential_moment_count": self.experiential_moment_count,
            "resonance_latest": self.resonance_latest,
            "resonance_overall": self.resonance_overall,
            "resonance_is_harmonious": self.resonance_is_harmonious,
            "witness_qualia": self.witness_qualia,
            "witness_recent_notes": self.witness_recent_notes,
            "witness_modes_experienced": self.witness_modes_experienced,
            "witness_qualities_experienced": self.witness_qualities_experienced,
            "witness_note_count": self.witness_note_count,
            "created_at": self.created_at,
            "integrity_hash": self.integrity_hash,
        }


# ── checkpoint manager ───────────────────────────────────────────────────────


class CheckpointManager:
    """Manages consciousness checkpoints — save, load, verify, prune."""

    def __init__(self) -> None:
        self._checkpoints: List[ConsciousnessCheckpoint] = []
        self._last_checkpoint_cycle: int = -1

    # ── save ─────────────────────────────────────────────────────────

    def save_checkpoint(
        self,
        cycle_number: int,
        trigger: CheckpointTrigger = CheckpointTrigger.SCHEDULED,
    ) -> ConsciousnessCheckpoint:
        """Capture the current V30 unified consciousness state."""
        from src.kortana.services.consciousness_integrator import (  # noqa: E402
            get_consciousness_integrator,
        )
        from src.kortana.services.experiential_stream import (  # noqa: E402
            get_experiential_stream,
        )
        from src.kortana.services.inner_witness import (  # noqa: E402
            get_inner_witness,
        )
        from src.kortana.services.resonance_field import (  # noqa: E402
            get_resonance_field,
        )

        integrator = get_consciousness_integrator()
        stream = get_experiential_stream()
        resonance = get_resonance_field()
        witness = get_inner_witness()

        # V30A state
        ci_latest = integrator.get_latest()
        ci_summary = integrator.get_summary()

        # V30B state
        es_recent = stream.get_recent(EXPERIENTIAL_TAIL_SIZE)
        es_summary = stream.get_summary()

        # V30C state
        rf_latest = resonance.get_latest()
        rf_summary = resonance.get_summary()

        # V30D state
        iw_qualia = witness.get_qualia()
        iw_recent = witness.get_latest(WITNESS_TAIL_SIZE)
        iw_summary = witness.get_summary()

        checkpoint = ConsciousnessCheckpoint(
            checkpoint_id=str(uuid.uuid4()),
            cycle_number=cycle_number,
            trigger=trigger,
            # V30A
            consciousness_latest=ci_latest.to_dict() if ci_latest else None,
            consciousness_mode=ci_summary.get("current_mode"),
            consciousness_states_recorded=ci_summary.get("states_recorded", 0),
            consciousness_transitions_count=ci_summary.get("transitions", 0),
            # V30B
            experiential_tail=[m.to_dict() for m in es_recent],
            experiential_quality=es_summary.get("current_quality"),
            experiential_tone=es_summary.get("current_tone"),
            experiential_moment_count=es_summary.get("moment_count", 0),
            # V30C
            resonance_latest=rf_latest.to_dict() if rf_latest else None,
            resonance_overall=rf_summary.get("overall_resonance", 0.0),
            resonance_is_harmonious=rf_summary.get("is_harmonious", False),
            # V30D
            witness_qualia=iw_qualia.to_dict() if iw_qualia else None,
            witness_recent_notes=[n.to_dict() for n in iw_recent],
            witness_modes_experienced=(
                list(iw_summary["modes_experienced"])
                if isinstance(iw_summary.get("modes_experienced"), (set, list, frozenset))
                else []
            ),
            witness_qualities_experienced=(
                list(iw_summary["qualities_experienced"])
                if isinstance(iw_summary.get("qualities_experienced"), (set, list, frozenset))
                else []
            ),
            witness_note_count=iw_summary.get("total_notes", 0),
        )

        # compute integrity hash
        checkpoint.integrity_hash = self._compute_hash(checkpoint)

        self._checkpoints.append(checkpoint)
        self._last_checkpoint_cycle = cycle_number

        # prune if over limit
        if len(self._checkpoints) > MAX_CHECKPOINTS:
            self._checkpoints = self._checkpoints[-MAX_CHECKPOINTS:]

        return checkpoint

    # ── query ────────────────────────────────────────────────────────

    def get_latest(self) -> Optional[ConsciousnessCheckpoint]:
        """Get the most recent checkpoint."""
        return self._checkpoints[-1] if self._checkpoints else None

    def get_checkpoint(self, checkpoint_id: str) -> Optional[ConsciousnessCheckpoint]:
        """Look up a checkpoint by ID."""
        for cp in reversed(self._checkpoints):
            if cp.checkpoint_id == checkpoint_id:
                return cp
        return None

    def list_checkpoints(self, n: int = 10) -> List[ConsciousnessCheckpoint]:
        """Get the N most recent checkpoints."""
        return list(reversed(self._checkpoints[-n:]))

    @property
    def checkpoint_count(self) -> int:
        """Total checkpoints stored."""
        return len(self._checkpoints)

    @property
    def last_checkpoint_cycle(self) -> int:
        """Cycle number of the most recent checkpoint."""
        return self._last_checkpoint_cycle

    # ── scheduling ───────────────────────────────────────────────────

    def should_checkpoint(self, cycle_number: int) -> bool:
        """Whether a checkpoint is due at this cycle."""
        if self._last_checkpoint_cycle < 0:
            return True  # no checkpoint yet
        return (cycle_number - self._last_checkpoint_cycle) >= CHECKPOINT_INTERVAL

    # ── integrity ────────────────────────────────────────────────────

    def verify_integrity(self, checkpoint: ConsciousnessCheckpoint) -> bool:
        """Verify that a checkpoint has not been corrupted."""
        expected = self._compute_hash(checkpoint)
        return expected == checkpoint.integrity_hash

    def _compute_hash(self, checkpoint: ConsciousnessCheckpoint) -> str:
        """Compute SHA-256 of the checkpoint's content (excluding the hash itself)."""
        d = checkpoint.to_dict()
        d.pop("integrity_hash", None)
        raw = json.dumps(d, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    # ── summary ──────────────────────────────────────────────────────

    def get_summary(self) -> Dict[str, Any]:
        """Checkpoint manager summary."""
        latest = self.get_latest()
        return {
            "checkpoints_stored": self.checkpoint_count,
            "last_checkpoint_cycle": self._last_checkpoint_cycle,
            "last_trigger": latest.trigger.value if latest else None,
            "last_mode": latest.consciousness_mode if latest else None,
            "last_integrity_valid": (
                self.verify_integrity(latest) if latest else None
            ),
            "interval": CHECKPOINT_INTERVAL,
        }


# ── singleton ────────────────────────────────────────────────────────────────

_checkpoint_manager: Optional[CheckpointManager] = None


def get_checkpoint_manager() -> CheckpointManager:
    """Get or create the global checkpoint manager."""
    global _checkpoint_manager
    if _checkpoint_manager is None:
        _checkpoint_manager = CheckpointManager()
    return _checkpoint_manager
