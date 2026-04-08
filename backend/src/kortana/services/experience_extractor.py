"""V27A — experience extractor.

extracts structured lessons from completed heartbeat cycles.
each beat is raw data; this turns it into remembered experience.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ─── enums ────────────────────────────────────────────────────────────────────

class LessonType(str, Enum):
    """Classification of extracted lessons."""
    SUCCESS = "success"
    FAILURE = "failure"
    DEFERRAL = "deferral"
    ANOMALY = "anomaly"
    INSIGHT = "insight"
    MISSED_OPPORTUNITY = "missed_opportunity"


class LessonSeverity(str, Enum):
    """How important a lesson is."""
    CRITICAL = "critical"
    SIGNIFICANT = "significant"
    MODERATE = "moderate"
    MINOR = "minor"
    TRIVIAL = "trivial"


# ─── dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class Lesson:
    """A single extracted lesson from a heartbeat cycle."""
    lesson_id: str = ""
    lesson_type: LessonType = LessonType.INSIGHT
    severity: LessonSeverity = LessonSeverity.MODERATE
    description: str = ""
    source_beat_id: str = ""
    source_cycle: int = 0
    context: dict[str, Any] = field(default_factory=dict)
    actionable: bool = False
    action_suggestion: str = ""
    extracted_at: str = ""

    def __post_init__(self) -> None:
        if not self.lesson_id:
            self.lesson_id = f"lesson-{uuid.uuid4().hex[:12]}"
        if not self.extracted_at:
            self.extracted_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "lesson_id": self.lesson_id,
            "lesson_type": self.lesson_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "source_beat_id": self.source_beat_id,
            "source_cycle": self.source_cycle,
            "context": self.context,
            "actionable": self.actionable,
            "action_suggestion": self.action_suggestion,
            "extracted_at": self.extracted_at,
        }


@dataclass
class Experience:
    """A complete extracted experience from a single heartbeat cycle."""
    experience_id: str = ""
    source_beat_id: str = ""
    cycle_number: int = 0
    lessons: list[Lesson] = field(default_factory=list)
    observation_count: int = 0
    decision_count: int = 0
    action_count: int = 0
    deferral_count: int = 0
    reflection_count: int = 0
    beat_duration_ms: float = 0
    beat_state: str = ""
    extracted_at: str = ""
    experience_hash: str = ""

    def __post_init__(self) -> None:
        if not self.experience_id:
            self.experience_id = f"exp-{uuid.uuid4().hex[:12]}"
        if not self.extracted_at:
            self.extracted_at = datetime.now(timezone.utc).isoformat()
        if not self.experience_hash:
            raw = f"{self.experience_id}:{self.cycle_number}:{self.extracted_at}"
            self.experience_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "experience_id": self.experience_id,
            "source_beat_id": self.source_beat_id,
            "cycle_number": self.cycle_number,
            "lessons": [lesson.to_dict() for lesson in self.lessons],
            "lesson_count": len(self.lessons),
            "observation_count": self.observation_count,
            "decision_count": self.decision_count,
            "action_count": self.action_count,
            "deferral_count": self.deferral_count,
            "reflection_count": self.reflection_count,
            "beat_duration_ms": self.beat_duration_ms,
            "beat_state": self.beat_state,
            "extracted_at": self.extracted_at,
            "experience_hash": self.experience_hash,
        }


# ─── experience extractor ────────────────────────────────────────────────────

class ExperienceExtractor:
    """Extracts structured lessons from completed heartbeat cycles.

    Takes raw beat data (observations, decisions, actions, deferrals,
    reflections) and produces Experience records with typed Lessons.
    This is the first step of the learning loop: before you can learn
    from experience, you must first *have* experience — structured,
    classified, and retrievable.
    """

    def __init__(self) -> None:
        self._experiences: list[Experience] = []
        self._by_id: dict[str, Experience] = {}
        self._by_cycle: dict[int, Experience] = {}

    # ── extraction ────────────────────────────────────────────────────────

    def extract_from_beat(
        self,
        beat_id: str,
        cycle_number: int,
        state: str,
        observations: list[dict[str, Any]],
        decisions: list[dict[str, Any]],
        actions: list[str],
        deferrals: list[str],
        reflections: list[str],
        duration_ms: float = 0,
    ) -> Experience:
        """Extract an Experience from a completed heartbeat beat."""
        exp = Experience(
            source_beat_id=beat_id,
            cycle_number=cycle_number,
            observation_count=len(observations),
            decision_count=len(decisions),
            action_count=len(actions),
            deferral_count=len(deferrals),
            reflection_count=len(reflections),
            beat_duration_ms=duration_ms,
            beat_state=state,
        )

        # extract lessons from each data source
        self._extract_observation_lessons(exp, observations)
        self._extract_decision_lessons(exp, decisions)
        self._extract_action_lessons(exp, actions)
        self._extract_deferral_lessons(exp, deferrals)
        self._extract_reflection_lessons(exp, reflections)
        self._extract_meta_lessons(exp)

        self._experiences.append(exp)
        self._by_id[exp.experience_id] = exp
        self._by_cycle[cycle_number] = exp
        return exp

    def _extract_observation_lessons(
        self, exp: Experience, observations: list[dict[str, Any]]
    ) -> None:
        """Extract lessons from observations."""
        severe = [o for o in observations if o.get("severity") in ("warning", "critical", "error")]
        if severe:
            exp.lessons.append(Lesson(
                lesson_type=LessonType.ANOMALY,
                severity=LessonSeverity.SIGNIFICANT,
                description=f"{len(severe)} concerning observation(s) detected",
                source_beat_id=exp.source_beat_id,
                source_cycle=exp.cycle_number,
                context={"severe_observations": [o.get("description", "") for o in severe]},
                actionable=True,
                action_suggestion="investigate root causes of severe observations",
            ))
        if not observations:
            exp.lessons.append(Lesson(
                lesson_type=LessonType.MISSED_OPPORTUNITY,
                severity=LessonSeverity.MODERATE,
                description="no observations recorded — cycle may have been blind",
                source_beat_id=exp.source_beat_id,
                source_cycle=exp.cycle_number,
                actionable=True,
                action_suggestion="ensure observation phase is collecting data",
            ))

    def _extract_decision_lessons(
        self, exp: Experience, decisions: list[dict[str, Any]]
    ) -> None:
        """Extract lessons from decisions."""
        high_priority = [d for d in decisions if d.get("priority", 5) <= 1]
        deferred_decisions = [d for d in decisions if d.get("deferred")]
        if high_priority:
            exp.lessons.append(Lesson(
                lesson_type=LessonType.INSIGHT,
                severity=LessonSeverity.SIGNIFICANT,
                description=f"{len(high_priority)} high-priority decision(s) made",
                source_beat_id=exp.source_beat_id,
                source_cycle=exp.cycle_number,
                context={"high_priority_actions": [d.get("action_type", "") for d in high_priority]},
            ))
        if deferred_decisions:
            exp.lessons.append(Lesson(
                lesson_type=LessonType.DEFERRAL,
                severity=LessonSeverity.MODERATE,
                description=f"{len(deferred_decisions)} decision(s) were deferred",
                source_beat_id=exp.source_beat_id,
                source_cycle=exp.cycle_number,
                context={"deferred_actions": [d.get("action_type", "") for d in deferred_decisions]},
                actionable=True,
                action_suggestion="review deferred decisions for accumulation risk",
            ))

    def _extract_action_lessons(
        self, exp: Experience, actions: list[str]
    ) -> None:
        """Extract lessons from actions taken."""
        if actions:
            exp.lessons.append(Lesson(
                lesson_type=LessonType.SUCCESS,
                severity=LessonSeverity.MINOR,
                description=f"{len(actions)} action(s) completed this cycle",
                source_beat_id=exp.source_beat_id,
                source_cycle=exp.cycle_number,
                context={"actions": actions},
            ))
        elif exp.decision_count > 0:
            exp.lessons.append(Lesson(
                lesson_type=LessonType.FAILURE,
                severity=LessonSeverity.SIGNIFICANT,
                description="decisions were made but no actions were taken",
                source_beat_id=exp.source_beat_id,
                source_cycle=exp.cycle_number,
                actionable=True,
                action_suggestion="investigate decision-to-action breakdown",
            ))

    def _extract_deferral_lessons(
        self, exp: Experience, deferrals: list[str]
    ) -> None:
        """Extract lessons from deferrals."""
        if len(deferrals) >= 3:
            exp.lessons.append(Lesson(
                lesson_type=LessonType.ANOMALY,
                severity=LessonSeverity.SIGNIFICANT,
                description=f"high deferral count ({len(deferrals)}) — possible overload or avoidance",
                source_beat_id=exp.source_beat_id,
                source_cycle=exp.cycle_number,
                context={"deferrals": deferrals},
                actionable=True,
                action_suggestion="assess whether deferrals are strategic or symptomatic",
            ))

    def _extract_reflection_lessons(
        self, exp: Experience, reflections: list[str]
    ) -> None:
        """Extract lessons from reflections."""
        if reflections:
            exp.lessons.append(Lesson(
                lesson_type=LessonType.INSIGHT,
                severity=LessonSeverity.MINOR,
                description=f"{len(reflections)} reflection(s) captured",
                source_beat_id=exp.source_beat_id,
                source_cycle=exp.cycle_number,
                context={"reflections": reflections},
            ))
        elif exp.action_count > 0:
            exp.lessons.append(Lesson(
                lesson_type=LessonType.MISSED_OPPORTUNITY,
                severity=LessonSeverity.MINOR,
                description="actions were taken but no reflections recorded",
                source_beat_id=exp.source_beat_id,
                source_cycle=exp.cycle_number,
                actionable=True,
                action_suggestion="add post-action reflection to capture learning",
            ))

    def _extract_meta_lessons(self, exp: Experience) -> None:
        """Extract meta-level lessons about the cycle itself."""
        # slow cycle
        if exp.beat_duration_ms > 5000:
            exp.lessons.append(Lesson(
                lesson_type=LessonType.ANOMALY,
                severity=LessonSeverity.MODERATE,
                description=f"cycle took {exp.beat_duration_ms:.0f}ms — above 5s threshold",
                source_beat_id=exp.source_beat_id,
                source_cycle=exp.cycle_number,
                actionable=True,
                action_suggestion="investigate slow cycle causes",
            ))
        # empty cycle
        if (exp.observation_count == 0 and exp.decision_count == 0
                and exp.action_count == 0):
            exp.lessons.append(Lesson(
                lesson_type=LessonType.FAILURE,
                severity=LessonSeverity.SIGNIFICANT,
                description="empty cycle — no observations, decisions, or actions",
                source_beat_id=exp.source_beat_id,
                source_cycle=exp.cycle_number,
                actionable=True,
                action_suggestion="verify cycle phases are executing",
            ))
        # degraded state
        if exp.beat_state in ("degraded", "dormant"):
            exp.lessons.append(Lesson(
                lesson_type=LessonType.ANOMALY,
                severity=LessonSeverity.CRITICAL if exp.beat_state == "dormant" else LessonSeverity.SIGNIFICANT,
                description=f"cycle ran in {exp.beat_state} state",
                source_beat_id=exp.source_beat_id,
                source_cycle=exp.cycle_number,
                actionable=True,
                action_suggestion="investigate and resolve degraded condition",
            ))

    # ── retrieval ─────────────────────────────────────────────────────────

    def get_experience(self, experience_id: str) -> Experience | None:
        """Get a specific experience by ID."""
        return self._by_id.get(experience_id)

    def get_by_cycle(self, cycle_number: int) -> Experience | None:
        """Get experience for a specific cycle number."""
        return self._by_cycle.get(cycle_number)

    def get_recent(self, n: int = 10) -> list[Experience]:
        """Get the N most recent experiences."""
        return list(reversed(self._experiences[-n:]))

    def get_lessons_by_type(self, lesson_type: LessonType) -> list[Lesson]:
        """Get all lessons of a specific type across all experiences."""
        result: list[Lesson] = []
        for exp in self._experiences:
            result.extend(ls for ls in exp.lessons if ls.lesson_type == lesson_type)
        return result

    def get_actionable_lessons(self) -> list[Lesson]:
        """Get all actionable lessons that haven't been addressed."""
        result: list[Lesson] = []
        for exp in self._experiences:
            result.extend(ls for ls in exp.lessons if ls.actionable)
        return result

    # ── properties ────────────────────────────────────────────────────────

    @property
    def experience_count(self) -> int:
        return len(self._experiences)

    @property
    def total_lessons(self) -> int:
        return sum(len(e.lessons) for e in self._experiences)

    @property
    def total_actionable(self) -> int:
        return sum(1 for e in self._experiences for ls in e.lessons if ls.actionable)

    @property
    def lesson_type_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for exp in self._experiences:
            for lesson in exp.lessons:
                key = lesson.lesson_type.value
                counts[key] = counts.get(key, 0) + 1
        return counts

    # ── summary ───────────────────────────────────────────────────────────

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of all extracted experiences."""
        avg_lessons = (
            self.total_lessons / self.experience_count
            if self.experience_count > 0 else 0
        )
        return {
            "experience_count": self.experience_count,
            "total_lessons": self.total_lessons,
            "total_actionable": self.total_actionable,
            "avg_lessons_per_experience": round(avg_lessons, 1),
            "lesson_type_counts": self.lesson_type_counts,
        }


# ─── singleton ────────────────────────────────────────────────────────────────

_instance: ExperienceExtractor | None = None


def get_experience_extractor() -> ExperienceExtractor:
    """Get or create the singleton ExperienceExtractor."""
    global _instance
    if _instance is None:
        _instance = ExperienceExtractor()
    return _instance
