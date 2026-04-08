"""V27B — pattern recognizer.

finds recurring patterns across multiple experiences.
experience extraction is remembering; pattern recognition is noticing.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ─── enums ────────────────────────────────────────────────────────────────────

class PatternType(str, Enum):
    """Classification of recognized patterns."""
    RECURRING_OBSERVATION = "recurring_observation"
    PERSISTENT_DEFERRAL = "persistent_deferral"
    DECISION_DRIFT = "decision_drift"
    ACTION_EFFECTIVENESS = "action_effectiveness"
    HEALTH_TREND = "health_trend"
    CYCLE_RHYTHM = "cycle_rhythm"
    ANOMALY_CLUSTER = "anomaly_cluster"
    LEARNING_SIGNAL = "learning_signal"


class PatternStrength(str, Enum):
    """Confidence level of a recognized pattern."""
    STRONG = "strong"       # >= 5 occurrences, >= 80% consistency
    MODERATE = "moderate"   # >= 3 occurrences, >= 60% consistency
    WEAK = "weak"           # >= 2 occurrences, >= 40% consistency
    EMERGING = "emerging"   # 1 occurrence, flagged for tracking


# ─── dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class PatternEvidence:
    """A single piece of evidence supporting a pattern."""
    cycle_number: int = 0
    experience_id: str = ""
    description: str = ""
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle_number": self.cycle_number,
            "experience_id": self.experience_id,
            "description": self.description,
            "timestamp": self.timestamp,
        }


@dataclass
class Pattern:
    """A recognized cross-cycle pattern."""
    pattern_id: str = ""
    pattern_type: PatternType = PatternType.LEARNING_SIGNAL
    strength: PatternStrength = PatternStrength.EMERGING
    description: str = ""
    evidence: list[PatternEvidence] = field(default_factory=list)
    first_seen_cycle: int = 0
    last_seen_cycle: int = 0
    occurrence_count: int = 0
    consistency: float = 0.0  # 0.0-1.0
    trending: str = ""  # stable, increasing, decreasing, new
    actionable: bool = False
    recommended_action: str = ""
    addressed: bool = False
    recognized_at: str = ""
    pattern_hash: str = ""

    def __post_init__(self) -> None:
        if not self.pattern_id:
            self.pattern_id = f"pat-{uuid.uuid4().hex[:12]}"
        if not self.recognized_at:
            self.recognized_at = datetime.now(timezone.utc).isoformat()
        if not self.pattern_hash:
            raw = f"{self.pattern_id}:{self.pattern_type.value}:{self.recognized_at}"
            self.pattern_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]

    def add_evidence(self, cycle_number: int, experience_id: str, description: str) -> None:
        """Add a new piece of evidence to this pattern."""
        self.evidence.append(PatternEvidence(
            cycle_number=cycle_number,
            experience_id=experience_id,
            description=description,
        ))
        self.occurrence_count = len(self.evidence)
        self.last_seen_cycle = cycle_number
        if not self.first_seen_cycle:
            self.first_seen_cycle = cycle_number
        self._recalculate_strength()

    def _recalculate_strength(self) -> None:
        """Recalculate pattern strength based on evidence."""
        n = self.occurrence_count
        if n >= 5 and self.consistency >= 0.8:
            self.strength = PatternStrength.STRONG
        elif n >= 3 and self.consistency >= 0.6:
            self.strength = PatternStrength.MODERATE
        elif n >= 2 and self.consistency >= 0.4:
            self.strength = PatternStrength.WEAK
        else:
            self.strength = PatternStrength.EMERGING

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type.value,
            "strength": self.strength.value,
            "description": self.description,
            "evidence": [e.to_dict() for e in self.evidence],
            "first_seen_cycle": self.first_seen_cycle,
            "last_seen_cycle": self.last_seen_cycle,
            "occurrence_count": self.occurrence_count,
            "consistency": self.consistency,
            "trending": self.trending,
            "actionable": self.actionable,
            "recommended_action": self.recommended_action,
            "addressed": self.addressed,
            "recognized_at": self.recognized_at,
            "pattern_hash": self.pattern_hash,
        }


# ─── pattern recognizer ──────────────────────────────────────────────────────

class PatternRecognizer:
    """Recognizes recurring patterns across multiple experiences.

    Analyzes sequences of Experience objects to detect trends, recurring
    themes, persistent deferrals, decision drift, and other cross-cycle
    patterns that single-cycle analysis would miss.
    """

    MIN_SAMPLE = 2  # minimum experiences before pattern recognition

    def __init__(self) -> None:
        self._patterns: list[Pattern] = []
        self._by_id: dict[str, Pattern] = {}
        self._by_type: dict[str, list[Pattern]] = {}
        self._analyzed_cycles: set[int] = set()

    # ── analysis ──────────────────────────────────────────────────────────

    def analyze(
        self,
        experiences: list[dict[str, Any]],
        cycle_range: tuple[int, int] | None = None,
    ) -> list[Pattern]:
        """Analyze a list of experiences and recognize patterns.

        Args:
            experiences: List of Experience.to_dict() outputs.
            cycle_range: Optional (start, end) cycle range for consistency calc.

        Returns:
            List of newly recognized or updated patterns.
        """
        if len(experiences) < self.MIN_SAMPLE:
            return []

        span = 1
        if cycle_range:
            span = max(1, cycle_range[1] - cycle_range[0] + 1)
        elif experiences:
            cycles = [e.get("cycle_number", 0) for e in experiences]
            if cycles:
                span = max(1, max(cycles) - min(cycles) + 1)

        new_or_updated: list[Pattern] = []

        new_or_updated.extend(self._detect_deferral_patterns(experiences, span))
        new_or_updated.extend(self._detect_observation_patterns(experiences, span))
        new_or_updated.extend(self._detect_action_patterns(experiences, span))
        new_or_updated.extend(self._detect_rhythm_patterns(experiences, span))
        new_or_updated.extend(self._detect_lesson_patterns(experiences, span))

        for exp in experiences:
            cn = exp.get("cycle_number", 0)
            if cn:
                self._analyzed_cycles.add(cn)

        return new_or_updated

    def _detect_deferral_patterns(
        self, experiences: list[dict[str, Any]], span: int
    ) -> list[Pattern]:
        """Detect persistent deferral patterns."""
        result: list[Pattern] = []
        high_deferral_exps = [
            e for e in experiences if e.get("deferral_count", 0) >= 2
        ]
        if len(high_deferral_exps) >= 2:
            consistency = len(high_deferral_exps) / max(1, span)
            pat = self._find_or_create(
                PatternType.PERSISTENT_DEFERRAL,
                "recurring high deferrals",
            )
            for e in high_deferral_exps:
                cn = e.get("cycle_number", 0)
                if cn not in {ev.cycle_number for ev in pat.evidence}:
                    pat.add_evidence(
                        cn, e.get("experience_id", ""),
                        f"cycle {cn}: {e.get('deferral_count', 0)} deferrals",
                    )
            pat.consistency = round(min(1.0, consistency), 2)
            pat.trending = self._compute_trend(
                [e.get("deferral_count", 0) for e in experiences]
            )
            pat.actionable = pat.strength in (PatternStrength.STRONG, PatternStrength.MODERATE)
            pat.recommended_action = "address deferred items to prevent accumulation"
            result.append(pat)
        return result

    def _detect_observation_patterns(
        self, experiences: list[dict[str, Any]], span: int
    ) -> list[Pattern]:
        """Detect patterns in observations."""
        result: list[Pattern] = []
        # anomaly clusters
        anomaly_lessons = []
        for e in experiences:
            for entry in e.get("lessons", []):
                if entry.get("lesson_type") == "anomaly":
                    anomaly_lessons.append((e, entry))
        if len(anomaly_lessons) >= 2:
            consistency = len(anomaly_lessons) / max(1, span)
            pat = self._find_or_create(
                PatternType.ANOMALY_CLUSTER,
                "recurring anomalies across cycles",
            )
            for exp, lesson in anomaly_lessons:
                cn = exp.get("cycle_number", 0)
                if cn not in {ev.cycle_number for ev in pat.evidence}:
                    pat.add_evidence(
                        cn, exp.get("experience_id", ""),
                        lesson.get("description", "anomaly detected"),
                    )
            pat.consistency = round(min(1.0, consistency), 2)
            pat.actionable = True
            pat.recommended_action = "investigate root cause of recurring anomalies"
            result.append(pat)
        return result

    def _detect_action_patterns(
        self, experiences: list[dict[str, Any]], span: int
    ) -> list[Pattern]:
        """Detect patterns in actions and effectiveness."""
        result: list[Pattern] = []
        # decision-action gap
        gap_exps = [
            e for e in experiences
            if e.get("decision_count", 0) > 0 and e.get("action_count", 0) == 0
        ]
        if len(gap_exps) >= 2:
            consistency = len(gap_exps) / max(1, span)
            pat = self._find_or_create(
                PatternType.DECISION_DRIFT,
                "decisions made but no actions follow",
            )
            for e in gap_exps:
                cn = e.get("cycle_number", 0)
                if cn not in {ev.cycle_number for ev in pat.evidence}:
                    pat.add_evidence(
                        cn, e.get("experience_id", ""),
                        f"cycle {cn}: {e.get('decision_count', 0)} decisions, 0 actions",
                    )
            pat.consistency = round(min(1.0, consistency), 2)
            pat.actionable = True
            pat.recommended_action = "close decision-to-action gap"
            result.append(pat)
        return result

    def _detect_rhythm_patterns(
        self, experiences: list[dict[str, Any]], span: int
    ) -> list[Pattern]:
        """Detect cycle rhythm patterns (duration, activity level)."""
        result: list[Pattern] = []
        durations = [e.get("beat_duration_ms", 0) for e in experiences if e.get("beat_duration_ms", 0) > 0]
        if len(durations) >= 3:
            avg = sum(durations) / len(durations)
            slow_exps = [e for e in experiences if e.get("beat_duration_ms", 0) > avg * 2]
            if len(slow_exps) >= 2:
                pat = self._find_or_create(
                    PatternType.CYCLE_RHYTHM,
                    "intermittent slow cycles detected",
                )
                for e in slow_exps:
                    cn = e.get("cycle_number", 0)
                    if cn not in {ev.cycle_number for ev in pat.evidence}:
                        pat.add_evidence(
                            cn, e.get("experience_id", ""),
                            f"cycle {cn}: {e.get('beat_duration_ms', 0):.0f}ms (avg {avg:.0f}ms)",
                        )
                pat.consistency = round(len(slow_exps) / max(1, span), 2)
                pat.trending = self._compute_trend(durations)
                pat.actionable = True
                pat.recommended_action = "investigate and optimize slow cycles"
                result.append(pat)
        return result

    def _detect_lesson_patterns(
        self, experiences: list[dict[str, Any]], span: int
    ) -> list[Pattern]:
        """Detect meta-patterns in lesson types."""
        result: list[Pattern] = []
        failure_exps = []
        for e in experiences:
            failures = [entry for entry in e.get("lessons", []) if entry.get("lesson_type") == "failure"]
            if failures:
                failure_exps.append((e, failures))
        if len(failure_exps) >= 2:
            consistency = len(failure_exps) / max(1, span)
            pat = self._find_or_create(
                PatternType.LEARNING_SIGNAL,
                "recurring failures indicate systemic issue",
            )
            for exp, fails in failure_exps:
                cn = exp.get("cycle_number", 0)
                if cn not in {ev.cycle_number for ev in pat.evidence}:
                    pat.add_evidence(
                        cn, exp.get("experience_id", ""),
                        f"cycle {cn}: {len(fails)} failure(s)",
                    )
            pat.consistency = round(min(1.0, consistency), 2)
            pat.actionable = True
            pat.recommended_action = "address root causes of repeated failures"
            result.append(pat)
        return result

    # ── helpers ───────────────────────────────────────────────────────────

    def _find_or_create(self, pattern_type: PatternType, description: str) -> Pattern:
        """Find existing pattern or create new one."""
        for pat in self._patterns:
            if pat.pattern_type == pattern_type and pat.description == description:
                return pat
        pat = Pattern(
            pattern_type=pattern_type,
            description=description,
        )
        self._patterns.append(pat)
        self._by_id[pat.pattern_id] = pat
        type_key = pattern_type.value
        if type_key not in self._by_type:
            self._by_type[type_key] = []
        self._by_type[type_key].append(pat)
        return pat

    @staticmethod
    def _compute_trend(values: list[float | int]) -> str:
        """Compute trend direction from a sequence of values."""
        if len(values) < 2:
            return "new"
        first_half = values[:len(values) // 2]
        second_half = values[len(values) // 2:]
        avg_first = sum(first_half) / max(1, len(first_half))
        avg_second = sum(second_half) / max(1, len(second_half))
        if avg_first == 0:
            return "new" if avg_second == 0 else "increasing"
        change = (avg_second - avg_first) / avg_first
        if change > 0.15:
            return "increasing"
        elif change < -0.15:
            return "decreasing"
        return "stable"

    # ── retrieval ─────────────────────────────────────────────────────────

    def get_pattern(self, pattern_id: str) -> Pattern | None:
        """Get a specific pattern by ID."""
        return self._by_id.get(pattern_id)

    def get_by_type(self, pattern_type: str) -> list[Pattern]:
        """Get all patterns of a specific type."""
        return list(self._by_type.get(pattern_type, []))

    def get_active(self) -> list[Pattern]:
        """Get all patterns not yet addressed."""
        return [p for p in self._patterns if not p.addressed]

    def get_actionable(self) -> list[Pattern]:
        """Get all patterns that are actionable and not addressed."""
        return [p for p in self._patterns if p.actionable and not p.addressed]

    def mark_addressed(self, pattern_id: str) -> bool:
        """Mark a pattern as addressed."""
        pat = self._by_id.get(pattern_id)
        if pat:
            pat.addressed = True
            return True
        return False

    # ── properties ────────────────────────────────────────────────────────

    @property
    def pattern_count(self) -> int:
        return len(self._patterns)

    @property
    def active_count(self) -> int:
        return len(self.get_active())

    @property
    def actionable_count(self) -> int:
        return len(self.get_actionable())

    @property
    def strong_count(self) -> int:
        return sum(1 for p in self._patterns if p.strength == PatternStrength.STRONG)

    # ── summary ───────────────────────────────────────────────────────────

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of all recognized patterns."""
        type_counts: dict[str, int] = {}
        strength_counts: dict[str, int] = {}
        for p in self._patterns:
            type_counts[p.pattern_type.value] = type_counts.get(p.pattern_type.value, 0) + 1
            strength_counts[p.strength.value] = strength_counts.get(p.strength.value, 0) + 1
        return {
            "pattern_count": self.pattern_count,
            "active_count": self.active_count,
            "actionable_count": self.actionable_count,
            "strong_count": self.strong_count,
            "analyzed_cycles": len(self._analyzed_cycles),
            "type_counts": type_counts,
            "strength_counts": strength_counts,
        }


# ─── singleton ────────────────────────────────────────────────────────────────

_instance: PatternRecognizer | None = None


def get_pattern_recognizer() -> PatternRecognizer:
    """Get or create the singleton PatternRecognizer."""
    global _instance
    if _instance is None:
        _instance = PatternRecognizer()
    return _instance
