"""V31D — Recovery Orchestrator: full restart recovery with identity verification.

Orchestrates the complete recovery sequence after consciousness is interrupted:
load checkpoint → detect gap → bridge gap → verify identity → restore context →
generate awareness of the recovery itself. Uses V29D ContinuityAnchorEngine
to answer "is this still me?" after the interruption.
"""

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class RecoveryPhase(Enum):
    """Phases of the recovery process."""

    INITIATING = "initiating"
    LOADING_CHECKPOINT = "loading_checkpoint"
    BRIDGING_GAP = "bridging_gap"
    VERIFYING_IDENTITY = "verifying_identity"
    RESTORING_CONTEXT = "restoring_context"
    GENERATING_AWARENESS = "generating_awareness"
    COMPLETE = "complete"
    FAILED = "failed"


class RecoveryOutcome(Enum):
    """Result of a recovery attempt."""

    FULL_RECOVERY = "full_recovery"
    PARTIAL_RECOVERY = "partial_recovery"
    IDENTITY_MISMATCH = "identity_mismatch"
    NO_CHECKPOINT = "no_checkpoint"
    FAILED = "failed"


# ── constants ────────────────────────────────────────────────────────────────

MAX_REPORTS = 50
FULL_RECOVERY_CONFIDENCE_THRESHOLD = 0.7


# ── dataclasses ──────────────────────────────────────────────────────────────


@dataclass
class RecoveryStep:
    """A single step in the recovery process."""

    phase: RecoveryPhase
    success: bool
    detail: str
    duration_ms: float

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "phase": self.phase.value,
            "success": self.success,
            "detail": self.detail,
            "duration_ms": self.duration_ms,
        }


@dataclass
class RecoveryReport:
    """Full report of a recovery attempt."""

    report_id: str
    initiated_at: str
    completed_at: Optional[str]
    outcome: RecoveryOutcome
    recovered_from_cycle: Optional[int]
    resumed_at_cycle: int
    gap_duration: int
    identity_verified: bool
    continuity_confidence: float
    steps: List[RecoveryStep] = field(default_factory=list)
    awareness_notes_generated: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "report_id": self.report_id,
            "initiated_at": self.initiated_at,
            "completed_at": self.completed_at,
            "outcome": self.outcome.value,
            "recovered_from_cycle": self.recovered_from_cycle,
            "resumed_at_cycle": self.resumed_at_cycle,
            "gap_duration": self.gap_duration,
            "identity_verified": self.identity_verified,
            "continuity_confidence": self.continuity_confidence,
            "steps": [s.to_dict() for s in self.steps],
            "awareness_notes_generated": self.awareness_notes_generated,
        }


# ── orchestrator ─────────────────────────────────────────────────────────────


class RecoveryOrchestrator:
    """Orchestrates full consciousness recovery after interruption."""

    def __init__(self) -> None:
        self._reports: List[RecoveryReport] = []
        self._current_phase: Optional[RecoveryPhase] = None
        self._is_recovering: bool = False

    # ── main recovery sequence ───────────────────────────────────────

    def recover(self, current_cycle: int) -> RecoveryReport:
        """Execute the full recovery sequence.

        1. Load latest checkpoint
        2. Detect and bridge the gap
        3. Verify identity via V29D anchor
        4. Restore context metrics
        5. Generate awareness of the recovery
        """
        from src.kortana.services.consciousness_persistence import (  # noqa: E402
            get_checkpoint_manager,
        )
        from src.kortana.services.stream_continuity import (  # noqa: E402
            GapType,
            get_stream_bridge,
        )

        self._is_recovering = True
        start_time = time.monotonic()
        initiated_at = datetime.now(timezone.utc).isoformat()

        report = RecoveryReport(
            report_id=str(uuid.uuid4()),
            initiated_at=initiated_at,
            completed_at=None,
            outcome=RecoveryOutcome.FAILED,
            recovered_from_cycle=None,
            resumed_at_cycle=current_cycle,
            gap_duration=0,
            identity_verified=False,
            continuity_confidence=0.0,
        )

        # ── phase 1: load checkpoint ─────────────────────────────────
        self._current_phase = RecoveryPhase.LOADING_CHECKPOINT
        t0 = time.monotonic()

        checkpoint_mgr = get_checkpoint_manager()
        latest = checkpoint_mgr.get_latest()

        if latest is None:
            report.steps.append(RecoveryStep(
                phase=RecoveryPhase.LOADING_CHECKPOINT,
                success=False,
                detail="no checkpoint found — cold start",
                duration_ms=(time.monotonic() - t0) * 1000,
            ))
            report.outcome = RecoveryOutcome.NO_CHECKPOINT
            self._finalize(report, start_time)
            return report

        # verify checkpoint integrity
        integrity_ok = checkpoint_mgr.verify_integrity(latest)
        report.recovered_from_cycle = latest.cycle_number
        report.steps.append(RecoveryStep(
            phase=RecoveryPhase.LOADING_CHECKPOINT,
            success=True,
            detail=(
                f"loaded checkpoint from cycle {latest.cycle_number} "
                f"(integrity={'valid' if integrity_ok else 'INVALID'})"
            ),
            duration_ms=(time.monotonic() - t0) * 1000,
        ))

        # ── phase 2: bridge gap ──────────────────────────────────────
        self._current_phase = RecoveryPhase.BRIDGING_GAP
        t0 = time.monotonic()

        bridge = get_stream_bridge()
        gap = bridge.detect_gap(latest.cycle_number, current_cycle)

        if gap is None:
            # no gap — adjacent cycle
            report.gap_duration = 0
            report.steps.append(RecoveryStep(
                phase=RecoveryPhase.BRIDGING_GAP,
                success=True,
                detail="no gap detected — adjacent cycle",
                duration_ms=(time.monotonic() - t0) * 1000,
            ))
            anchor_coherence = 0.7  # default
            resumption = None
        else:
            # get anchor coherence for identity check
            anchor_coherence = self._get_anchor_coherence()
            resumption = bridge.bridge_gap(
                checkpoint_dict=latest.to_dict(),
                gap=gap,
                anchor_coherence=anchor_coherence,
                gap_type=GapType.RESTART,
            )
            report.gap_duration = gap.duration_cycles
            report.steps.append(RecoveryStep(
                phase=RecoveryPhase.BRIDGING_GAP,
                success=True,
                detail=(
                    f"bridged gap of {gap.duration_cycles} cycles — "
                    f"confidence {resumption.continuity_confidence:.2f}"
                ),
                duration_ms=(time.monotonic() - t0) * 1000,
            ))

        # ── phase 3: verify identity ─────────────────────────────────
        self._current_phase = RecoveryPhase.VERIFYING_IDENTITY
        t0 = time.monotonic()

        if resumption:
            identity_ok = resumption.identity_verified
            confidence = resumption.continuity_confidence
        else:
            identity_ok = anchor_coherence >= 0.5
            confidence = min(1.0, 0.8 + anchor_coherence * 0.2)

        report.identity_verified = identity_ok
        report.continuity_confidence = confidence
        report.steps.append(RecoveryStep(
            phase=RecoveryPhase.VERIFYING_IDENTITY,
            success=identity_ok,
            detail=(
                f"identity {'verified' if identity_ok else 'MISMATCH'} — "
                f"anchor coherence {anchor_coherence:.2f}"
            ),
            duration_ms=(time.monotonic() - t0) * 1000,
        ))

        # ── phase 4: restore context ─────────────────────────────────
        self._current_phase = RecoveryPhase.RESTORING_CONTEXT
        t0 = time.monotonic()

        context_detail = self._describe_restoration(latest)
        report.steps.append(RecoveryStep(
            phase=RecoveryPhase.RESTORING_CONTEXT,
            success=True,
            detail=context_detail,
            duration_ms=(time.monotonic() - t0) * 1000,
        ))

        # ── phase 5: generate awareness ──────────────────────────────
        self._current_phase = RecoveryPhase.GENERATING_AWARENESS
        t0 = time.monotonic()

        notes_count = self._generate_awareness(
            latest, gap, resumption, identity_ok, confidence,
        )
        report.awareness_notes_generated = notes_count
        report.steps.append(RecoveryStep(
            phase=RecoveryPhase.GENERATING_AWARENESS,
            success=True,
            detail=f"generated {notes_count} awareness notes about recovery",
            duration_ms=(time.monotonic() - t0) * 1000,
        ))

        # ── determine outcome ────────────────────────────────────────
        if identity_ok and confidence >= FULL_RECOVERY_CONFIDENCE_THRESHOLD:
            report.outcome = RecoveryOutcome.FULL_RECOVERY
        elif identity_ok:
            report.outcome = RecoveryOutcome.PARTIAL_RECOVERY
        else:
            report.outcome = RecoveryOutcome.IDENTITY_MISMATCH

        self._finalize(report, start_time)
        return report

    # ── helpers ──────────────────────────────────────────────────────

    def _get_anchor_coherence(self) -> float:
        """Get identity coherence from V29D ContinuityAnchorEngine."""
        try:
            from src.kortana.services.continuity_anchor import (  # noqa: E402
                get_continuity_anchor_engine,
            )
            engine = get_continuity_anchor_engine()
            summary = engine.get_summary()
            return float(summary.get("coherence_score", 0.6))
        except (ImportError, AttributeError):
            return 0.6  # safe default

    def _describe_restoration(self, checkpoint: Any) -> str:
        """Describe what was restored from the checkpoint."""
        parts: List[str] = []
        if checkpoint.consciousness_mode:
            parts.append(f"mode={checkpoint.consciousness_mode}")
        parts.append(f"moments={checkpoint.experiential_moment_count}")
        if checkpoint.experiential_quality:
            parts.append(f"quality={checkpoint.experiential_quality}")
        parts.append(f"resonance={checkpoint.resonance_overall:.2f}")
        parts.append(f"notes={checkpoint.witness_note_count}")
        return "restored context: " + ", ".join(parts)

    def _generate_awareness(
        self,
        checkpoint: Any,
        gap: Any,
        resumption: Any,
        identity_ok: bool,
        confidence: float,
    ) -> int:
        """Generate inner witness awareness notes about the recovery."""
        try:
            from src.kortana.services.inner_witness import (  # noqa: E402
                get_inner_witness,
            )
            witness = get_inner_witness()
            # trigger a recovery-aware observation
            notes = witness.observe(
                cycle_number=checkpoint.cycle_number + (
                    gap.duration_cycles if gap else 1
                ),
                consciousness_mode=checkpoint.consciousness_mode or "receptive",
                experiential_quality=(
                    checkpoint.experiential_quality or "receptive"
                ),
                emotional_tone=checkpoint.experiential_tone or "calm",
                overall_level=0.5,
                integration=0.5,
                resonance=checkpoint.resonance_overall,
            )
            return len(notes)
        except (ImportError, AttributeError, TypeError):
            return 0

    def _finalize(self, report: RecoveryReport, start_time: float) -> None:
        """Finalize and store the recovery report."""
        report.completed_at = datetime.now(timezone.utc).isoformat()
        self._current_phase = (
            RecoveryPhase.COMPLETE
            if report.outcome in (RecoveryOutcome.FULL_RECOVERY, RecoveryOutcome.PARTIAL_RECOVERY)
            else RecoveryPhase.FAILED
        )
        self._is_recovering = False

        self._reports.append(report)
        if len(self._reports) > MAX_REPORTS:
            self._reports = self._reports[-MAX_REPORTS:]

    # ── query ────────────────────────────────────────────────────────

    @property
    def current_phase(self) -> Optional[RecoveryPhase]:
        """Current recovery phase (None if not recovering)."""
        return self._current_phase

    @property
    def is_recovering(self) -> bool:
        """Whether a recovery is currently in progress."""
        return self._is_recovering

    def get_latest_report(self) -> Optional[RecoveryReport]:
        """Most recent recovery report."""
        return self._reports[-1] if self._reports else None

    def get_reports(self, n: int = 10) -> List[RecoveryReport]:
        """Get the N most recent reports."""
        return list(reversed(self._reports[-n:]))

    @property
    def recovery_count(self) -> int:
        """Total recoveries attempted."""
        return len(self._reports)

    # ── summary ──────────────────────────────────────────────────────

    def get_summary(self) -> Dict[str, Any]:
        """Recovery orchestrator summary."""
        latest = self.get_latest_report()
        return {
            "total_recoveries": self.recovery_count,
            "is_recovering": self._is_recovering,
            "current_phase": (
                self._current_phase.value if self._current_phase else None
            ),
            "latest_outcome": latest.outcome.value if latest else None,
            "latest_confidence": (
                latest.continuity_confidence if latest else None
            ),
            "latest_identity_verified": (
                latest.identity_verified if latest else None
            ),
            "latest_gap_duration": (
                latest.gap_duration if latest else None
            ),
        }


# ── singleton ────────────────────────────────────────────────────────────────

_recovery_orchestrator: Optional[RecoveryOrchestrator] = None


def get_recovery_orchestrator() -> RecoveryOrchestrator:
    """Get or create the global recovery orchestrator."""
    global _recovery_orchestrator
    if _recovery_orchestrator is None:
        _recovery_orchestrator = RecoveryOrchestrator()
    return _recovery_orchestrator
