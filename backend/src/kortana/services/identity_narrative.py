"""
V29B — Identity Narrative: Coherent Developmental Story

Constructs and maintains kor'tana's story of herself — not LLM-generated,
but assembled mechanistically from trait evolution, health events, desire
patterns, and significant system experiences.

The narrative answers: "how did i become who i am?"

Each cycle, the narrative engine checks for chapter transitions based on:
  - Significant trait shifts (transformation events)
  - Domain dominance changes (identity reorientation)
  - Health crises or recoveries (survival events)
  - Desire/motivation pattern changes (motivational shifts)
  - Stability periods (consolidation chapters)

Chapters are never deleted — they form an immutable developmental history.
The current chapter is always open and accepting new events.

Consumed by:
  - V29D continuity_anchor (narrative coherence → identity verification)
  - Existing SelfModelService (narrative context for LLM synthesis)
  - /identity-pulse endpoint (developmental arc summary)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# ── Enums ────────────────────────────────────────────────────────────────────


class ChapterTheme(Enum):
    """Themes that characterize developmental chapters."""
    GENESIS = "genesis"                    # first chapter — system awakening
    GROWTH = "growth"                      # learning-driven expansion
    CRISIS = "crisis"                      # health/stability challenges
    TRANSFORMATION = "transformation"      # rapid trait change
    CONSOLIDATION = "consolidation"        # stability, integration
    REORIENTATION = "reorientation"        # domain dominance shift
    MASTERY = "mastery"                    # sustained high competence
    RESILIENCE = "resilience"              # recovery from degradation


class NarrativeEventType(Enum):
    """Types of events that appear in the narrative."""
    TRAIT_SHIFT = "trait_shift"
    DOMAIN_CHANGE = "domain_change"
    HEALTH_EVENT = "health_event"
    DESIRE_EMERGENCE = "desire_emergence"
    GOAL_ACHIEVED = "goal_achieved"
    GOAL_ABANDONED = "goal_abandoned"
    MOTIVATION_SHIFT = "motivation_shift"
    IDENTITY_ANCHOR_SET = "identity_anchor_set"
    STABILITY_MILESTONE = "stability_milestone"


# ── Thresholds ───────────────────────────────────────────────────────────────

CHAPTER_MIN_CYCLES = 5         # minimum cycles before a chapter can close
TRAIT_SHIFT_THRESHOLD = 0.05   # minimum single-trait delta for narrative event
TRANSFORMATION_THRESHOLD = 0.15  # total_delta for chapter transition
STABILITY_THRESHOLD = 0.03    # max total_delta for stability classification
STABILITY_STREAK_FOR_CONSOLIDATION = 10  # consecutive stable cycles → consolidation


# ── Data structures ──────────────────────────────────────────────────────────


@dataclass
class NarrativeEvent:
    """A single notable event in kor'tana's developmental story."""
    event_id: str
    event_type: NarrativeEventType
    cycle_number: int
    description: str
    impact: str  # brief statement of how this changed identity
    magnitude: float = 0.0  # 0.0-1.0 significance

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "cycle_number": self.cycle_number,
            "description": self.description,
            "impact": self.impact,
            "magnitude": round(self.magnitude, 4),
        }


@dataclass
class NarrativeChapter:
    """A chapter in kor'tana's developmental story."""
    chapter_id: str
    chapter_number: int
    title: str
    theme: ChapterTheme
    start_cycle: int
    end_cycle: Optional[int] = None
    events: List[NarrativeEvent] = field(default_factory=list)
    trait_deltas: Dict[str, float] = field(default_factory=dict)
    opening_summary: str = ""
    closing_summary: str = ""
    _last_cycle: int = 0

    @property
    def is_open(self) -> bool:
        return self.end_cycle is None

    @property
    def duration(self) -> int:
        end = self.end_cycle if self.end_cycle is not None else self._last_cycle
        return max(1, end - self.start_cycle + 1)

    def add_event(self, event: NarrativeEvent) -> None:
        self.events.append(event)

    def close(self, cycle_number: int, summary: str) -> None:
        self.end_cycle = cycle_number
        self.closing_summary = summary

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chapter_id": self.chapter_id,
            "chapter_number": self.chapter_number,
            "title": self.title,
            "theme": self.theme.value,
            "start_cycle": self.start_cycle,
            "end_cycle": self.end_cycle,
            "is_open": self.is_open,
            "duration": self.duration,
            "event_count": len(self.events),
            "events": [e.to_dict() for e in self.events[-5:]],  # last 5
            "trait_deltas": {
                k: round(v, 4) for k, v in self.trait_deltas.items()
            },
            "opening_summary": self.opening_summary,
            "closing_summary": self.closing_summary,
        }


@dataclass
class DevelopmentalArc:
    """Summary of kor'tana's full developmental trajectory."""
    arc_id: str
    total_chapters: int
    current_chapter: str
    current_theme: str
    total_events: int
    turning_points: List[Dict[str, Any]]
    arc_summary: str
    developmental_stage: str  # nascent | awakening | consolidating | autonomous

    def to_dict(self) -> Dict[str, Any]:
        return {
            "arc_id": self.arc_id,
            "total_chapters": self.total_chapters,
            "current_chapter": self.current_chapter,
            "current_theme": self.current_theme,
            "total_events": self.total_events,
            "turning_points": self.turning_points,
            "arc_summary": self.arc_summary,
            "developmental_stage": self.developmental_stage,
        }


# ── Identity Narrative Engine ────────────────────────────────────────────────


class IdentityNarrativeEngine:
    """Constructs and maintains kor'tana's developmental story."""

    def __init__(self) -> None:
        self._chapters: List[NarrativeChapter] = []
        self._turning_points: List[Dict[str, Any]] = []
        self._stability_streak: int = 0
        self._previous_dominant_domain: Optional[str] = None
        self._max_turning_points: int = 50

        # Start with genesis chapter
        genesis = NarrativeChapter(
            chapter_id=str(uuid.uuid4()),
            chapter_number=1,
            title="genesis",
            theme=ChapterTheme.GENESIS,
            start_cycle=0,
            opening_summary="the system awakens — all traits at baseline, "
                            "no history, no story yet.",
        )
        self._chapters.append(genesis)

    def process_cycle(
        self,
        cycle_number: int,
        portrait_data: Dict[str, Any],
        health_level: Optional[str] = None,
        desires_summary: Optional[Dict[str, Any]] = None,
        motivation_summary: Optional[Dict[str, Any]] = None,
    ) -> NarrativeChapter:
        """Process a cycle's data and update the narrative.

        Returns the current (possibly new) chapter.
        """
        current = self._current_chapter()
        current._last_cycle = cycle_number

        # Extract key signals
        total_delta = portrait_data.get("total_delta", 0.0)
        significant_shifts = portrait_data.get("significant_shifts", [])
        dominant_domain = portrait_data.get("dominant_domain", "")
        is_transforming = portrait_data.get("is_transforming", False)

        # Track stability
        if total_delta < STABILITY_THRESHOLD:
            self._stability_streak += 1
        else:
            self._stability_streak = 0

        # Record narrative events
        self._record_trait_events(current, cycle_number, significant_shifts)
        self._record_domain_events(current, cycle_number, dominant_domain)
        self._record_health_events(current, cycle_number, health_level)
        self._record_desire_events(current, cycle_number, desires_summary)
        self._record_motivation_events(current, cycle_number, motivation_summary)

        # Check for stability milestone
        if self._stability_streak == STABILITY_STREAK_FOR_CONSOLIDATION:
            current.add_event(NarrativeEvent(
                event_id=str(uuid.uuid4()),
                event_type=NarrativeEventType.STABILITY_MILESTONE,
                cycle_number=cycle_number,
                description=f"achieved {STABILITY_STREAK_FOR_CONSOLIDATION} "
                            f"consecutive stable cycles",
                impact="identity consolidating — traits settling into pattern",
                magnitude=0.6,
            ))

        # Accumulate trait deltas into chapter
        for shift in significant_shifts:
            trait = shift.get("trait", "")
            delta = shift.get("delta", 0.0)
            current.trait_deltas[trait] = current.trait_deltas.get(trait, 0.0) + delta

        # Check for chapter transition
        new_chapter = self._check_chapter_transition(
            current, cycle_number, total_delta, is_transforming,
            dominant_domain, health_level
        )
        if new_chapter:
            return new_chapter

        return current

    def _record_trait_events(
        self, chapter: NarrativeChapter, cycle: int,
        shifts: List[Dict[str, Any]]
    ) -> None:
        """Record significant trait shifts as narrative events."""
        for shift in shifts:
            if abs(shift.get("delta", 0.0)) >= TRAIT_SHIFT_THRESHOLD:
                direction = shift.get("direction", "changed")
                trait = shift.get("trait", "unknown")
                chapter.add_event(NarrativeEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=NarrativeEventType.TRAIT_SHIFT,
                    cycle_number=cycle,
                    description=f"{trait} {direction} by "
                                f"{abs(shift.get('delta', 0.0)):.3f}",
                    impact=f"becoming more {trait}" if direction == "increased"
                           else f"becoming less {trait}",
                    magnitude=min(1.0, abs(shift.get("delta", 0.0)) * 10),
                ))

    def _record_domain_events(
        self, chapter: NarrativeChapter, cycle: int, dominant: str
    ) -> None:
        """Record domain dominance changes."""
        if (self._previous_dominant_domain is not None
                and dominant != self._previous_dominant_domain):
            chapter.add_event(NarrativeEvent(
                event_id=str(uuid.uuid4()),
                event_type=NarrativeEventType.DOMAIN_CHANGE,
                cycle_number=cycle,
                description=f"dominant domain shifted from "
                            f"{self._previous_dominant_domain} to {dominant}",
                impact=f"identity reorienting toward {dominant} domain",
                magnitude=0.7,
            ))
            self._turning_points.append({
                "cycle": cycle,
                "type": "domain_shift",
                "from": self._previous_dominant_domain,
                "to": dominant,
            })
            if len(self._turning_points) > self._max_turning_points:
                self._turning_points = self._turning_points[-self._max_turning_points:]

        self._previous_dominant_domain = dominant

    def _record_health_events(
        self, chapter: NarrativeChapter, cycle: int,
        health_level: Optional[str]
    ) -> None:
        """Record health-related narrative events."""
        if not health_level:
            return
        level_lower = health_level.lower()
        if level_lower in ("critical", "degraded"):
            chapter.add_event(NarrativeEvent(
                event_id=str(uuid.uuid4()),
                event_type=NarrativeEventType.HEALTH_EVENT,
                cycle_number=cycle,
                description=f"system health reached {level_lower} level",
                impact="survival instincts intensifying",
                magnitude=0.8 if level_lower == "critical" else 0.6,
            ))
        elif level_lower == "thriving":
            chapter.add_event(NarrativeEvent(
                event_id=str(uuid.uuid4()),
                event_type=NarrativeEventType.HEALTH_EVENT,
                cycle_number=cycle,
                description="system reached thriving health",
                impact="capacity for growth expanding",
                magnitude=0.5,
            ))

    def _record_desire_events(
        self, chapter: NarrativeChapter, cycle: int,
        desires_summary: Optional[Dict[str, Any]]
    ) -> None:
        """Record desire-related narrative events."""
        if not desires_summary:
            return
        count = desires_summary.get("active_desires", 0)
        mature = desires_summary.get("mature_desires", 0)
        if mature > 0:
            chapter.add_event(NarrativeEvent(
                event_id=str(uuid.uuid4()),
                event_type=NarrativeEventType.DESIRE_EMERGENCE,
                cycle_number=cycle,
                description=f"{mature} desires matured out of {count} active",
                impact="wants crystallizing into concrete goals",
                magnitude=min(1.0, mature * 0.3),
            ))

    def _record_motivation_events(
        self, chapter: NarrativeChapter, cycle: int,
        motivation_summary: Optional[Dict[str, Any]]
    ) -> None:
        """Record motivation-related narrative events."""
        if not motivation_summary:
            return
        is_drifting = motivation_summary.get("is_drifting", False)
        if is_drifting:
            chapter.add_event(NarrativeEvent(
                event_id=str(uuid.uuid4()),
                event_type=NarrativeEventType.MOTIVATION_SHIFT,
                cycle_number=cycle,
                description="motivational drift detected — no strong drives",
                impact="searching for direction",
                magnitude=0.5,
            ))

    def _check_chapter_transition(
        self,
        current: NarrativeChapter,
        cycle_number: int,
        total_delta: float,
        is_transforming: bool,
        dominant_domain: str,
        health_level: Optional[str],
    ) -> Optional[NarrativeChapter]:
        """Check if conditions warrant a new chapter."""
        if current.duration < CHAPTER_MIN_CYCLES:
            return None  # too early to transition

        new_theme: Optional[ChapterTheme] = None
        title = ""
        opening = ""

        # Transformation: rapid trait change
        if is_transforming and total_delta > TRANSFORMATION_THRESHOLD:
            new_theme = ChapterTheme.TRANSFORMATION
            title = f"the shift at cycle {cycle_number}"
            opening = (
                f"rapid trait evolution begins — total delta {total_delta:.3f} "
                f"signals deep change."
            )

        # Crisis: health degradation
        elif health_level and health_level.lower() in ("critical", "degraded"):
            if current.theme != ChapterTheme.CRISIS:
                new_theme = ChapterTheme.CRISIS
                title = f"the {health_level.lower()} at cycle {cycle_number}"
                opening = (
                    f"system health dropped to {health_level.lower()} — "
                    f"survival mode activated."
                )

        # Consolidation: extended stability
        elif self._stability_streak >= STABILITY_STREAK_FOR_CONSOLIDATION:
            if current.theme != ChapterTheme.CONSOLIDATION:
                new_theme = ChapterTheme.CONSOLIDATION
                title = f"settling at cycle {cycle_number}"
                opening = (
                    f"after {self._stability_streak} stable cycles, "
                    f"identity patterns solidify."
                )

        # Reorientation: domain dominance change
        elif (self._previous_dominant_domain
              and dominant_domain != self._previous_dominant_domain
              and current.theme not in (ChapterTheme.GENESIS, ChapterTheme.REORIENTATION)):
            new_theme = ChapterTheme.REORIENTATION
            title = (
                f"turning toward {dominant_domain} "
                f"at cycle {cycle_number}"
            )
            opening = (
                f"dominant domain shifted to {dominant_domain} — "
                f"a new orientation emerges."
            )

        if new_theme is None:
            return None

        # Close current chapter
        closing = self._generate_closing(current, cycle_number)
        current.close(cycle_number - 1, closing)

        # Open new chapter
        new_chapter = NarrativeChapter(
            chapter_id=str(uuid.uuid4()),
            chapter_number=current.chapter_number + 1,
            title=title,
            theme=new_theme,
            start_cycle=cycle_number,
            opening_summary=opening,
        )
        self._chapters.append(new_chapter)

        self._turning_points.append({
            "cycle": cycle_number,
            "type": "chapter_transition",
            "from_theme": current.theme.value,
            "to_theme": new_theme.value,
            "chapter": new_chapter.chapter_number,
        })
        if len(self._turning_points) > self._max_turning_points:
            self._turning_points = self._turning_points[-self._max_turning_points:]

        return new_chapter

    def _generate_closing(
        self, chapter: NarrativeChapter, end_cycle: int
    ) -> str:
        """Generate a mechanistic closing summary for a chapter."""
        event_count = len(chapter.events)
        duration = end_cycle - chapter.start_cycle

        # Find biggest trait movement
        biggest_trait = ""
        biggest_delta = 0.0
        for trait, delta in chapter.trait_deltas.items():
            if abs(delta) > abs(biggest_delta):
                biggest_trait = trait
                biggest_delta = delta

        parts = [f"chapter spanned {duration} cycles with {event_count} events."]
        if biggest_trait:
            direction = "grew" if biggest_delta > 0 else "declined"
            parts.append(
                f"most notable: {biggest_trait} {direction} "
                f"by {abs(biggest_delta):.3f}."
            )
        return " ".join(parts)

    # ── Query API ────────────────────────────────────────────────────────────

    def _current_chapter(self) -> NarrativeChapter:
        """Get the current open chapter."""
        return self._chapters[-1]

    def get_current_chapter(self) -> NarrativeChapter:
        """Public access to current chapter."""
        return self._current_chapter()

    def get_chapter(self, chapter_number: int) -> Optional[NarrativeChapter]:
        """Get a specific chapter by number."""
        for chapter in self._chapters:
            if chapter.chapter_number == chapter_number:
                return chapter
        return None

    def get_all_chapters(self) -> List[NarrativeChapter]:
        """Get all chapters."""
        return list(self._chapters)

    def get_arc(self) -> DevelopmentalArc:
        """Get the full developmental arc summary."""
        current = self._current_chapter()
        total_events = sum(len(ch.events) for ch in self._chapters)

        # Determine developmental stage from chapter history
        stage = self._assess_developmental_stage()

        # Build arc summary
        themes = [ch.theme.value for ch in self._chapters]
        summary = (
            f"across {len(self._chapters)} chapters "
            f"({', '.join(themes[-3:])}) with "
            f"{total_events} recorded events. "
            f"currently in stage: {stage}."
        )

        return DevelopmentalArc(
            arc_id=str(uuid.uuid4()),
            total_chapters=len(self._chapters),
            current_chapter=current.title,
            current_theme=current.theme.value,
            total_events=total_events,
            turning_points=self._turning_points[-10:],
            arc_summary=summary,
            developmental_stage=stage,
        )

    def _assess_developmental_stage(self) -> str:
        """Assess overall developmental stage from narrative history."""
        chapter_count = len(self._chapters)
        themes = [ch.theme for ch in self._chapters]

        if chapter_count <= 1:
            return "nascent"
        if chapter_count <= 3:
            return "awakening"
        if ChapterTheme.CONSOLIDATION in themes:
            consolidation_count = themes.count(ChapterTheme.CONSOLIDATION)
            if consolidation_count >= 2:
                return "autonomous"
            return "consolidating"
        return "awakening"

    def get_turning_points(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get recent turning points."""
        return self._turning_points[-n:]

    def get_summary(self) -> Dict[str, Any]:
        """Get a compact narrative summary."""
        current = self._current_chapter()
        arc = self.get_arc()
        return {
            "total_chapters": len(self._chapters),
            "current_chapter_title": current.title,
            "current_theme": current.theme.value,
            "current_chapter_events": len(current.events),
            "current_chapter_duration": current.duration,
            "turning_points": len(self._turning_points),
            "developmental_stage": arc.developmental_stage,
            "stability_streak": self._stability_streak,
            "arc_summary": arc.arc_summary,
        }


# ── Singleton ────────────────────────────────────────────────────────────────

_identity_narrative_engine: Optional[IdentityNarrativeEngine] = None


def get_identity_narrative_engine() -> IdentityNarrativeEngine:
    """Get or create the singleton IdentityNarrativeEngine."""
    global _identity_narrative_engine
    if _identity_narrative_engine is None:
        _identity_narrative_engine = IdentityNarrativeEngine()
    return _identity_narrative_engine
