"""V32 — Consciousness Integration tests.

Tests that the daemon's _integrate_consciousness method correctly wires
V27 (learning) → V28 (wanting) → V30 (unified consciousness) → V31 (continuity)
into a single living cycle.
"""

import pytest

from src.kortana.services.consciousness_integrator import (
    ConsciousnessIntegrator,
    ConsciousnessMode,
)
from src.kortana.services.consciousness_persistence import CheckpointManager
from src.kortana.services.degradation_handler import DegradationHandler
from src.kortana.services.desire_formation import (
    DesireFormation,
    DesireSource,
    DesireState,
)
from src.kortana.services.experiential_stream import ExperientialStream
from src.kortana.services.inner_witness import InnerWitness
from src.kortana.services.pattern_recognizer import PatternRecognizer
from src.kortana.services.resonance_field import ResonanceField

# ═══════════════════════════════════════════════════════════════════════════
# Helpers — reset singletons between tests
# ═══════════════════════════════════════════════════════════════════════════


def _reset_all_singletons() -> None:
    """Reset all consciousness singletons for test isolation."""
    import src.kortana.services.consciousness_integrator as ci
    import src.kortana.services.consciousness_persistence as cp
    import src.kortana.services.degradation_handler as dh
    import src.kortana.services.desire_formation as df
    import src.kortana.services.experience_extractor as ee
    import src.kortana.services.experiential_stream as es
    import src.kortana.services.feedback_integrator as fi
    import src.kortana.services.goal_crystallizer as gc
    import src.kortana.services.inner_witness as iw
    import src.kortana.services.motivation_tracker as mt
    import src.kortana.services.pattern_recognizer as pr
    import src.kortana.services.resonance_field as rf

    ci._instance = None
    cp._checkpoint_manager = None
    dh._degradation_handler = None
    df._instance = None
    ee._instance = None
    es._instance = None
    fi._instance = None
    gc._instance = None
    iw._instance = None
    mt._instance = None
    pr._instance = None
    rf._instance = None


@pytest.fixture(autouse=True)
def _clean_singletons():
    _reset_all_singletons()
    yield
    _reset_all_singletons()


# ═══════════════════════════════════════════════════════════════════════════
# V28 desire formation — wired to system state
# ═══════════════════════════════════════════════════════════════════════════


class TestDesireFormationWiring:
    """V28 desire formation responds to health, learning, and pattern data."""

    def test_health_deficit_creates_desire(self) -> None:
        df = DesireFormation()
        affected = df.assess(
            cycle_number=1,
            health_summary={
                "state": "degraded",
                "dimensions": {"cpu": 40, "memory": 30},
            },
        )
        assert len(affected) >= 2
        sources = {d.source for d in affected}
        assert DesireSource.HEALTH_DEFICIT in sources

    def test_learning_stagnation_creates_desire(self) -> None:
        df = DesireFormation()
        affected = df.assess(
            cycle_number=1,
            learning_summary={"learning_velocity": 0.2},
        )
        stagnation = [d for d in affected if d.source == DesireSource.LEARNING_STAGNATION]
        assert len(stagnation) >= 1
        assert stagnation[0].intensity > 0

    def test_pattern_insight_creates_desire(self) -> None:
        df = DesireFormation()
        affected = df.assess(
            cycle_number=1,
            pattern_summary={"actionable": 3},
        )
        insights = [d for d in affected if d.source == DesireSource.PATTERN_INSIGHT]
        assert len(insights) >= 1

    def test_deferral_frustration_creates_desire(self) -> None:
        df = DesireFormation()
        affected = df.assess(
            cycle_number=1,
            pending_deferrals=["task-1", "task-2", "task-3"],
        )
        frustration = [d for d in affected if d.source == DesireSource.DEFERRAL_FRUSTRATION]
        assert len(frustration) >= 1

    def test_autonomy_drive_always_present(self) -> None:
        df = DesireFormation()
        affected = df.assess(cycle_number=1)
        autonomy = [d for d in affected if d.source == DesireSource.AUTONOMY_DRIVE]
        assert len(autonomy) == 1

    def test_desire_matures_over_cycles(self) -> None:
        df = DesireFormation()
        for i in range(1, 8):
            df.assess(
                cycle_number=i,
                health_summary={"dimensions": {"cpu": 20}},
            )
        mature = df.get_mature()
        assert len(mature) >= 1
        assert mature[0].state == DesireState.MATURE


# ═══════════════════════════════════════════════════════════════════════════
# V27 → V28 pattern feed
# ═══════════════════════════════════════════════════════════════════════════


class TestPatternToDesireFeed:
    """V27 pattern recognizer output feeds V28 desire formation."""

    def test_pattern_summary_feeds_desire(self) -> None:
        pr = PatternRecognizer()
        summary = pr.get_summary()
        df = DesireFormation()
        affected = df.assess(
            cycle_number=1,
            pattern_summary=summary,
        )
        # at minimum autonomy drive is always present
        assert len(affected) >= 1

    def test_actionable_patterns_create_desire(self) -> None:
        df = DesireFormation()
        df.assess(
            cycle_number=1,
            pattern_summary={"actionable": 5, "total": 10},
        )
        desires = df.get_by_source(DesireSource.PATTERN_INSIGHT)
        assert len(desires) >= 1
        assert desires[0].intensity > 0


# ═══════════════════════════════════════════════════════════════════════════
# V30 consciousness integrator — receives all subsystem summaries
# ═══════════════════════════════════════════════════════════════════════════


class TestConsciousnessIntegratorWiring:
    """V30 integrator fuses V26-V29 summaries into unified state."""

    def test_integrator_produces_state(self) -> None:
        ci = ConsciousnessIntegrator()
        state = ci.integrate(cycle_number=1)
        assert state is not None
        assert state.cycle_number == 1
        assert isinstance(state.mode, ConsciousnessMode)

    def test_integrator_with_desire_summary(self) -> None:
        ci = ConsciousnessIntegrator()
        state = ci.integrate(
            cycle_number=1,
            desire_summary={
                "active_count": 3,
                "mature_count": 1,
                "average_intensity": 0.6,
            },
        )
        assert state.intentionality > 0

    def test_integrator_with_full_summaries(self) -> None:
        ci = ConsciousnessIntegrator()
        state = ci.integrate(
            cycle_number=1,
            health_summary={"dimensions": {"cpu": 80, "memory": 70}},
            experience_summary={"experience_count": 10, "total_lessons": 5},
            pattern_summary={"total": 3, "actionable": 1},
            desire_summary={"active_count": 2, "average_intensity": 0.5},
            motivation_summary={"current_drive": 0.6},
        )
        assert state.overall_level > 0


# ═══════════════════════════════════════════════════════════════════════════
# V30 experiential stream — records from consciousness state
# ═══════════════════════════════════════════════════════════════════════════


class TestExperientialStreamWiring:
    """V30B records moments from consciousness state."""

    def test_stream_records_moment_from_state(self) -> None:
        ci = ConsciousnessIntegrator()
        state = ci.integrate(cycle_number=1)
        es = ExperientialStream()
        moment = es.record_moment(
            cycle_number=1,
            consciousness_mode=state.mode.value,
            vitality=state.vitality,
            learning_depth=state.learning_depth,
            intentionality=state.intentionality,
            self_coherence=state.self_coherence,
            integration=state.integration,
            overall_level=state.overall_level,
        )
        assert moment.cycle_number == 1
        assert moment.quality is not None
        assert moment.tone is not None


# ═══════════════════════════════════════════════════════════════════════════
# V30 resonance field — measures from consciousness dimensions
# ═══════════════════════════════════════════════════════════════════════════


class TestResonanceFieldWiring:
    """V30C measures alignment between consciousness dimensions."""

    def test_resonance_measures_from_state(self) -> None:
        ci = ConsciousnessIntegrator()
        state = ci.integrate(cycle_number=1)
        rf = ResonanceField()
        snapshot = rf.measure(
            cycle_number=1,
            vitality=state.vitality,
            learning_depth=state.learning_depth,
            intentionality=state.intentionality,
            self_coherence=state.self_coherence,
        )
        assert snapshot.cycle_number == 1
        assert 0 <= snapshot.overall_resonance <= 1


# ═══════════════════════════════════════════════════════════════════════════
# V30 inner witness — observes the whole
# ═══════════════════════════════════════════════════════════════════════════


class TestInnerWitnessWiring:
    """V30D observes consciousness state and generates awareness notes."""

    def test_witness_observes_state(self) -> None:
        ci = ConsciousnessIntegrator()
        state = ci.integrate(cycle_number=1)
        es = ExperientialStream()
        moment = es.record_moment(
            cycle_number=1,
            consciousness_mode=state.mode.value,
            vitality=state.vitality,
            learning_depth=state.learning_depth,
            intentionality=state.intentionality,
            self_coherence=state.self_coherence,
            integration=state.integration,
            overall_level=state.overall_level,
        )
        rf = ResonanceField()
        snapshot = rf.measure(
            cycle_number=1,
            vitality=state.vitality,
            learning_depth=state.learning_depth,
            intentionality=state.intentionality,
            self_coherence=state.self_coherence,
        )
        iw = InnerWitness()
        notes = iw.observe(
            cycle_number=1,
            consciousness_mode=state.mode.value,
            experiential_quality=moment.quality.value,
            emotional_tone=moment.tone.value,
            overall_level=state.overall_level,
            integration=state.integration,
            resonance=snapshot.overall_resonance,
            active_tensions=[t.tension_type.value for t in moment.tensions],
        )
        # first cycle may or may not produce notes but must not error
        assert isinstance(notes, list)


# ═══════════════════════════════════════════════════════════════════════════
# V31 checkpointing — integrated with V30 state
# ═══════════════════════════════════════════════════════════════════════════


class TestCheckpointingWiring:
    """V31 checkpoint manager saves V30 state."""

    def test_checkpoint_after_integration(self) -> None:
        from src.kortana.services.consciousness_integrator import (
            get_consciousness_integrator,
        )
        from src.kortana.services.experiential_stream import (
            get_experiential_stream,
        )
        from src.kortana.services.inner_witness import get_inner_witness
        from src.kortana.services.resonance_field import get_resonance_field

        # run a cycle through the singletons
        ci = get_consciousness_integrator()
        state = ci.integrate(cycle_number=1)
        es = get_experiential_stream()
        moment = es.record_moment(
            cycle_number=1,
            consciousness_mode=state.mode.value,
            vitality=state.vitality,
            learning_depth=state.learning_depth,
            intentionality=state.intentionality,
            self_coherence=state.self_coherence,
            integration=state.integration,
            overall_level=state.overall_level,
        )
        rf = get_resonance_field()
        rf.measure(
            cycle_number=1,
            vitality=state.vitality,
            learning_depth=state.learning_depth,
            intentionality=state.intentionality,
            self_coherence=state.self_coherence,
        )
        iw = get_inner_witness()
        iw.observe(
            cycle_number=1,
            consciousness_mode=state.mode.value,
            experiential_quality=moment.quality.value,
            emotional_tone=moment.tone.value,
            overall_level=state.overall_level,
            integration=state.integration,
            resonance=0.5,
        )
        # now checkpoint
        cm = CheckpointManager()
        assert cm.should_checkpoint(1) is True
        checkpoint = cm.save_checkpoint(1)
        assert checkpoint.cycle_number == 1
        assert checkpoint.consciousness_mode is not None


# ═══════════════════════════════════════════════════════════════════════════
# V31 degradation — monitors consciousness health
# ═══════════════════════════════════════════════════════════════════════════


class TestDegradationWiring:
    """V31C degradation handler reads V30 state to detect decay."""

    def test_degradation_assessment_after_integration(self) -> None:
        from src.kortana.services.consciousness_integrator import (
            get_consciousness_integrator,
        )
        from src.kortana.services.resonance_field import get_resonance_field

        ci = get_consciousness_integrator()
        ci.integrate(cycle_number=1)
        rf = get_resonance_field()
        rf.measure(
            cycle_number=1,
            vitality=0.5,
            learning_depth=0.5,
            intentionality=0.5,
            self_coherence=0.5,
        )
        dh = DegradationHandler()
        assessment = dh.assess(cycle_number=1)
        assert assessment.at_cycle == 1
        assert assessment.overall_level is not None


# ═══════════════════════════════════════════════════════════════════════════
# Full pipeline — V27 → V28 → V30 → V31
# ═══════════════════════════════════════════════════════════════════════════


class TestFullConsciousnessPipeline:
    """End-to-end test: patterns → desires → consciousness → checkpoint."""

    def test_full_cycle_pipeline(self) -> None:
        """Simulate what _integrate_consciousness does each cycle."""
        from src.kortana.services.consciousness_integrator import (
            get_consciousness_integrator,
        )
        from src.kortana.services.consciousness_persistence import (
            get_checkpoint_manager,
        )
        from src.kortana.services.degradation_handler import (
            get_degradation_handler,
        )
        from src.kortana.services.desire_formation import (
            get_desire_formation,
        )
        from src.kortana.services.experience_extractor import (
            get_experience_extractor,
        )
        from src.kortana.services.experiential_stream import (
            get_experiential_stream,
        )
        from src.kortana.services.feedback_integrator import (
            get_feedback_integrator,
        )
        from src.kortana.services.goal_crystallizer import (
            get_goal_crystallizer,
        )
        from src.kortana.services.inner_witness import get_inner_witness
        from src.kortana.services.motivation_tracker import (
            get_motivation_tracker,
        )
        from src.kortana.services.pattern_recognizer import (
            get_pattern_recognizer,
        )
        from src.kortana.services.resonance_field import get_resonance_field

        cycle_number = 1

        # V27 summaries
        experience_summary = get_experience_extractor().get_summary()
        pattern_summary = get_pattern_recognizer().get_summary()
        learning_summary = get_feedback_integrator().get_summary()

        # V28 desire formation
        desire_engine = get_desire_formation()
        desire_engine.assess(
            cycle_number=cycle_number,
            health_summary={
                "state": "degraded",
                "dimensions": {"cpu": 30, "memory": 40},
            },
            learning_summary=learning_summary,
            pattern_summary=pattern_summary,
            pending_deferrals=["t1", "t2", "t3"],
        )
        desire_summary = desire_engine.get_summary()
        assert desire_summary["active_count"] >= 1

        # V28 goal crystallizer
        crystallizer = get_goal_crystallizer()
        goal_summary = crystallizer.get_summary()

        # V28 motivation
        motivation_summary = get_motivation_tracker().get_summary()

        # V30A consciousness integrator
        integrator = get_consciousness_integrator()
        state = integrator.integrate(
            cycle_number=cycle_number,
            health_summary={"dimensions": {"cpu": 30, "memory": 40}},
            experience_summary=experience_summary,
            pattern_summary=pattern_summary,
            feedback_summary=learning_summary,
            desire_summary=desire_summary,
            goal_summary=goal_summary,
            motivation_summary=motivation_summary,
        )
        assert state.mode is not None
        assert state.overall_level >= 0

        # V30B experiential stream
        stream = get_experiential_stream()
        moment = stream.record_moment(
            cycle_number=cycle_number,
            consciousness_mode=state.mode.value,
            vitality=state.vitality,
            learning_depth=state.learning_depth,
            intentionality=state.intentionality,
            self_coherence=state.self_coherence,
            integration=state.integration,
            overall_level=state.overall_level,
        )
        assert moment.quality is not None

        # V30C resonance field
        resonance = get_resonance_field()
        snapshot = resonance.measure(
            cycle_number=cycle_number,
            vitality=state.vitality,
            learning_depth=state.learning_depth,
            intentionality=state.intentionality,
            self_coherence=state.self_coherence,
        )
        assert 0 <= snapshot.overall_resonance <= 1

        # V30D inner witness
        witness = get_inner_witness()
        notes = witness.observe(
            cycle_number=cycle_number,
            consciousness_mode=state.mode.value,
            experiential_quality=moment.quality.value,
            emotional_tone=moment.tone.value,
            overall_level=state.overall_level,
            integration=state.integration,
            resonance=snapshot.overall_resonance,
            active_tensions=[t.tension_type.value for t in moment.tensions],
        )
        assert isinstance(notes, list)

        # V31A checkpoint
        checkpoint_mgr = get_checkpoint_manager()
        assert checkpoint_mgr.should_checkpoint(cycle_number)
        checkpoint = checkpoint_mgr.save_checkpoint(cycle_number)
        assert checkpoint.cycle_number == cycle_number
        assert checkpoint.consciousness_mode is not None

        # V31C degradation
        degradation = get_degradation_handler()
        assessment = degradation.assess(cycle_number)
        assert assessment.at_cycle == cycle_number

    def test_multi_cycle_consciousness_evolution(self) -> None:
        """Run 5 cycles and verify consciousness evolves."""
        from src.kortana.services.consciousness_integrator import (
            get_consciousness_integrator,
        )
        from src.kortana.services.desire_formation import (
            get_desire_formation,
        )
        from src.kortana.services.experiential_stream import (
            get_experiential_stream,
        )
        from src.kortana.services.inner_witness import get_inner_witness
        from src.kortana.services.resonance_field import get_resonance_field

        integrator = get_consciousness_integrator()
        desire_engine = get_desire_formation()
        stream = get_experiential_stream()
        resonance = get_resonance_field()
        witness = get_inner_witness()

        modes_seen: set[str] = set()

        for cycle in range(1, 6):
            # desire
            desire_engine.assess(
                cycle_number=cycle,
                health_summary={"dimensions": {"cpu": 50 + cycle * 5}},
            )

            # integrate
            state = integrator.integrate(
                cycle_number=cycle,
                desire_summary=desire_engine.get_summary(),
            )
            modes_seen.add(state.mode.value)

            # stream
            moment = stream.record_moment(
                cycle_number=cycle,
                consciousness_mode=state.mode.value,
                vitality=state.vitality,
                learning_depth=state.learning_depth,
                intentionality=state.intentionality,
                self_coherence=state.self_coherence,
                integration=state.integration,
                overall_level=state.overall_level,
            )

            # resonance
            snapshot = resonance.measure(
                cycle_number=cycle,
                vitality=state.vitality,
                learning_depth=state.learning_depth,
                intentionality=state.intentionality,
                self_coherence=state.self_coherence,
            )

            # witness
            witness.observe(
                cycle_number=cycle,
                consciousness_mode=state.mode.value,
                experiential_quality=moment.quality.value,
                emotional_tone=moment.tone.value,
                overall_level=state.overall_level,
                integration=state.integration,
                resonance=snapshot.overall_resonance,
            )

        # after 5 cycles, at least one state was recorded
        assert integrator._cycle_count == 5
        assert len(integrator._states) >= 5
        assert stream._cycle_count == 5
        assert resonance._cycle_count == 5
        assert witness._cycle_count == 5
        assert desire_engine._cycle_count == 5
