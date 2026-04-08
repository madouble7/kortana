"""
V29 — Self-Model & Identity Persistence — Test Suite

Tests for:
  V29A: SelfPortraitEngine — structured trait profile
  V29B: IdentityNarrativeEngine — developmental story
  V29C: TraitEvolutionEngine — trait trajectory tracking
  V29D: ContinuityAnchorEngine — identity persistence
  Pipeline: V27 experience → V28 desire → V29 identity flow
"""

from src.kortana.services.continuity_anchor import (
    AnchorStrength,
    ContinuityAnchorEngine,
    DriftSeverity,
    get_continuity_anchor_engine,
)
from src.kortana.services.identity_narrative import (
    ChapterTheme,
    IdentityNarrativeEngine,
    NarrativeEventType,
    get_identity_narrative_engine,
)
from src.kortana.services.self_portrait import (
    DEFAULT_TRAIT_SCORES,
    SelfPortraitEngine,
    TraitName,
    get_self_portrait_engine,
)
from src.kortana.services.trait_evolution import (
    TraitEvolutionEngine,
    TraitStatus,
    get_trait_evolution_engine,
)

# ── V29A: SelfPortraitEngine Tests ──────────────────────────────────────────


class TestSelfPortraitEngine:
    """Tests for the structured self-model."""

    def _make(self) -> SelfPortraitEngine:
        return SelfPortraitEngine()

    def test_initial_traits(self):
        engine = self._make()
        scores = engine.get_trait_scores()
        assert len(scores) == 15
        assert scores["empathy"] == 0.7
        assert scores["curiosity"] == 0.6

    def test_assess_no_inputs(self):
        engine = self._make()
        portrait = engine.assess(cycle_number=1)
        assert portrait.cycle_number == 1
        assert portrait.portrait_id
        assert portrait.total_delta == 0.0  # no inputs → no change

    def test_assess_with_lessons(self):
        engine = self._make()
        lessons = [
            {"lesson_type": "success", "severity": "significant"},
            {"lesson_type": "failure", "severity": "moderate"},
        ]
        portrait = engine.assess(cycle_number=1, lessons=lessons)
        assert portrait.total_delta > 0.0
        assert len(portrait.significant_shifts) > 0

    def test_assess_with_desires(self):
        engine = self._make()
        desires = [
            {"source": "autonomy_drive", "intensity": 0.8},
            {"source": "learning_stagnation", "intensity": 0.5},
        ]
        engine.assess(cycle_number=1, desires=desires)
        # Autonomy drive should boost decisiveness and purpose_clarity
        scores = engine.get_trait_scores()
        assert scores["decisiveness"] > DEFAULT_TRAIT_SCORES[TraitName.DECISIVENESS]

    def test_weak_desires_ignored(self):
        engine = self._make()
        desires = [{"source": "autonomy_drive", "intensity": 0.1}]
        engine.assess(cycle_number=1, desires=desires)
        scores = engine.get_trait_scores()
        # Intensity < 0.3 should be ignored
        assert scores["decisiveness"] == round(
            DEFAULT_TRAIT_SCORES[TraitName.DECISIVENESS], 4
        )

    def test_assess_with_motivation(self):
        engine = self._make()
        motivation = {"dominant_dimension": "growth", "overall_drive": 0.7}
        engine.assess(cycle_number=1, motivation_snapshot=motivation)
        # Growth → cognitive domain boost
        scores = engine.get_trait_scores()
        assert scores["curiosity"] >= DEFAULT_TRAIT_SCORES[TraitName.CURIOSITY]

    def test_motivation_low_drive_ignored(self):
        engine = self._make()
        motivation = {"dominant_dimension": "growth", "overall_drive": 0.1}
        engine.assess(cycle_number=1, motivation_snapshot=motivation)
        scores = engine.get_trait_scores()
        assert scores["curiosity"] == round(
            DEFAULT_TRAIT_SCORES[TraitName.CURIOSITY], 4
        )

    def test_assess_with_health(self):
        engine = self._make()
        health = {
            "dimensions": {
                "learning": {"score": 90.0},
                "continuity": {"score": 20.0},
            }
        }
        engine.assess(cycle_number=1, health_snapshot=health)
        scores = engine.get_trait_scores()
        # Learning high → slight curiosity boost
        # Continuity low → resilience penalty
        assert scores["curiosity"] >= round(
            DEFAULT_TRAIT_SCORES[TraitName.CURIOSITY], 4
        )

    def test_trait_clamping(self):
        engine = self._make()
        # Many success lessons to push decisiveness high
        lessons = [{"lesson_type": "success", "severity": "critical"}] * 20
        engine.assess(cycle_number=1, lessons=lessons)
        scores = engine.get_trait_scores()
        assert scores["decisiveness"] <= 0.98  # ceiling

    def test_get_trait(self):
        engine = self._make()
        assert engine.get_trait("empathy") == 0.7
        assert engine.get_trait("nonexistent") is None

    def test_get_domain_average(self):
        engine = self._make()
        avg = engine.get_domain_average("emotional")
        assert avg is not None
        expected = (0.7 + 0.5 + 0.6) / 3  # empathy, resilience, patience
        assert abs(avg - expected) < 0.001

    def test_get_domain_invalid(self):
        engine = self._make()
        assert engine.get_domain_average("nonexistent") is None

    def test_portrait_history(self):
        engine = self._make()
        engine.assess(cycle_number=1)
        engine.assess(cycle_number=2)
        engine.assess(cycle_number=3)
        history = engine.get_history(2)
        assert len(history) == 2
        assert history[0].cycle_number == 3

    def test_portrait_to_dict(self):
        engine = self._make()
        portrait = engine.assess(cycle_number=1)
        d = portrait.to_dict()
        assert "portrait_id" in d
        assert "traits" in d
        assert "domain_averages" in d
        assert "is_stable" in d

    def test_portrait_stability(self):
        engine = self._make()
        portrait = engine.assess(cycle_number=1)
        assert portrait.is_stable  # no change

    def test_summary(self):
        engine = self._make()
        engine.assess(cycle_number=1)
        summary = engine.get_summary()
        assert summary["trait_count"] == 15
        assert summary["portraits_captured"] == 1

    def test_singleton(self):
        # Reset singleton for test isolation
        import src.kortana.services.self_portrait as mod
        mod._self_portrait_engine = None
        e1 = get_self_portrait_engine()
        e2 = get_self_portrait_engine()
        assert e1 is e2
        mod._self_portrait_engine = None

    def test_lesson_severity_weights(self):
        self._make()
        # Critical lessons have higher impact than trivial
        lessons_critical = [{"lesson_type": "insight", "severity": "critical"}]
        lessons_trivial = [{"lesson_type": "insight", "severity": "trivial"}]

        engine1 = self._make()
        engine1.assess(cycle_number=1, lessons=lessons_critical)
        score_critical = engine1.get_trait("analytical")

        engine2 = self._make()
        engine2.assess(cycle_number=1, lessons=lessons_trivial)
        score_trivial = engine2.get_trait("analytical")

        assert score_critical > score_trivial

    def test_multiple_cycles_accumulate(self):
        engine = self._make()
        lessons = [{"lesson_type": "success", "severity": "moderate"}]
        engine.assess(cycle_number=1, lessons=lessons)
        score_1 = engine.get_trait("decisiveness")
        engine.assess(cycle_number=2, lessons=lessons)
        score_2 = engine.get_trait("decisiveness")
        assert score_2 > score_1


# ── V29B: IdentityNarrativeEngine Tests ─────────────────────────────────────


class TestIdentityNarrativeEngine:
    """Tests for the developmental narrative."""

    def _make(self) -> IdentityNarrativeEngine:
        return IdentityNarrativeEngine()

    def test_genesis_chapter(self):
        engine = self._make()
        current = engine.get_current_chapter()
        assert current.theme == ChapterTheme.GENESIS
        assert current.chapter_number == 1
        assert current.is_open

    def test_process_stable_cycle(self):
        engine = self._make()
        portrait_data = {
            "total_delta": 0.01,
            "significant_shifts": [],
            "dominant_domain": "cognitive",
            "is_transforming": False,
        }
        chapter = engine.process_cycle(cycle_number=1, portrait_data=portrait_data)
        assert chapter.chapter_number == 1  # still in genesis

    def test_trait_shift_event(self):
        engine = self._make()
        portrait_data = {
            "total_delta": 0.1,
            "significant_shifts": [
                {"trait": "curiosity", "delta": 0.06, "direction": "increased"}
            ],
            "dominant_domain": "cognitive",
            "is_transforming": False,
        }
        engine.process_cycle(cycle_number=1, portrait_data=portrait_data)
        current = engine.get_current_chapter()
        assert len(current.events) >= 1
        assert current.events[0].event_type == NarrativeEventType.TRAIT_SHIFT

    def test_domain_change_event(self):
        engine = self._make()
        # First cycle sets domain
        engine.process_cycle(cycle_number=1, portrait_data={
            "total_delta": 0.01, "significant_shifts": [],
            "dominant_domain": "cognitive", "is_transforming": False,
        })
        # Second cycle changes domain
        engine.process_cycle(cycle_number=2, portrait_data={
            "total_delta": 0.01, "significant_shifts": [],
            "dominant_domain": "emotional", "is_transforming": False,
        })
        current = engine.get_current_chapter()
        domain_events = [
            e for e in current.events
            if e.event_type == NarrativeEventType.DOMAIN_CHANGE
        ]
        assert len(domain_events) == 1

    def test_health_crisis_event(self):
        engine = self._make()
        engine.process_cycle(
            cycle_number=1,
            portrait_data={
                "total_delta": 0.01, "significant_shifts": [],
                "dominant_domain": "cognitive", "is_transforming": False,
            },
            health_level="critical",
        )
        current = engine.get_current_chapter()
        health_events = [
            e for e in current.events
            if e.event_type == NarrativeEventType.HEALTH_EVENT
        ]
        assert len(health_events) == 1

    def test_desire_emergence_event(self):
        engine = self._make()
        engine.process_cycle(
            cycle_number=1,
            portrait_data={
                "total_delta": 0.01, "significant_shifts": [],
                "dominant_domain": "cognitive", "is_transforming": False,
            },
            desires_summary={"active_desires": 5, "mature_desires": 2},
        )
        current = engine.get_current_chapter()
        desire_events = [
            e for e in current.events
            if e.event_type == NarrativeEventType.DESIRE_EMERGENCE
        ]
        assert len(desire_events) == 1

    def test_chapter_transition_transformation(self):
        engine = self._make()
        # Need CHAPTER_MIN_CYCLES first
        for i in range(6):
            engine.process_cycle(
                cycle_number=i,
                portrait_data={
                    "total_delta": 0.01, "significant_shifts": [],
                    "dominant_domain": "cognitive", "is_transforming": False,
                },
            )
        # Now trigger transformation
        chapter = engine.process_cycle(
            cycle_number=6,
            portrait_data={
                "total_delta": 0.25,
                "significant_shifts": [],
                "dominant_domain": "cognitive",
                "is_transforming": True,
            },
        )
        assert chapter.theme == ChapterTheme.TRANSFORMATION
        assert chapter.chapter_number == 2

    def test_no_transition_before_min_cycles(self):
        engine = self._make()
        # Only 2 cycles, then try transformation
        engine.process_cycle(cycle_number=1, portrait_data={
            "total_delta": 0.01, "significant_shifts": [],
            "dominant_domain": "cognitive", "is_transforming": False,
        })
        chapter = engine.process_cycle(cycle_number=2, portrait_data={
            "total_delta": 0.25, "significant_shifts": [],
            "dominant_domain": "cognitive", "is_transforming": True,
        })
        assert chapter.chapter_number == 1  # still in genesis

    def test_get_chapter_by_number(self):
        engine = self._make()
        ch = engine.get_chapter(1)
        assert ch is not None
        assert ch.theme == ChapterTheme.GENESIS

    def test_get_chapter_not_found(self):
        engine = self._make()
        assert engine.get_chapter(99) is None

    def test_get_all_chapters(self):
        engine = self._make()
        chapters = engine.get_all_chapters()
        assert len(chapters) == 1

    def test_developmental_arc(self):
        engine = self._make()
        arc = engine.get_arc()
        assert arc.developmental_stage == "nascent"
        assert arc.total_chapters == 1

    def test_chapter_to_dict(self):
        engine = self._make()
        d = engine.get_current_chapter().to_dict()
        assert "chapter_id" in d
        assert "theme" in d
        assert "is_open" in d

    def test_arc_to_dict(self):
        engine = self._make()
        d = engine.get_arc().to_dict()
        assert "arc_summary" in d
        assert "developmental_stage" in d

    def test_turning_points(self):
        engine = self._make()
        pts = engine.get_turning_points()
        assert isinstance(pts, list)

    def test_summary(self):
        engine = self._make()
        summary = engine.get_summary()
        assert "total_chapters" in summary
        assert "developmental_stage" in summary
        assert "stability_streak" in summary

    def test_singleton(self):
        import src.kortana.services.identity_narrative as mod
        mod._identity_narrative_engine = None
        e1 = get_identity_narrative_engine()
        e2 = get_identity_narrative_engine()
        assert e1 is e2
        mod._identity_narrative_engine = None

    def test_motivation_drift_event(self):
        engine = self._make()
        engine.process_cycle(
            cycle_number=1,
            portrait_data={
                "total_delta": 0.01, "significant_shifts": [],
                "dominant_domain": "cognitive", "is_transforming": False,
            },
            motivation_summary={"is_drifting": True},
        )
        current = engine.get_current_chapter()
        drift_events = [
            e for e in current.events
            if e.event_type == NarrativeEventType.MOTIVATION_SHIFT
        ]
        assert len(drift_events) == 1

    def test_trait_deltas_accumulate(self):
        engine = self._make()
        engine.process_cycle(cycle_number=1, portrait_data={
            "total_delta": 0.1,
            "significant_shifts": [
                {"trait": "curiosity", "delta": 0.06, "direction": "increased"}
            ],
            "dominant_domain": "cognitive", "is_transforming": False,
        })
        engine.process_cycle(cycle_number=2, portrait_data={
            "total_delta": 0.1,
            "significant_shifts": [
                {"trait": "curiosity", "delta": 0.04, "direction": "increased"}
            ],
            "dominant_domain": "cognitive", "is_transforming": False,
        })
        current = engine.get_current_chapter()
        assert abs(current.trait_deltas.get("curiosity", 0) - 0.10) < 0.001


# ── V29C: TraitEvolutionEngine Tests ────────────────────────────────────────


class TestTraitEvolutionEngine:
    """Tests for trait trajectory tracking."""

    def _make(self) -> TraitEvolutionEngine:
        return TraitEvolutionEngine()

    def test_record_cycle(self):
        engine = self._make()
        scores = {"curiosity": 0.65, "empathy": 0.72}
        snapshot = engine.record_cycle(cycle_number=1, trait_scores=scores)
        assert snapshot.cycle_number == 1
        assert "curiosity" in snapshot.trajectories

    def test_trajectory_created(self):
        engine = self._make()
        engine.record_cycle(cycle_number=1, trait_scores={"curiosity": 0.65})
        traj = engine.get_trajectory("curiosity")
        assert traj is not None
        assert traj.current_score == 0.65

    def test_velocity_computation(self):
        engine = self._make()
        # Steadily increasing scores
        for i in range(10):
            engine.record_cycle(
                cycle_number=i,
                trait_scores={"curiosity": 0.5 + i * 0.02},
                previous_scores={"curiosity": 0.5 + max(0, i - 1) * 0.02},
            )
        traj = engine.get_trajectory("curiosity")
        assert traj.velocity > 0  # should be positive (increasing)

    def test_stability_high_for_constant(self):
        engine = self._make()
        for i in range(20):
            engine.record_cycle(
                cycle_number=i, trait_scores={"curiosity": 0.5}
            )
        traj = engine.get_trajectory("curiosity")
        assert traj.stability > 0.9

    def test_stability_low_for_volatile(self):
        engine = self._make()
        import random
        random.seed(42)
        for i in range(20):
            engine.record_cycle(
                cycle_number=i,
                trait_scores={"curiosity": random.uniform(0.2, 0.8)},
            )
        traj = engine.get_trajectory("curiosity")
        assert traj.stability < 0.5

    def test_crystallization(self):
        engine = self._make()
        # 20 cycles of constant score → should crystallize
        for i in range(20):
            engine.record_cycle(
                cycle_number=i, trait_scores={"patience": 0.7}
            )
        traj = engine.get_trajectory("patience")
        assert traj.status == TraitStatus.CRYSTALLIZED
        assert traj.is_crystallized
        assert traj.crystallized_at is not None

    def test_dormant_detection(self):
        engine = self._make()
        for i in range(20):
            engine.record_cycle(
                cycle_number=i, trait_scores={"creativity": 0.1}
            )
        traj = engine.get_trajectory("creativity")
        assert traj.status == TraitStatus.DORMANT

    def test_record_event(self):
        engine = self._make()
        engine.record_cycle(cycle_number=1, trait_scores={"curiosity": 0.5})
        event = engine.record_event(
            "curiosity", cycle_number=1,
            old_score=0.5, new_score=0.55,
            source="lesson:insight",
        )
        assert event is not None
        assert abs(event.delta - 0.05) < 0.001

    def test_record_event_insignificant(self):
        engine = self._make()
        engine.record_cycle(cycle_number=1, trait_scores={"curiosity": 0.5})
        event = engine.record_event(
            "curiosity", cycle_number=1,
            old_score=0.5, new_score=0.5005,
            source="minor",
        )
        assert event is None

    def test_get_crystallized(self):
        engine = self._make()
        for i in range(20):
            engine.record_cycle(
                cycle_number=i, trait_scores={"patience": 0.7, "curiosity": 0.5}
            )
        crystallized = engine.get_crystallized()
        assert "patience" in crystallized

    def test_get_drifting(self):
        engine = self._make()
        for i in range(10):
            engine.record_cycle(
                cycle_number=i,
                trait_scores={"curiosity": 0.5 + i * 0.03},
                previous_scores={"curiosity": 0.5 + max(0, i - 1) * 0.03},
            )
        drifting = engine.get_drifting()
        assert "curiosity" in drifting

    def test_snapshot_to_dict(self):
        engine = self._make()
        snapshot = engine.record_cycle(
            cycle_number=1, trait_scores={"curiosity": 0.6}
        )
        d = snapshot.to_dict()
        assert "crystallized_traits" in d
        assert "overall_stability" in d

    def test_trajectory_to_dict(self):
        engine = self._make()
        engine.record_cycle(cycle_number=1, trait_scores={"curiosity": 0.6})
        traj = engine.get_trajectory("curiosity")
        d = traj.to_dict()
        assert "velocity" in d
        assert "stability" in d
        assert "trend" in d

    def test_trait_history(self):
        engine = self._make()
        for i in range(5):
            engine.record_cycle(
                cycle_number=i, trait_scores={"curiosity": 0.5 + i * 0.01}
            )
        history = engine.get_trait_history("curiosity")
        assert len(history) == 5

    def test_summary(self):
        engine = self._make()
        engine.record_cycle(cycle_number=1, trait_scores={"curiosity": 0.6})
        summary = engine.get_summary()
        assert "traits_tracked" in summary
        assert summary["traits_tracked"] == 1

    def test_singleton(self):
        import src.kortana.services.trait_evolution as mod
        mod._trait_evolution_engine = None
        e1 = get_trait_evolution_engine()
        e2 = get_trait_evolution_engine()
        assert e1 is e2
        mod._trait_evolution_engine = None

    def test_trend_stable(self):
        engine = self._make()
        for i in range(10):
            engine.record_cycle(
                cycle_number=i, trait_scores={"patience": 0.5}
            )
        traj = engine.get_trajectory("patience")
        assert traj.trend == "stable"

    def test_event_to_dict(self):
        engine = self._make()
        engine.record_cycle(cycle_number=1, trait_scores={"curiosity": 0.5})
        event = engine.record_event(
            "curiosity", 1, 0.5, 0.55, "test_source"
        )
        d = event.to_dict()
        assert d["source"] == "test_source"
        assert d["delta"] == 0.05


# ── V29D: ContinuityAnchorEngine Tests ──────────────────────────────────────


class TestContinuityAnchorEngine:
    """Tests for identity persistence."""

    def _make(self) -> ContinuityAnchorEngine:
        return ContinuityAnchorEngine()

    def test_foundational_anchors(self):
        engine = self._make()
        foundational = engine.get_foundational()
        assert len(foundational) == 4
        names = [a.trait_name for a in foundational]
        assert "empathy" in names
        assert "purpose_clarity" in names

    def test_anchor_trait(self):
        engine = self._make()
        anchor = engine.anchor_trait("curiosity", 0.65, cycle_number=1)
        assert anchor.trait_name == "curiosity"
        assert anchor.anchored_value == 0.65
        assert anchor.strength == AnchorStrength.STRONG

    def test_anchor_no_override_foundational(self):
        engine = self._make()
        anchor = engine.anchor_trait(
            "empathy", 0.9, cycle_number=1, strength=AnchorStrength.STRONG
        )
        assert anchor.strength == AnchorStrength.FOUNDATIONAL

    def test_verify_stable(self):
        engine = self._make()
        # Verify with matching scores
        scores = {
            "empathy": 0.7,
            "purpose_clarity": 0.5,
            "coherence_seeking": 0.6,
            "growth_orientation": 0.6,
        }
        report = engine.verify(cycle_number=1, trait_scores=scores)
        assert report.identity_verified
        assert report.drift_severity == DriftSeverity.NONE
        assert report.coherence_score > 0.9

    def test_verify_drift(self):
        engine = self._make()
        # Verify with deviated scores
        scores = {
            "empathy": 0.2,  # big drift from 0.7
            "purpose_clarity": 0.1,
            "coherence_seeking": 0.1,
            "growth_orientation": 0.1,
        }
        report = engine.verify(cycle_number=1, trait_scores=scores)
        assert report.drift_magnitude > 0.2
        assert report.drift_severity in (
            DriftSeverity.SIGNIFICANT, DriftSeverity.CRITICAL
        )

    def test_verify_drifting_traits(self):
        engine = self._make()
        scores = {
            "empathy": 0.2,
            "purpose_clarity": 0.5,
            "coherence_seeking": 0.6,
            "growth_orientation": 0.6,
        }
        report = engine.verify(cycle_number=1, trait_scores=scores)
        assert "empathy" in report.drifting_traits

    def test_anchor_crystallized(self):
        engine = self._make()
        anchored = engine.anchor_crystallized(
            crystallized_traits=["curiosity", "patience"],
            trait_scores={"curiosity": 0.7, "patience": 0.6},
            cycle_number=5,
        )
        assert len(anchored) == 2

    def test_anchor_update_tracks_slowly(self):
        engine = self._make()
        engine.anchor_trait(
            "curiosity", 0.5, cycle_number=1, strength=AnchorStrength.STRONG
        )
        # Verify with higher value
        engine.verify(cycle_number=2, trait_scores={"curiosity": 0.8})
        # Anchored value should have moved slightly toward 0.8
        updated = engine.get_anchor("curiosity")
        assert updated.anchored_value > 0.5

    def test_foundational_doesnt_track(self):
        engine = self._make()
        original = engine.get_anchor("empathy").anchored_value
        engine.verify(cycle_number=1, trait_scores={"empathy": 0.9})
        # Foundational should NOT track
        assert engine.get_anchor("empathy").anchored_value == original

    def test_coherence_property(self):
        engine = self._make()
        assert engine.coherence == 1.0  # before any verification

    def test_identity_verified_property(self):
        engine = self._make()
        assert engine.is_identity_verified  # before any verification

    def test_drift_severity_property(self):
        engine = self._make()
        assert engine.drift_severity == "none"

    def test_get_all_anchors(self):
        engine = self._make()
        anchors = engine.get_all_anchors()
        assert len(anchors) == 4  # foundational only initially

    def test_coherence_history(self):
        engine = self._make()
        scores = {"empathy": 0.7, "purpose_clarity": 0.5,
                  "coherence_seeking": 0.6, "growth_orientation": 0.6}
        engine.verify(cycle_number=1, trait_scores=scores)
        engine.verify(cycle_number=2, trait_scores=scores)
        history = engine.get_coherence_history()
        assert len(history) == 2

    def test_report_to_dict(self):
        engine = self._make()
        scores = {"empathy": 0.7, "purpose_clarity": 0.5,
                  "coherence_seeking": 0.6, "growth_orientation": 0.6}
        report = engine.verify(cycle_number=1, trait_scores=scores)
        d = report.to_dict()
        assert "coherence_score" in d
        assert "drift_severity" in d
        assert "identity_verified" in d

    def test_summary(self):
        engine = self._make()
        summary = engine.get_summary()
        assert "anchor_count" in summary
        assert "foundational_count" in summary
        assert summary["foundational_count"] == 4

    def test_singleton(self):
        import src.kortana.services.continuity_anchor as mod
        mod._continuity_anchor_engine = None
        e1 = get_continuity_anchor_engine()
        e2 = get_continuity_anchor_engine()
        assert e1 is e2
        mod._continuity_anchor_engine = None

    def test_prune_weakest(self):
        engine = self._make()
        # Add many anchors to exceed MAX_ANCHORS
        for i in range(25):
            engine.anchor_trait(
                f"trait_{i}", 0.5, cycle_number=1,
                strength=AnchorStrength.TENTATIVE,
            )
        # Should have pruned to MAX_ANCHORS
        all_anchors = engine.get_all_anchors()
        assert len(all_anchors) <= 20

    def test_is_coherent_property(self):
        engine = self._make()
        scores = {"empathy": 0.7, "purpose_clarity": 0.5,
                  "coherence_seeking": 0.6, "growth_orientation": 0.6}
        report = engine.verify(cycle_number=1, trait_scores=scores)
        assert report.is_coherent

    def test_is_not_in_crisis(self):
        engine = self._make()
        scores = {"empathy": 0.7, "purpose_clarity": 0.5,
                  "coherence_seeking": 0.6, "growth_orientation": 0.6}
        report = engine.verify(cycle_number=1, trait_scores=scores)
        assert not report.is_in_crisis


# ── V29 Pipeline Tests ──────────────────────────────────────────────────────


class TestV29Pipeline:
    """Integration tests: V27 experience → V28 desire → V29 identity."""

    def test_full_identity_cycle(self):
        """Test complete: portrait → narrative → evolution → continuity."""
        portrait_engine = SelfPortraitEngine()
        narrative_engine = IdentityNarrativeEngine()
        evolution_engine = TraitEvolutionEngine()
        anchor_engine = ContinuityAnchorEngine()

        # 1. Assess portrait with V27+V28 inputs
        portrait = portrait_engine.assess(
            cycle_number=1,
            lessons=[{"lesson_type": "insight", "severity": "significant"}],
            desires=[{"source": "autonomy_drive", "intensity": 0.7}],
            motivation_snapshot={"dominant_dimension": "growth", "overall_drive": 0.6},
            health_snapshot={"dimensions": {"learning": {"score": 80.0}}},
        )

        # 2. Process narrative
        chapter = narrative_engine.process_cycle(
            cycle_number=1,
            portrait_data=portrait.to_dict(),
        )
        assert chapter.chapter_number == 1

        # 3. Record trait evolution
        snapshot = evolution_engine.record_cycle(
            cycle_number=1,
            trait_scores=portrait_engine.get_trait_scores(),
        )
        assert snapshot.cycle_number == 1

        # 4. Verify continuity
        report = anchor_engine.verify(
            cycle_number=1,
            trait_scores=portrait_engine.get_trait_scores(),
        )
        assert report.identity_verified

    def test_crystallization_to_anchor(self):
        """Test: stable traits crystallize (V29C) → anchored (V29D)."""
        evolution_engine = TraitEvolutionEngine()
        anchor_engine = ContinuityAnchorEngine()

        # 20 cycles of stability → crystallization
        for i in range(20):
            evolution_engine.record_cycle(
                cycle_number=i,
                trait_scores={"patience": 0.7, "curiosity": 0.6},
            )

        crystallized = evolution_engine.get_crystallized()
        assert len(crystallized) > 0

        # Anchor crystallized traits
        scores = {"patience": 0.7, "curiosity": 0.6}
        anchored = anchor_engine.anchor_crystallized(
            crystallized_traits=crystallized,
            trait_scores=scores,
            cycle_number=20,
        )
        assert len(anchored) >= 1

    def test_drift_triggers_narrative(self):
        """Test: identity drift creates narrative events."""
        narrative_engine = IdentityNarrativeEngine()

        # Simulate domain change (turns into narrative event)
        narrative_engine.process_cycle(cycle_number=1, portrait_data={
            "total_delta": 0.01, "significant_shifts": [],
            "dominant_domain": "cognitive", "is_transforming": False,
        })
        narrative_engine.process_cycle(cycle_number=2, portrait_data={
            "total_delta": 0.01, "significant_shifts": [],
            "dominant_domain": "existential", "is_transforming": False,
        })

        current = narrative_engine.get_current_chapter()
        domain_events = [
            e for e in current.events
            if e.event_type == NarrativeEventType.DOMAIN_CHANGE
        ]
        assert len(domain_events) == 1

    def test_identity_pulse_integration(self):
        """Test all four V29 components produce summaries."""
        portrait_engine = SelfPortraitEngine()
        narrative_engine = IdentityNarrativeEngine()
        evolution_engine = TraitEvolutionEngine()
        anchor_engine = ContinuityAnchorEngine()

        # Run one cycle through everything
        portrait = portrait_engine.assess(cycle_number=1)
        narrative_engine.process_cycle(
            cycle_number=1, portrait_data=portrait.to_dict()
        )
        evolution_engine.record_cycle(
            cycle_number=1,
            trait_scores=portrait_engine.get_trait_scores(),
        )
        anchor_engine.verify(
            cycle_number=1,
            trait_scores=portrait_engine.get_trait_scores(),
        )

        # All summaries should work
        assert "trait_count" in portrait_engine.get_summary()
        assert "total_chapters" in narrative_engine.get_summary()
        assert "traits_tracked" in evolution_engine.get_summary()
        assert "anchor_count" in anchor_engine.get_summary()

    def test_v28_to_v29_bridge(self):
        """Test V28 desire/motivation data flows into V29 portrait."""
        engine = SelfPortraitEngine()

        # V28 desire data
        desires = [
            {"source": "health_deficit", "intensity": 0.8},
            {"source": "learning_stagnation", "intensity": 0.6},
        ]
        # V28 motivation data
        motivation = {
            "dominant_dimension": "survival",
            "overall_drive": 0.7,
        }

        engine.assess(
            cycle_number=1,
            desires=desires,
            motivation_snapshot=motivation,
        )

        # Health deficit → caution and protectiveness boosted
        scores = engine.get_trait_scores()
        assert scores["caution"] > DEFAULT_TRAIT_SCORES[TraitName.CAUTION]
        assert scores["protectiveness"] > DEFAULT_TRAIT_SCORES[TraitName.PROTECTIVENESS]

    def test_multi_cycle_narrative_arc(self):
        """Test narrative arc builds across multiple cycles."""
        portrait_engine = SelfPortraitEngine()
        narrative_engine = IdentityNarrativeEngine()

        for i in range(3):
            portrait = portrait_engine.assess(
                cycle_number=i,
                lessons=[{"lesson_type": "insight", "severity": "moderate"}],
            )
            narrative_engine.process_cycle(
                cycle_number=i,
                portrait_data=portrait.to_dict(),
            )

        arc = narrative_engine.get_arc()
        assert arc.total_events >= 0
        assert arc.developmental_stage in (
            "nascent", "awakening", "consolidating", "autonomous"
        )
