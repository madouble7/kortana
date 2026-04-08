"""V27D — feedback integrator.

closes the loop by feeding learned adaptations back into the heartbeat.
experience → pattern → adaptation → feedback → next cycle.
this is the service that makes learning *real* — not just noticed, but applied.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ─── dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class LearningCycleReport:
    """Report on one complete learning cycle (extract → recognize → adapt → feedback)."""
    report_id: str = ""
    cycle_number: int = 0
    experiences_extracted: int = 0
    lessons_extracted: int = 0
    patterns_recognized: int = 0
    patterns_actionable: int = 0
    adaptations_proposed: int = 0
    adaptations_activated: int = 0
    adaptations_expired: int = 0
    adaptations_rolled_back: int = 0
    learning_velocity: float = 0.0  # lessons per cycle (rolling avg)
    adaptation_effectiveness: float = 0.0  # 0-1
    context_injections: list[str] = field(default_factory=list)
    generated_at: str = ""
    report_hash: str = ""

    def __post_init__(self) -> None:
        if not self.report_id:
            self.report_id = f"lrep-{uuid.uuid4().hex[:12]}"
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()
        if not self.report_hash:
            raw = f"{self.report_id}:{self.cycle_number}:{self.generated_at}"
            self.report_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "cycle_number": self.cycle_number,
            "experiences_extracted": self.experiences_extracted,
            "lessons_extracted": self.lessons_extracted,
            "patterns_recognized": self.patterns_recognized,
            "patterns_actionable": self.patterns_actionable,
            "adaptations_proposed": self.adaptations_proposed,
            "adaptations_activated": self.adaptations_activated,
            "adaptations_expired": self.adaptations_expired,
            "adaptations_rolled_back": self.adaptations_rolled_back,
            "learning_velocity": round(self.learning_velocity, 2),
            "adaptation_effectiveness": round(self.adaptation_effectiveness, 2),
            "context_injections": self.context_injections,
            "generated_at": self.generated_at,
            "report_hash": self.report_hash,
        }


@dataclass
class ContextInjection:
    """A piece of learned context to inject into the next cycle."""
    injection_id: str = ""
    category: str = ""  # adaptation, pattern_alert, learning_note
    content: str = ""
    source_adaptation_id: str = ""
    source_pattern_id: str = ""
    priority: int = 5  # 1=highest, 10=lowest
    injected_at: str = ""

    def __post_init__(self) -> None:
        if not self.injection_id:
            self.injection_id = f"inj-{uuid.uuid4().hex[:12]}"
        if not self.injected_at:
            self.injected_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "injection_id": self.injection_id,
            "category": self.category,
            "content": self.content,
            "source_adaptation_id": self.source_adaptation_id,
            "source_pattern_id": self.source_pattern_id,
            "priority": self.priority,
            "injected_at": self.injected_at,
        }


# ─── feedback integrator ─────────────────────────────────────────────────────

class FeedbackIntegrator:
    """Closes the learning loop by integrating everything back into cycles.

    Orchestrates the full learning pipeline:
    1. Takes experience extraction results
    2. Takes pattern recognition results
    3. Takes behavioral adaptation results
    4. Produces context injections for the next cycle
    5. Generates learning cycle reports
    6. Tracks learning velocity and adaptation effectiveness

    This is the service that makes the learning loop *closed* — without it,
    experiences are extracted, patterns are noticed, adaptations are proposed,
    but nothing actually changes. FeedbackIntegrator is what makes the
    next beat genuinely different from the last.
    """

    def __init__(self) -> None:
        self._reports: list[LearningCycleReport] = []
        self._by_id: dict[str, LearningCycleReport] = {}
        self._injections: list[ContextInjection] = []
        self._pending_injections: list[ContextInjection] = []
        self._total_lessons: int = 0
        self._lesson_counts: list[int] = []  # per-cycle lesson counts for velocity

    # ── integration ───────────────────────────────────────────────────────

    def integrate(
        self,
        cycle_number: int,
        experience_summary: dict[str, Any],
        pattern_summary: dict[str, Any],
        adaptation_summary: dict[str, Any],
        active_adaptations: list[dict[str, Any]] | None = None,
        actionable_patterns: list[dict[str, Any]] | None = None,
    ) -> LearningCycleReport:
        """Run one complete feedback integration cycle.

        Takes summaries from all three V27 components and produces
        a learning report + context injections for the next cycle.
        """
        lessons = experience_summary.get("total_lessons", 0)
        self._total_lessons += lessons
        self._lesson_counts.append(lessons)

        # compute learning velocity (rolling average over last 10 cycles)
        recent = self._lesson_counts[-10:]
        velocity = sum(recent) / max(1, len(recent))

        # compute adaptation effectiveness
        effectiveness = adaptation_summary.get("effectiveness_rate", 0.0)

        report = LearningCycleReport(
            cycle_number=cycle_number,
            experiences_extracted=experience_summary.get("experience_count", 0),
            lessons_extracted=lessons,
            patterns_recognized=pattern_summary.get("pattern_count", 0),
            patterns_actionable=pattern_summary.get("actionable_count", 0),
            adaptations_proposed=adaptation_summary.get("adaptation_count", 0),
            adaptations_activated=adaptation_summary.get("active_count", 0),
            adaptations_expired=adaptation_summary.get("status_counts", {}).get("expired", 0),
            adaptations_rolled_back=adaptation_summary.get("rollback_count", 0),
            learning_velocity=velocity,
            adaptation_effectiveness=effectiveness,
        )

        # generate context injections
        injections = self._generate_injections(
            cycle_number,
            active_adaptations or [],
            actionable_patterns or [],
            velocity,
            effectiveness,
        )
        report.context_injections = [inj.content for inj in injections]

        self._reports.append(report)
        self._by_id[report.report_id] = report
        return report

    def _generate_injections(
        self,
        cycle_number: int,
        active_adaptations: list[dict[str, Any]],
        actionable_patterns: list[dict[str, Any]],
        velocity: float,
        effectiveness: float,
    ) -> list[ContextInjection]:
        """Generate context injections based on current learning state."""
        injections: list[ContextInjection] = []

        # inject active adaptations as context
        for adapt in active_adaptations:
            inj = ContextInjection(
                category="adaptation",
                content=f"[active adaptation] {adapt.get('description', '')}: "
                        f"{adapt.get('parameter', '')} = {adapt.get('new_value', '')}",
                source_adaptation_id=adapt.get("adaptation_id", ""),
                priority=3,
            )
            injections.append(inj)

        # inject actionable pattern alerts
        for pat in actionable_patterns:
            inj = ContextInjection(
                category="pattern_alert",
                content=f"[pattern: {pat.get('strength', 'unknown')}] "
                        f"{pat.get('description', '')}: {pat.get('recommended_action', '')}",
                source_pattern_id=pat.get("pattern_id", ""),
                priority=2 if pat.get("strength") == "strong" else 4,
            )
            injections.append(inj)

        # inject learning velocity note
        if velocity > 0:
            trend = "accelerating" if len(self._lesson_counts) >= 3 and (
                self._lesson_counts[-1] > self._lesson_counts[-2] > self._lesson_counts[-3]
            ) else "steady" if len(self._lesson_counts) >= 2 and (
                abs(self._lesson_counts[-1] - self._lesson_counts[-2]) <= 1
            ) else "variable"
            inj = ContextInjection(
                category="learning_note",
                content=f"[learning velocity] {velocity:.1f} lessons/cycle ({trend})",
                priority=7,
            )
            injections.append(inj)

        # inject effectiveness warning if low
        if effectiveness > 0 and effectiveness < 0.4 and len(self._reports) >= 3:
            inj = ContextInjection(
                category="learning_note",
                content=f"[warning] adaptation effectiveness is low ({effectiveness:.0%}) — "
                        "consider reviewing adaptation strategy",
                priority=2,
            )
            injections.append(inj)

        # store injections
        self._injections.extend(injections)
        self._pending_injections = list(injections)
        return injections

    # ── context provision ─────────────────────────────────────────────────

    def get_pending_injections(self) -> list[ContextInjection]:
        """Get context injections pending for the next cycle."""
        return list(self._pending_injections)

    def consume_injections(self) -> list[dict[str, Any]]:
        """Consume pending injections (clears them). Called by cycle start."""
        result = [inj.to_dict() for inj in self._pending_injections]
        self._pending_injections = []
        return result

    def get_context_for_cycle(self) -> dict[str, Any]:
        """Get the full learning context to inject into the next cycle.

        Returns a dict suitable for merging into CycleContext.notes.
        """
        pending = self.get_pending_injections()
        if not pending:
            return {}

        # sort by priority (lower = higher priority)
        pending.sort(key=lambda x: x.priority)

        return {
            "learning_injections": [inj.to_dict() for inj in pending],
            "injection_count": len(pending),
            "learning_velocity": self.learning_velocity,
            "adaptation_effectiveness": self.adaptation_effectiveness,
            "total_lessons_learned": self._total_lessons,
        }

    # ── retrieval ─────────────────────────────────────────────────────────

    def get_report(self, report_id: str) -> LearningCycleReport | None:
        """Get a specific learning cycle report."""
        return self._by_id.get(report_id)

    def get_recent(self, n: int = 10) -> list[LearningCycleReport]:
        """Get the N most recent reports."""
        return list(reversed(self._reports[-n:]))

    def get_velocity_trend(self, n: int = 10) -> list[float]:
        """Get the learning velocity over the last N cycles."""
        return list(self._lesson_counts[-n:])

    # ── properties ────────────────────────────────────────────────────────

    @property
    def report_count(self) -> int:
        return len(self._reports)

    @property
    def total_lessons_learned(self) -> int:
        return self._total_lessons

    @property
    def learning_velocity(self) -> float:
        """Current rolling average lessons per cycle."""
        recent = self._lesson_counts[-10:]
        if not recent:
            return 0.0
        return round(sum(recent) / len(recent), 2)

    @property
    def adaptation_effectiveness(self) -> float:
        """Most recent adaptation effectiveness."""
        if not self._reports:
            return 0.0
        return self._reports[-1].adaptation_effectiveness

    @property
    def total_injections(self) -> int:
        return len(self._injections)

    @property
    def pending_injection_count(self) -> int:
        return len(self._pending_injections)

    # ── summary ───────────────────────────────────────────────────────────

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the feedback integration state."""
        return {
            "report_count": self.report_count,
            "total_lessons_learned": self.total_lessons_learned,
            "learning_velocity": self.learning_velocity,
            "adaptation_effectiveness": self.adaptation_effectiveness,
            "total_injections": self.total_injections,
            "pending_injections": self.pending_injection_count,
            "velocity_trend": self.get_velocity_trend(5),
        }


# ─── singleton ────────────────────────────────────────────────────────────────

_instance: FeedbackIntegrator | None = None


def get_feedback_integrator() -> FeedbackIntegrator:
    """Get or create the singleton FeedbackIntegrator."""
    global _instance
    if _instance is None:
        _instance = FeedbackIntegrator()
    return _instance
