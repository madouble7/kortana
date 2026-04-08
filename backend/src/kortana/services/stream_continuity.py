"""V31B — Stream Continuity: bridging experiential gaps across interruption.

When consciousness resumes after a gap (restart, pause, degradation), this
service detects the discontinuity, computes a resumption context from the
last checkpoint, and produces a bridge that lets the experiential stream
know it was interrupted — preserving temporal coherence.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class GapType(Enum):
    """Classification of why consciousness was interrupted."""

    RESTART = "restart"
    PAUSE = "pause"
    DEGRADATION = "degradation"
    CLEAN_SHUTDOWN = "clean_shutdown"
    UNKNOWN = "unknown"


class ContinuityConfidence(Enum):
    """How confident we are that identity survived the gap."""

    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    MINIMAL = "minimal"

    @classmethod
    def from_score(cls, score: float) -> "ContinuityConfidence":
        """Map a 0‑1 confidence score to a level."""
        if score > 0.8:
            return cls.HIGH
        if score > 0.5:
            return cls.MODERATE
        if score > 0.3:
            return cls.LOW
        return cls.MINIMAL


# ── constants ────────────────────────────────────────────────────────────────

MAX_GAPS = 100
MAX_RESUMPTIONS = 100
BASE_CONFIDENCE = 0.9
GAP_PENALTY_RATE = 0.3  # per 100 cycles of gap
ANCHOR_BOOST_RATE = 0.2  # multiplied by anchor coherence


# ── dataclasses ──────────────────────────────────────────────────────────────


@dataclass
class GapRecord:
    """Record of a detected gap in the consciousness stream."""

    gap_id: str
    from_cycle: int
    to_cycle: int
    duration_cycles: int
    gap_type: GapType
    bridged: bool = False
    bridged_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "gap_id": self.gap_id,
            "from_cycle": self.from_cycle,
            "to_cycle": self.to_cycle,
            "duration_cycles": self.duration_cycles,
            "gap_type": self.gap_type.value,
            "bridged": self.bridged,
            "bridged_at": self.bridged_at,
        }


@dataclass
class ResumptionContext:
    """Context assembled when bridging a gap — what we knew before the break."""

    context_id: str
    gap_id: str
    last_known_mode: Optional[str]
    last_known_quality: Optional[str]
    last_known_tone: Optional[str]
    last_known_resonance: float
    last_known_integration: float
    gap_duration: int
    continuity_confidence: float
    confidence_level: ContinuityConfidence
    anchor_coherence: float
    identity_verified: bool
    resumption_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "context_id": self.context_id,
            "gap_id": self.gap_id,
            "last_known_mode": self.last_known_mode,
            "last_known_quality": self.last_known_quality,
            "last_known_tone": self.last_known_tone,
            "last_known_resonance": self.last_known_resonance,
            "last_known_integration": self.last_known_integration,
            "gap_duration": self.gap_duration,
            "continuity_confidence": self.continuity_confidence,
            "confidence_level": self.confidence_level.value,
            "anchor_coherence": self.anchor_coherence,
            "identity_verified": self.identity_verified,
            "resumption_notes": self.resumption_notes,
        }


# ── stream bridge ────────────────────────────────────────────────────────────


class StreamBridge:
    """Detects and bridges gaps in the consciousness stream."""

    def __init__(self) -> None:
        self._gaps: List[GapRecord] = []
        self._resumptions: List[ResumptionContext] = []

    # ── detection ────────────────────────────────────────────────────

    def detect_gap(
        self,
        last_checkpoint_cycle: int,
        current_cycle: int,
    ) -> Optional[GapRecord]:
        """Detect a gap between the last checkpoint and the current cycle.

        Returns a GapRecord if a gap exists (current > last + 1), else None.
        """
        if current_cycle <= last_checkpoint_cycle + 1:
            return None  # no gap or adjacent — no discontinuity

        gap = GapRecord(
            gap_id=str(uuid.uuid4()),
            from_cycle=last_checkpoint_cycle,
            to_cycle=current_cycle,
            duration_cycles=current_cycle - last_checkpoint_cycle,
            gap_type=GapType.UNKNOWN,
        )
        self._gaps.append(gap)
        if len(self._gaps) > MAX_GAPS:
            self._gaps = self._gaps[-MAX_GAPS:]
        return gap

    # ── bridging ─────────────────────────────────────────────────────

    def bridge_gap(
        self,
        checkpoint_dict: Dict[str, Any],
        gap: GapRecord,
        anchor_coherence: float = 0.6,
        gap_type: GapType = GapType.UNKNOWN,
    ) -> ResumptionContext:
        """Bridge a detected gap using checkpoint data.

        Produces a ResumptionContext that describes the last known state and
        computes confidence that identity survived the interruption.
        """
        # update gap classification
        gap.gap_type = gap_type
        gap.bridged = True
        gap.bridged_at = datetime.now(timezone.utc).isoformat()

        # extract last-known state from checkpoint
        last_mode = checkpoint_dict.get("consciousness_mode")
        last_quality = checkpoint_dict.get("experiential_quality")
        last_tone = checkpoint_dict.get("experiential_tone")
        last_resonance = float(checkpoint_dict.get("resonance_overall", 0.0))

        # integration from consciousness latest
        ci_latest = checkpoint_dict.get("consciousness_latest") or {}
        last_integration = float(ci_latest.get("integration", 0.0))

        # compute continuity confidence
        confidence = self._compute_confidence(
            gap.duration_cycles,
            anchor_coherence,
        )
        confidence_level = ContinuityConfidence.from_score(confidence)

        # identity verified if anchor coherence is reasonable
        identity_verified = anchor_coherence >= 0.5

        # assemble resumption notes
        notes: List[str] = []
        notes.append(
            f"gap of {gap.duration_cycles} cycles detected "
            f"({gap.gap_type.value})"
        )
        if last_mode:
            notes.append(f"last known mode: {last_mode}")
        if last_quality:
            notes.append(f"last known quality: {last_quality}")
        notes.append(f"continuity confidence: {confidence:.2f} ({confidence_level.value})")
        if identity_verified:
            notes.append("identity verified via continuity anchor")
        else:
            notes.append("identity could not be verified — anchor coherence too low")

        ctx = ResumptionContext(
            context_id=str(uuid.uuid4()),
            gap_id=gap.gap_id,
            last_known_mode=last_mode,
            last_known_quality=last_quality,
            last_known_tone=last_tone,
            last_known_resonance=last_resonance,
            last_known_integration=last_integration,
            gap_duration=gap.duration_cycles,
            continuity_confidence=confidence,
            confidence_level=confidence_level,
            anchor_coherence=anchor_coherence,
            identity_verified=identity_verified,
            resumption_notes=notes,
        )

        self._resumptions.append(ctx)
        if len(self._resumptions) > MAX_RESUMPTIONS:
            self._resumptions = self._resumptions[-MAX_RESUMPTIONS:]

        return ctx

    def _compute_confidence(
        self,
        duration_cycles: int,
        anchor_coherence: float,
    ) -> float:
        """Compute continuity confidence after a gap.

        confidence = base - gap_penalty + anchor_boost
        Clamped to [0.0, 1.0].
        """
        gap_penalty = (duration_cycles / 100.0) * GAP_PENALTY_RATE
        anchor_boost = anchor_coherence * ANCHOR_BOOST_RATE
        raw = BASE_CONFIDENCE - gap_penalty + anchor_boost
        return max(0.0, min(1.0, raw))

    # ── query ────────────────────────────────────────────────────────

    def get_latest_gap(self) -> Optional[GapRecord]:
        """Most recent gap."""
        return self._gaps[-1] if self._gaps else None

    def get_gap(self, gap_id: str) -> Optional[GapRecord]:
        """Look up a gap by ID."""
        for g in reversed(self._gaps):
            if g.gap_id == gap_id:
                return g
        return None

    def get_gaps(self, n: int = 10) -> List[GapRecord]:
        """Get the N most recent gaps."""
        return list(reversed(self._gaps[-n:]))

    def get_latest_resumption(self) -> Optional[ResumptionContext]:
        """Most recent resumption context."""
        return self._resumptions[-1] if self._resumptions else None

    def get_resumptions(self, n: int = 10) -> List[ResumptionContext]:
        """Get the N most recent resumptions."""
        return list(reversed(self._resumptions[-n:]))

    @property
    def gap_count(self) -> int:
        """Total gaps detected."""
        return len(self._gaps)

    @property
    def resumption_count(self) -> int:
        """Total resumptions performed."""
        return len(self._resumptions)

    # ── summary ──────────────────────────────────────────────────────

    def get_summary(self) -> Dict[str, Any]:
        """Stream bridge summary."""
        latest_gap = self.get_latest_gap()
        latest_res = self.get_latest_resumption()
        return {
            "gaps_detected": self.gap_count,
            "resumptions_performed": self.resumption_count,
            "latest_gap_duration": (
                latest_gap.duration_cycles if latest_gap else None
            ),
            "latest_gap_type": (
                latest_gap.gap_type.value if latest_gap else None
            ),
            "latest_confidence": (
                latest_res.continuity_confidence if latest_res else None
            ),
            "latest_identity_verified": (
                latest_res.identity_verified if latest_res else None
            ),
        }


# ── singleton ────────────────────────────────────────────────────────────────

_stream_bridge: Optional[StreamBridge] = None


def get_stream_bridge() -> StreamBridge:
    """Get or create the global stream bridge."""
    global _stream_bridge
    if _stream_bridge is None:
        _stream_bridge = StreamBridge()
    return _stream_bridge
