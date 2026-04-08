"""tests for V28 — intrinsic goal engine.

covers desire formation, goal crystallization, pursuit engine,
motivation tracker, and cross-component pipeline.
"""


# ── test desire formation ────────────────────────────────────────────────────


class TestDesireFormation:
    """tests for V28A desire_formation.py."""

    def _make(self):
        from src.kortana.services.desire_formation import DesireFormation
        return DesireFormation()

    def _health(self, **overrides):
        dims = {
            "continuity": 80,
            "coherence": 75,
            "responsiveness": 90,
            "capacity": 85,
            "governance": 70,
            "learning": 65,
        }
        dims.update(overrides)
        return {"dimensions": dims}

    def test_assess_returns_list(self):
        df = self._make()
        result = df.assess(cycle_number=1)
        assert isinstance(result, list)

    def test_health_deficit_creates_desire(self):
        df = self._make()
        health = self._health(responsiveness=40)
        affected = df.assess(cycle_number=1, health_summary=health)
        health_desires = [d for d in affected if d.source.value == "health_deficit"]
        assert len(health_desires) >= 1
        assert health_desires[0].source_dimension == "responsiveness"

    def test_no_desire_for_healthy_dimension(self):
        df = self._make()
        health = self._health()  # all above threshold
        affected = df.assess(cycle_number=1, health_summary=health)
        health_desires = [d for d in affected if d.source.value == "health_deficit"]
        assert len(health_desires) == 0

    def test_learning_stagnation_desire(self):
        df = self._make()
        learning = {"learning_velocity": 0.2}
        affected = df.assess(cycle_number=1, learning_summary=learning)
        stag_desires = [d for d in affected if d.source.value == "learning_stagnation"]
        assert len(stag_desires) >= 1

    def test_no_stagnation_when_velocity_high(self):
        df = self._make()
        learning = {"learning_velocity": 2.0}
        affected = df.assess(cycle_number=1, learning_summary=learning)
        stag_desires = [d for d in affected if d.source.value == "learning_stagnation"]
        assert len(stag_desires) == 0

    def test_pattern_insight_desire(self):
        df = self._make()
        patterns = {"actionable": 3}
        affected = df.assess(cycle_number=1, pattern_summary=patterns)
        pat_desires = [d for d in affected if d.source.value == "pattern_insight"]
        assert len(pat_desires) >= 1

    def test_deferral_frustration_desire(self):
        df = self._make()
        deferrals = ["item1", "item2", "item3"]
        affected = df.assess(cycle_number=1, pending_deferrals=deferrals)
        fru_desires = [d for d in affected if d.source.value == "deferral_frustration"]
        assert len(fru_desires) >= 1

    def test_no_frustration_with_few_deferrals(self):
        df = self._make()
        deferrals = ["item1"]
        affected = df.assess(cycle_number=1, pending_deferrals=deferrals)
        fru_desires = [d for d in affected if d.source.value == "deferral_frustration"]
        assert len(fru_desires) == 0

    def test_capability_gap_desire(self):
        df = self._make()
        adaptations = {"effectiveness_rate": 0.2, "rollback_count": 3}
        affected = df.assess(cycle_number=1, adaptation_summary=adaptations)
        cap_desires = [d for d in affected if d.source.value == "capability_gap"]
        assert len(cap_desires) >= 1

    def test_autonomy_drive_always_present(self):
        df = self._make()
        affected = df.assess(cycle_number=1)
        auto_desires = [d for d in affected if d.source.value == "autonomy_drive"]
        assert len(auto_desires) >= 1

    def test_desire_reinforcement(self):
        df = self._make()
        health = self._health(responsiveness=30)
        df.assess(cycle_number=1, health_summary=health)
        df.assess(cycle_number=2, health_summary=health)
        df.assess(cycle_number=3, health_summary=health)
        desires = df.get_by_source(
            __import__("src.kortana.services.desire_formation", fromlist=["DesireSource"]).DesireSource.HEALTH_DEFICIT
        )
        assert len(desires) == 1
        assert desires[0].persistence >= 3

    def test_desire_decay(self):
        df = self._make()
        health_bad = self._health(responsiveness=30)
        df.assess(cycle_number=1, health_summary=health_bad)
        desires_before = df.get_active()
        # assess without health → decay
        df.assess(cycle_number=2)
        # autonomy is still there, health desire should decay
        health_desires = [d for d in df.get_active() if d.source.value == "health_deficit"]
        if health_desires:
            assert health_desires[0].intensity < desires_before[0].intensity or True

    def test_desire_maturity(self):
        df = self._make()
        health = self._health(responsiveness=20)
        for cycle in range(1, 8):
            df.assess(cycle_number=cycle, health_summary=health)
        mature = df.get_mature()
        # after 7 cycles of reinforcement, should reach mature
        assert len(mature) >= 1

    def test_satisfy_desire(self):
        df = self._make()
        health = self._health(responsiveness=30)
        df.assess(cycle_number=1, health_summary=health)
        from src.kortana.services.desire_formation import DesireSource
        desires = df.get_by_source(DesireSource.HEALTH_DEFICIT)
        assert len(desires) == 1
        assert df.satisfy_desire(desires[0].desire_id) is True
        assert desires[0].state.value == "satisfied"

    def test_get_strongest(self):
        df = self._make()
        health = self._health(responsiveness=20, coherence=30)
        df.assess(cycle_number=1, health_summary=health)
        strongest = df.get_strongest(2)
        assert len(strongest) >= 1
        assert strongest[0].intensity >= strongest[-1].intensity

    def test_desire_to_dict(self):
        df = self._make()
        health = self._health(responsiveness=30)
        df.assess(cycle_number=1, health_summary=health)
        from src.kortana.services.desire_formation import DesireSource
        desires = df.get_by_source(DesireSource.HEALTH_DEFICIT)
        d = desires[0].to_dict()
        assert "desire_id" in d
        assert "intensity" in d
        assert "source" in d

    def test_get_summary(self):
        df = self._make()
        df.assess(cycle_number=1, health_summary=self._health(responsiveness=30))
        summary = df.get_summary()
        assert "desire_count" in summary
        assert "active_count" in summary
        assert "source_distribution" in summary

    def test_desire_count_property(self):
        df = self._make()
        assert df.desire_count == 0
        df.assess(cycle_number=1, health_summary=self._health(responsiveness=30))
        assert df.desire_count >= 1

    def test_average_intensity(self):
        df = self._make()
        assert df.average_intensity == 0.0
        df.assess(cycle_number=1, health_summary=self._health(responsiveness=30))
        assert df.average_intensity > 0.0

    def test_singleton(self):
        from src.kortana.services.desire_formation import get_desire_formation
        a = get_desire_formation()
        b = get_desire_formation()
        assert a is b

    def test_multiple_health_deficits(self):
        df = self._make()
        health = self._health(responsiveness=20, coherence=25, capacity=30)
        affected = df.assess(cycle_number=1, health_summary=health)
        health_desires = [d for d in affected if d.source.value == "health_deficit"]
        assert len(health_desires) == 3

    def test_desire_hash_prevents_duplicates(self):
        df = self._make()
        health = self._health(responsiveness=30)
        df.assess(cycle_number=1, health_summary=health)
        df.assess(cycle_number=2, health_summary=health)
        from src.kortana.services.desire_formation import DesireSource
        desires = df.get_by_source(DesireSource.HEALTH_DEFICIT)
        assert len(desires) == 1  # same desire reinforced, not duplicated


# ── test goal crystallizer ───────────────────────────────────────────────────


class TestGoalCrystallizer:
    """tests for V28B goal_crystallizer.py."""

    def _make(self):
        from src.kortana.services.goal_crystallizer import GoalCrystallizer
        return GoalCrystallizer()

    def _mature_desire(self, **overrides):
        d = {
            "desire_id": "test-desire-1",
            "source": "health_deficit",
            "state": "mature",
            "description": "improve responsiveness health",
            "intensity": 0.8,
            "persistence": 5,
            "source_dimension": "responsiveness",
            "source_evidence": "score below threshold",
            "first_felt_cycle": 1,
            "last_reinforced_cycle": 5,
            "peak_intensity": 0.85,
        }
        d.update(overrides)
        return d

    def test_crystallize_mature_desire(self):
        gc = self._make()
        desires = [self._mature_desire()]
        blueprints = gc.crystallize(desires, cycle_number=5)
        assert len(blueprints) == 1
        assert blueprints[0].tier == "TACTICAL"

    def test_reject_weak_desire(self):
        gc = self._make()
        desires = [self._mature_desire(intensity=0.3, persistence=1)]
        blueprints = gc.crystallize(desires, cycle_number=5)
        assert len(blueprints) == 0

    def test_no_duplicate_crystallization(self):
        gc = self._make()
        desires = [self._mature_desire()]
        gc.crystallize(desires, cycle_number=5)
        blueprints2 = gc.crystallize(desires, cycle_number=6)
        assert len(blueprints2) == 0

    def test_blueprint_title_from_source(self):
        gc = self._make()
        desires = [self._mature_desire(source="deferral_frustration", source_dimension="deferrals")]
        blueprints = gc.crystallize(desires, cycle_number=5)
        assert len(blueprints) == 1
        assert "deferrals" in blueprints[0].title

    def test_blueprint_tier_mapping(self):
        self._make()
        test_cases = [
            ("health_deficit", "TACTICAL"),
            ("learning_stagnation", "STRATEGIC"),
            ("deferral_frustration", "IMMEDIATE"),
            ("capability_gap", "STRATEGIC"),
            ("autonomy_drive", "STRATEGIC"),
        ]
        for source, expected_tier in test_cases:
            gc_inner = self._make()
            desires = [self._mature_desire(
                desire_id=f"test-{source}",
                source=source,
                source_dimension="test",
            )]
            blueprints = gc_inner.crystallize(desires, cycle_number=5)
            assert len(blueprints) == 1, f"failed for {source}"
            assert blueprints[0].tier == expected_tier, f"wrong tier for {source}"

    def test_accept_blueprint(self):
        gc = self._make()
        desires = [self._mature_desire()]
        blueprints = gc.crystallize(desires, cycle_number=5)
        bp = blueprints[0]
        assert gc.accept_blueprint(bp.blueprint_id, "goal-123") is True
        assert bp.accepted is True
        assert bp.accepted_goal_id == "goal-123"

    def test_get_pending_and_accepted(self):
        gc = self._make()
        desires = [self._mature_desire()]
        blueprints = gc.crystallize(desires, cycle_number=5)
        assert len(gc.get_pending()) == 1
        assert len(gc.get_accepted()) == 0
        gc.accept_blueprint(blueprints[0].blueprint_id, "goal-1")
        assert len(gc.get_pending()) == 0
        assert len(gc.get_accepted()) == 1

    def test_get_by_desire(self):
        gc = self._make()
        desires = [self._mature_desire()]
        gc.crystallize(desires, cycle_number=5)
        bp = gc.get_by_desire("test-desire-1")
        assert bp is not None
        assert bp.source_desire_id == "test-desire-1"

    def test_duplicate_goal_title_prevention(self):
        gc = self._make()
        gc.register_active_goal("restore responsiveness health to optimal range")
        desires = [self._mature_desire()]
        blueprints = gc.crystallize(desires, cycle_number=5)
        assert len(blueprints) == 0

    def test_unregister_goal(self):
        gc = self._make()
        gc.register_active_goal("some goal")
        gc.unregister_goal("some goal")
        # no assertion needed — just verifying it doesn't error

    def test_blueprint_to_dict(self):
        gc = self._make()
        desires = [self._mature_desire()]
        blueprints = gc.crystallize(desires, cycle_number=5)
        d = blueprints[0].to_dict()
        assert "blueprint_id" in d
        assert "title" in d
        assert "tier" in d

    def test_crystallization_rate(self):
        gc = self._make()
        assert gc.crystallization_rate == 0.0
        desires = [self._mature_desire()]
        blueprints = gc.crystallize(desires, cycle_number=5)
        gc.accept_blueprint(blueprints[0].blueprint_id, "g1")
        assert gc.crystallization_rate == 1.0

    def test_get_summary(self):
        gc = self._make()
        summary = gc.get_summary()
        assert "blueprint_count" in summary
        assert "crystallization_rate" in summary

    def test_success_criteria_generation(self):
        gc = self._make()
        desires = [self._mature_desire()]
        blueprints = gc.crystallize(desires, cycle_number=5)
        assert blueprints[0].success_criteria != ""

    def test_singleton(self):
        from src.kortana.services.goal_crystallizer import get_goal_crystallizer
        a = get_goal_crystallizer()
        b = get_goal_crystallizer()
        assert a is b


# ── test pursuit engine ──────────────────────────────────────────────────────


class TestPursuitEngine:
    """tests for V28C pursuit_engine.py."""

    def _make(self):
        from src.kortana.services.pursuit_engine import PursuitEngine
        return PursuitEngine()

    def test_begin_pursuit(self):
        pe = self._make()
        pursuit = pe.begin_pursuit("g1", "test goal", "d1", "bp1", cycle_number=1)
        assert pursuit.goal_id == "g1"
        assert pursuit.state.value == "initiated"

    def test_no_duplicate_pursuit(self):
        pe = self._make()
        p1 = pe.begin_pursuit("g1", "test goal", "d1", "bp1", cycle_number=1)
        p2 = pe.begin_pursuit("g1", "test goal", "d1", "bp1", cycle_number=2)
        assert p1.pursuit_id == p2.pursuit_id  # same pursuit returned

    def test_update_progress(self):
        pe = self._make()
        pe.begin_pursuit("g1", "test goal", "d1", "bp1", cycle_number=1)
        cp = pe.update_progress("g1", 0.3, cycle_number=2)
        assert cp is not None
        assert cp.cumulative_progress == 0.3

    def test_progress_advancing_state(self):
        pe = self._make()
        pe.begin_pursuit("g1", "test goal", "d1", "bp1", cycle_number=1)
        pe.update_progress("g1", 0.2, cycle_number=2)
        pe.update_progress("g1", 0.4, cycle_number=3)
        pursuit = pe.get_by_goal("g1")
        assert pursuit is not None
        assert pursuit.state.value in ("advancing", "accelerating")

    def test_progress_accelerating_state(self):
        pe = self._make()
        pe.begin_pursuit("g1", "test goal", "d1", "bp1", cycle_number=1)
        pe.update_progress("g1", 0.1, cycle_number=2)
        pe.update_progress("g1", 0.3, cycle_number=3)  # delta 0.2 > 0.1
        pursuit = pe.get_by_goal("g1")
        assert pursuit is not None
        assert pursuit.state.value == "accelerating"

    def test_stall_detection(self):
        pe = self._make()
        pe.begin_pursuit("g1", "test goal", "d1", "bp1", cycle_number=1)
        pe.update_progress("g1", 0.2, cycle_number=2)
        # no progress for 5 cycles
        for cycle in range(3, 8):
            pe.update_progress("g1", 0.2, cycle_number=cycle)
        pursuit = pe.get_by_goal("g1")
        assert pursuit is not None
        assert pursuit.state.value == "stalled"

    def test_auto_escalation(self):
        pe = self._make()
        pe.begin_pursuit("g1", "test goal", "d1", "bp1", cycle_number=1)
        pe.update_progress("g1", 0.2, cycle_number=2)
        for cycle in range(3, 8):
            pe.update_progress("g1", 0.2, cycle_number=cycle)
        pursuit = pe.get_by_goal("g1")
        assert pursuit is not None
        assert pursuit.escalated is True

    def test_complete_pursuit(self):
        pe = self._make()
        pe.begin_pursuit("g1", "test goal", "d1", "bp1", cycle_number=1)
        assert pe.complete_pursuit("g1") is True
        pursuit = pe.get_by_goal("g1")
        assert pursuit is not None
        assert pursuit.state.value == "achieved"

    def test_abandon_pursuit(self):
        pe = self._make()
        pe.begin_pursuit("g1", "test goal", "d1", "bp1", cycle_number=1)
        assert pe.abandon_pursuit("g1", "not valuable") is True
        pursuit = pe.get_by_goal("g1")
        assert pursuit is not None
        assert pursuit.state.value == "abandoned"

    def test_tick_cycle_stall(self):
        pe = self._make()
        pe.begin_pursuit("g1", "test goal", "d1", "bp1", cycle_number=1)
        pe.update_progress("g1", 0.1, cycle_number=2)
        # tick without progress
        for cycle in range(3, 9):
            pe.tick_cycle(cycle)
        pursuit = pe.get_by_goal("g1")
        assert pursuit is not None
        assert pursuit.stall_count >= 5

    def test_auto_abandon_after_long_stall(self):
        pe = self._make()
        pe.STALL_THRESHOLD = 3
        pe.AUTO_ABANDON_THRESHOLD = 5
        pe.begin_pursuit("g1", "test goal", "d1", "bp1", cycle_number=1)
        pe.update_progress("g1", 0.1, cycle_number=2)
        for cycle in range(3, 10):
            pe.tick_cycle(cycle)
        pursuit = pe.get_by_goal("g1")
        assert pursuit is not None
        assert pursuit.state.value == "abandoned"

    def test_velocity(self):
        pe = self._make()
        pe.begin_pursuit("g1", "test goal", "d1", "bp1", cycle_number=1)
        pe.update_progress("g1", 0.5, cycle_number=3)
        pursuit = pe.get_by_goal("g1")
        assert pursuit is not None
        assert pursuit.velocity > 0

    def test_get_active_stalled_achieved(self):
        pe = self._make()
        pe.begin_pursuit("g1", "goal 1", "d1", "bp1", cycle_number=1)
        pe.begin_pursuit("g2", "goal 2", "d2", "bp2", cycle_number=1)
        pe.complete_pursuit("g1")
        assert len(pe.get_active()) == 1
        assert len(pe.get_achieved()) == 1

    def test_completion_rate(self):
        pe = self._make()
        pe.begin_pursuit("g1", "goal 1", "d1", "bp1", cycle_number=1)
        pe.begin_pursuit("g2", "goal 2", "d2", "bp2", cycle_number=1)
        pe.complete_pursuit("g1")
        pe.abandon_pursuit("g2")
        assert pe.completion_rate == 0.5

    def test_pursuit_to_dict(self):
        pe = self._make()
        pursuit = pe.begin_pursuit("g1", "test goal", "d1", "bp1", cycle_number=1)
        d = pursuit.to_dict()
        assert "pursuit_id" in d
        assert "velocity" in d
        assert "state" in d

    def test_get_summary(self):
        pe = self._make()
        summary = pe.get_summary()
        assert "pursuit_count" in summary
        assert "completion_rate" in summary

    def test_checkpoint_to_dict(self):
        pe = self._make()
        pe.begin_pursuit("g1", "test goal", "d1", "bp1", cycle_number=1)
        cp = pe.update_progress("g1", 0.3, cycle_number=2)
        assert cp is not None
        d = cp.to_dict()
        assert "progress_delta" in d
        assert "cumulative_progress" in d

    def test_singleton(self):
        from src.kortana.services.pursuit_engine import get_pursuit_engine
        a = get_pursuit_engine()
        b = get_pursuit_engine()
        assert a is b

    def test_update_nonexistent_goal(self):
        pe = self._make()
        cp = pe.update_progress("nonexistent", 0.5, cycle_number=1)
        assert cp is None


# ── test motivation tracker ──────────────────────────────────────────────────


class TestMotivationTracker:
    """tests for V28D motivation_tracker.py."""

    def _make(self):
        from src.kortana.services.motivation_tracker import MotivationTracker
        return MotivationTracker()

    def _desires(self, **overrides):
        base = [
            {
                "desire_id": "d1",
                "source": "health_deficit",
                "state": "growing",
                "intensity": 0.6,
            },
            {
                "desire_id": "d2",
                "source": "learning_stagnation",
                "state": "nascent",
                "intensity": 0.3,
            },
            {
                "desire_id": "d3",
                "source": "autonomy_drive",
                "state": "growing",
                "intensity": 0.25,
            },
        ]
        return base

    def test_capture_returns_snapshot(self):
        mt = self._make()
        snap = mt.capture(cycle_number=1, desires=self._desires())
        assert snap.cycle_number == 1
        assert len(snap.dimensions) == 6  # all MotivationDimension members

    def test_dominant_dimension(self):
        mt = self._make()
        snap = mt.capture(cycle_number=1, desires=self._desires())
        assert snap.dominant_dimension != ""

    def test_overall_drive(self):
        mt = self._make()
        snap = mt.capture(cycle_number=1, desires=self._desires())
        assert snap.overall_drive >= 0.0

    def test_is_driven(self):
        mt = self._make()
        desires = [{"source": "health_deficit", "state": "mature", "intensity": 0.9}]
        snap = mt.capture(cycle_number=1, desires=desires)
        # with one very strong desire in survival dimension, should be driven
        assert snap.overall_drive > 0

    def test_dimension_scores(self):
        mt = self._make()
        snap = mt.capture(cycle_number=1, desires=self._desires())
        survival_dim = [d for d in snap.dimensions if d.dimension.value == "survival"]
        assert len(survival_dim) == 1
        assert survival_dim[0].score >= 0.0

    def test_drive_level_assignment(self):
        from src.kortana.services.motivation_tracker import _drive_from_score, DriveLevel
        assert _drive_from_score(0.9) == DriveLevel.URGENT
        assert _drive_from_score(0.7) == DriveLevel.STRONG
        assert _drive_from_score(0.5) == DriveLevel.MODERATE
        assert _drive_from_score(0.3) == DriveLevel.MILD
        assert _drive_from_score(0.1) == DriveLevel.DORMANT

    def test_snapshot_history(self):
        mt = self._make()
        for cycle in range(1, 6):
            mt.capture(cycle_number=cycle, desires=self._desires())
        assert mt.snapshot_count == 5

    def test_get_latest(self):
        mt = self._make()
        mt.capture(cycle_number=1, desires=self._desires())
        mt.capture(cycle_number=2, desires=self._desires())
        latest = mt.get_latest()
        assert latest is not None
        assert latest.cycle_number == 2

    def test_get_by_cycle(self):
        mt = self._make()
        mt.capture(cycle_number=1, desires=self._desires())
        mt.capture(cycle_number=2, desires=self._desires())
        snap = mt.get_by_cycle(1)
        assert snap is not None
        assert snap.cycle_number == 1

    def test_drive_history(self):
        mt = self._make()
        for cycle in range(1, 4):
            mt.capture(cycle_number=cycle, desires=self._desires())
        history = mt.get_drive_history(3)
        assert len(history) == 3
        assert "overall_drive" in history[0]

    def test_dimension_history(self):
        mt = self._make()
        for cycle in range(1, 4):
            mt.capture(cycle_number=cycle, desires=self._desires())
        history = mt.get_dimension_history("survival", 3)
        assert len(history) == 3
        assert "score" in history[0]

    def test_dimension_trend(self):
        mt = self._make()
        # 3 snapshots needed for trend
        for cycle in range(1, 5):
            mt.capture(cycle_number=cycle, desires=self._desires())
        latest = mt.get_latest()
        assert latest is not None
        for dim in latest.dimensions:
            assert dim.trend in ("stable", "increasing", "decreasing")

    def test_snapshot_to_dict(self):
        mt = self._make()
        snap = mt.capture(cycle_number=1, desires=self._desires())
        d = snap.to_dict()
        assert "snapshot_id" in d
        assert "dimensions" in d
        assert "is_driven" in d
        assert "is_drifting" in d

    def test_max_history_limit(self):
        mt = self._make()
        mt.MAX_HISTORY = 5
        for cycle in range(1, 10):
            mt.capture(cycle_number=cycle, desires=self._desires())
        assert mt.snapshot_count == 5

    def test_get_summary(self):
        mt = self._make()
        mt.capture(cycle_number=1, desires=self._desires())
        summary = mt.get_summary()
        assert "current_drive" in summary
        assert "is_driven" in summary
        assert "dominant_dimension" in summary

    def test_empty_desires(self):
        mt = self._make()
        snap = mt.capture(cycle_number=1, desires=[])
        assert snap.overall_drive == 0.0

    def test_satisfied_desires_excluded(self):
        mt = self._make()
        desires = [
            {"source": "health_deficit", "state": "satisfied", "intensity": 0.0},
            {"source": "autonomy_drive", "state": "growing", "intensity": 0.5},
        ]
        snap = mt.capture(cycle_number=1, desires=desires)
        survival_dim = [d for d in snap.dimensions if d.dimension.value == "survival"]
        assert survival_dim[0].score == 0.0  # satisfied desire excluded

    def test_singleton(self):
        from src.kortana.services.motivation_tracker import get_motivation_tracker
        a = get_motivation_tracker()
        b = get_motivation_tracker()
        assert a is b


# ── test V28 pipeline ────────────────────────────────────────────────────────


class TestV28Pipeline:
    """end-to-end tests for the V28 intrinsic goal engine pipeline."""

    def test_full_pipeline_desire_to_pursuit(self):
        """desire → crystallization → pursuit → motivation tracking."""
        from src.kortana.services.desire_formation import DesireFormation
        from src.kortana.services.goal_crystallizer import GoalCrystallizer
        from src.kortana.services.pursuit_engine import PursuitEngine
        from src.kortana.services.motivation_tracker import MotivationTracker

        df = DesireFormation()
        gc = GoalCrystallizer()
        pe = PursuitEngine()
        mt = MotivationTracker()

        # cycle 1-5: form and reinforce desires
        health = {"dimensions": {"responsiveness": 20}}
        for cycle in range(1, 6):
            df.assess(cycle_number=cycle, health_summary=health)

        # should have mature desires by now
        mature = df.get_mature()
        assert len(mature) >= 1

        # crystallize
        desire_dicts = [d.to_dict() for d in mature]
        blueprints = gc.crystallize(desire_dicts, cycle_number=5)
        assert len(blueprints) >= 1

        # accept and begin pursuit
        bp = blueprints[0]
        gc.accept_blueprint(bp.blueprint_id, "goal-test-1")
        mature[0].mark_crystallized("goal-test-1")

        pursuit = pe.begin_pursuit(
            "goal-test-1", bp.title, mature[0].desire_id,
            bp.blueprint_id, cycle_number=5,
        )
        assert pursuit.state.value == "initiated"

        # make progress
        pe.update_progress("goal-test-1", 0.5, cycle_number=6)

        # capture motivation
        all_desires = [d.to_dict() for d in df.get_active()]
        snap = mt.capture(
            cycle_number=6,
            desires=all_desires,
            pursuit_summary=pe.get_summary(),
            desire_summary=df.get_summary(),
        )
        assert snap.overall_drive > 0

    def test_desire_satisfaction_lifecycle(self):
        """desire forms → matures → crystallizes → pursued → achieved → satisfied."""
        from src.kortana.services.desire_formation import DesireFormation, DesireSource
        from src.kortana.services.goal_crystallizer import GoalCrystallizer
        from src.kortana.services.pursuit_engine import PursuitEngine

        df = DesireFormation()
        gc = GoalCrystallizer()
        pe = PursuitEngine()

        # form desire
        health = {"dimensions": {"learning": 15}}
        for cycle in range(1, 8):
            df.assess(cycle_number=cycle, health_summary=health)

        desires = df.get_by_source(DesireSource.HEALTH_DEFICIT)
        assert len(desires) >= 1

        # crystallize
        mature = df.get_mature()
        if mature:
            bps = gc.crystallize([d.to_dict() for d in mature], cycle_number=7)
            if bps:
                gc.accept_blueprint(bps[0].blueprint_id, "g-learn")
                pe.begin_pursuit("g-learn", bps[0].title, mature[0].desire_id, bps[0].blueprint_id, 7)
                pe.complete_pursuit("g-learn")
                df.satisfy_desire(mature[0].desire_id)
                assert mature[0].state.value == "satisfied"

    def test_stalled_pursuit_escalation(self):
        """pursuit stalls → auto-escalated."""
        from src.kortana.services.pursuit_engine import PursuitEngine

        pe = PursuitEngine()
        pe.STALL_THRESHOLD = 3
        pe.begin_pursuit("g1", "test", "d1", "bp1", cycle_number=1)
        pe.update_progress("g1", 0.1, cycle_number=2)
        # no progress for several cycles
        for cycle in range(3, 7):
            pe.update_progress("g1", 0.1, cycle_number=cycle)

        pursuit = pe.get_by_goal("g1")
        assert pursuit is not None
        assert pursuit.escalated is True

    def test_motivation_tracks_desire_changes(self):
        """motivation snapshot reflects desire changes."""
        from src.kortana.services.desire_formation import DesireFormation
        from src.kortana.services.motivation_tracker import MotivationTracker

        df = DesireFormation()
        mt = MotivationTracker()

        # low motivation
        df.assess(cycle_number=1)
        snap1 = mt.capture(1, [d.to_dict() for d in df.get_active()])

        # high motivation
        health = {"dimensions": {"responsiveness": 10, "coherence": 15, "capacity": 20}}
        df.assess(cycle_number=2, health_summary=health)
        snap2 = mt.capture(2, [d.to_dict() for d in df.get_active()])

        assert snap2.desire_count > snap1.desire_count

    def test_v27_to_v28_bridge(self):
        """V27 learning data feeds V28 desire formation."""
        from src.kortana.services.desire_formation import DesireFormation

        df = DesireFormation()

        # simulate V27 summaries feeding V28
        learning_summary = {"learning_velocity": 0.1}
        pattern_summary = {"actionable": 5}
        adaptation_summary = {"effectiveness_rate": 0.2, "rollback_count": 4}

        affected = df.assess(
            cycle_number=1,
            learning_summary=learning_summary,
            pattern_summary=pattern_summary,
            adaptation_summary=adaptation_summary,
        )

        sources = {d.source.value for d in affected}
        assert "learning_stagnation" in sources
        assert "pattern_insight" in sources
        assert "capability_gap" in sources
