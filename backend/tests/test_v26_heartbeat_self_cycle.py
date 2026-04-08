"""V26 — heartbeat & continuous self-cycle tests.

Tests for heartbeat loop, cycle memory, health assessor, and graceful degradation.
"""



# ═══════════════════════════════════════════════════════════════════════════════
# V26A: Heartbeat Loop Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestHeartbeatLoop:
    """Tests for the core heartbeat loop."""

    def _make(self):
        from src.kortana.services.heartbeat_loop import HeartbeatLoop
        return HeartbeatLoop()

    def test_begin_beat(self):
        from src.kortana.services.heartbeat_loop import HeartbeatPhase, HeartbeatState
        loop = self._make()
        beat = loop.begin_beat()
        assert beat.cycle_number == 1
        assert beat.state == HeartbeatState.ALIVE
        assert beat.phase == HeartbeatPhase.OBSERVE
        assert loop.beat_count == 1

    def test_dormant_to_alive(self):
        from src.kortana.services.heartbeat_loop import HeartbeatState
        loop = self._make()
        assert loop.current_state == HeartbeatState.DORMANT
        loop.begin_beat()
        assert loop.current_state == HeartbeatState.ALIVE

    def test_cycle_number_increments(self):
        loop = self._make()
        b1 = loop.begin_beat()
        b2 = loop.begin_beat()
        b3 = loop.begin_beat()
        assert b1.cycle_number == 1
        assert b2.cycle_number == 2
        assert b3.cycle_number == 3
        assert loop.cycle_number == 3

    def test_add_observation(self):
        loop = self._make()
        beat = loop.begin_beat()
        obs = loop.add_observation(beat.beat_id, "health-check", "all systems nominal")
        assert obs is not None
        assert obs.source == "health-check"
        assert len(beat.observations) == 1

    def test_add_observation_with_severity(self):
        loop = self._make()
        beat = loop.begin_beat()
        obs = loop.add_observation(beat.beat_id, "monitor", "high latency",
                                   severity="warning", data={"ms": 500})
        assert obs is not None
        assert obs.severity == "warning"
        assert obs.data["ms"] == 500

    def test_add_decision(self):
        loop = self._make()
        beat = loop.begin_beat()
        dec = loop.add_decision(beat.beat_id, "scale-up", "latency exceeds threshold",
                                priority=2)
        assert dec is not None
        assert dec.action_type == "scale-up"
        assert dec.priority == 2
        assert not dec.deferred

    def test_add_deferral(self):
        loop = self._make()
        beat = loop.begin_beat()
        dec = loop.add_deferral(beat.beat_id, "refactor", "not urgent this cycle")
        assert dec is not None
        assert dec.deferred is True
        assert "refactor" in beat.deferrals[0]

    def test_record_action(self):
        loop = self._make()
        beat = loop.begin_beat()
        assert loop.record_action(beat.beat_id, "scaled provider to 3 instances")
        assert len(beat.actions_taken) == 1

    def test_add_reflection(self):
        loop = self._make()
        beat = loop.begin_beat()
        assert loop.add_reflection(beat.beat_id, "cycle was productive, 2 actions taken")
        assert len(beat.reflections) == 1

    def test_complete_beat(self):
        loop = self._make()
        beat = loop.begin_beat()
        loop.add_observation(beat.beat_id, "sys", "check")
        assert loop.complete_beat(beat.beat_id) is True
        assert beat.ended_at != ""
        assert beat.duration_ms >= 0

    def test_get_beat(self):
        loop = self._make()
        beat = loop.begin_beat()
        found = loop.get_beat(beat.beat_id)
        assert found is not None
        assert found.beat_id == beat.beat_id

    def test_get_nonexistent_beat(self):
        loop = self._make()
        assert loop.get_beat("nonexistent") is None

    def test_get_recent(self):
        loop = self._make()
        for _ in range(5):
            loop.begin_beat()
        recent = loop.get_recent(3)
        assert len(recent) == 3
        # Most recent first
        assert recent[0].cycle_number == 5

    def test_last_beat(self):
        loop = self._make()
        assert loop.last_beat is None
        b1 = loop.begin_beat()
        assert loop.last_beat is b1
        b2 = loop.begin_beat()
        assert loop.last_beat is b2

    def test_uptime_beats(self):
        from src.kortana.services.heartbeat_loop import HeartbeatState
        loop = self._make()
        loop.begin_beat()  # ALIVE
        loop.begin_beat()  # ALIVE
        loop.set_state(HeartbeatState.DEGRADED)
        loop.begin_beat()  # DEGRADED
        assert loop.uptime_beats == 2

    def test_total_observations(self):
        loop = self._make()
        b1 = loop.begin_beat()
        loop.add_observation(b1.beat_id, "a", "x")
        loop.add_observation(b1.beat_id, "b", "y")
        b2 = loop.begin_beat()
        loop.add_observation(b2.beat_id, "c", "z")
        assert loop.total_observations == 3

    def test_total_deferrals(self):
        loop = self._make()
        b1 = loop.begin_beat()
        loop.add_deferral(b1.beat_id, "a", "r1")
        loop.add_deferral(b1.beat_id, "b", "r2")
        assert loop.total_deferrals == 2

    def test_set_state(self):
        from src.kortana.services.heartbeat_loop import HeartbeatState
        loop = self._make()
        prev = loop.set_state(HeartbeatState.RECOVERING)
        assert prev == HeartbeatState.DORMANT
        assert loop.current_state == HeartbeatState.RECOVERING

    def test_is_alive(self):
        from src.kortana.services.heartbeat_loop import HeartbeatState
        loop = self._make()
        assert not loop.is_alive
        loop.set_state(HeartbeatState.ALIVE)
        assert loop.is_alive
        loop.set_state(HeartbeatState.RECOVERING)
        assert loop.is_alive
        loop.set_state(HeartbeatState.DEGRADED)
        assert not loop.is_alive

    def test_beat_hash(self):
        loop = self._make()
        beat = loop.begin_beat()
        assert len(beat.beat_hash) == 16

    def test_beat_to_dict(self):
        loop = self._make()
        beat = loop.begin_beat()
        loop.add_observation(beat.beat_id, "sys", "ok")
        data = beat.to_dict()
        assert data["cycle_number"] == 1
        assert data["state"] == "alive"
        assert len(data["observations"]) == 1

    def test_observation_to_dict(self):
        loop = self._make()
        beat = loop.begin_beat()
        obs = loop.add_observation(beat.beat_id, "sys", "ok")
        data = obs.to_dict()
        assert data["source"] == "sys"

    def test_decision_to_dict(self):
        loop = self._make()
        beat = loop.begin_beat()
        dec = loop.add_decision(beat.beat_id, "act", "reason", priority=1)
        data = dec.to_dict()
        assert data["action_type"] == "act"
        assert data["priority"] == 1

    def test_summary(self):
        loop = self._make()
        b = loop.begin_beat()
        loop.add_observation(b.beat_id, "s", "d")
        loop.complete_beat(b.beat_id)
        summary = loop.get_summary()
        assert summary["beat_count"] == 1
        assert summary["state"] == "alive"
        assert summary["uptime_beats"] == 1

    def test_operations_on_nonexistent_beat(self):
        loop = self._make()
        assert loop.add_observation("bad", "s", "d") is None
        assert loop.add_decision("bad", "a", "r") is None
        assert loop.add_deferral("bad", "a", "r") is None
        assert loop.record_action("bad", "a") is False
        assert loop.add_reflection("bad", "r") is False
        assert loop.complete_beat("bad") is False

    def test_module_singleton(self):
        from src.kortana.services.heartbeat_loop import get_heartbeat_loop
        h1 = get_heartbeat_loop()
        h2 = get_heartbeat_loop()
        assert h1 is h2


# ═══════════════════════════════════════════════════════════════════════════════
# V26B: Cycle Memory Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestCycleMemory:
    """Tests for cycle memory and context inheritance."""

    def _make(self):
        from src.kortana.services.cycle_memory import CycleMemory
        return CycleMemory()

    def test_begin_cycle(self):
        mem = self._make()
        record = mem.begin_cycle()
        assert record.cycle_number == 1
        assert not record.finalized
        assert mem.cycle_count == 1

    def test_cycle_number_increments(self):
        mem = self._make()
        c1 = mem.begin_cycle()
        c2 = mem.begin_cycle()
        assert c1.cycle_number == 1
        assert c2.cycle_number == 2

    def test_record_observation(self):
        mem = self._make()
        c = mem.begin_cycle()
        assert mem.record_observation(c.cycle_id, "health check passed")
        assert len(c.observations) == 1

    def test_record_decision(self):
        mem = self._make()
        c = mem.begin_cycle()
        assert mem.record_decision(c.cycle_id, "scale up provider")
        assert len(c.decisions_made) == 1

    def test_record_action(self):
        mem = self._make()
        c = mem.begin_cycle()
        assert mem.record_action(c.cycle_id, "scaled provider to 3 instances")
        assert len(c.actions_taken) == 1

    def test_record_deferral(self):
        mem = self._make()
        c = mem.begin_cycle()
        assert mem.record_deferral(c.cycle_id, "code refactor — not urgent")
        assert len(c.deferrals) == 1

    def test_record_reflection(self):
        mem = self._make()
        c = mem.begin_cycle()
        assert mem.record_reflection(c.cycle_id, "productive cycle")
        assert len(c.reflections) == 1

    def test_end_cycle(self):
        mem = self._make()
        c = mem.begin_cycle()
        mem.record_observation(c.cycle_id, "observed something")
        assert mem.end_cycle(c.cycle_id) is True
        assert c.finalized is True
        assert c.ended_at != ""
        assert c.duration_ms >= 0

    def test_cannot_record_after_finalize(self):
        mem = self._make()
        c = mem.begin_cycle()
        mem.end_cycle(c.cycle_id)
        assert mem.record_observation(c.cycle_id, "late") is False
        assert mem.record_decision(c.cycle_id, "late") is False
        assert mem.record_action(c.cycle_id, "late") is False
        assert mem.record_deferral(c.cycle_id, "late") is False

    def test_context_inheritance(self):
        from src.kortana.services.cycle_memory import CycleContext
        mem = self._make()

        # Cycle 1: bequeath some context
        c1 = mem.begin_cycle()
        mem.record_deferral(c1.cycle_id, "refactor code")
        bequeath = CycleContext(
            pending_deferrals=["refactor code"],
            active_concerns=["latency rising"],
            health_state="healthy",
        )
        mem.end_cycle(c1.cycle_id, bequeath)

        # Cycle 2: should inherit
        c2 = mem.begin_cycle()
        assert "refactor code" in c2.context_inherited.pending_deferrals
        assert "latency rising" in c2.context_inherited.active_concerns
        assert c2.context_inherited.health_state == "healthy"

    def test_auto_bequeath_deferrals(self):
        mem = self._make()
        c1 = mem.begin_cycle()
        mem.record_deferral(c1.cycle_id, "upgrade dependency")
        mem.end_cycle(c1.cycle_id)  # no explicit bequeath

        # Autobequeathment carries forward deferrals
        c2 = mem.begin_cycle()
        assert "upgrade dependency" in c2.context_inherited.pending_deferrals

    def test_unfinalized_cycle_inheritance(self):
        mem = self._make()
        c1 = mem.begin_cycle()
        mem.record_deferral(c1.cycle_id, "important task")
        # Do NOT finalize c1

        c2 = mem.begin_cycle()
        assert "important task" in c2.context_inherited.pending_deferrals
        assert "previous cycle did not finalize" in c2.context_inherited.active_concerns

    def test_get_cycle(self):
        mem = self._make()
        c = mem.begin_cycle()
        found = mem.get_cycle(c.cycle_id)
        assert found is not None
        assert found.cycle_id == c.cycle_id

    def test_get_recent(self):
        mem = self._make()
        for _ in range(5):
            mem.begin_cycle()
        recent = mem.get_recent(3)
        assert len(recent) == 3
        assert recent[0].cycle_number == 5

    def test_last_cycle(self):
        mem = self._make()
        assert mem.last_cycle is None
        c = mem.begin_cycle()
        assert mem.last_cycle is c

    def test_get_inherited_context(self):
        from src.kortana.services.cycle_memory import CycleContext
        mem = self._make()
        assert mem.get_inherited_context() is None

        c = mem.begin_cycle()
        mem.end_cycle(c.cycle_id, CycleContext(health_state="thriving"))
        ctx = mem.get_inherited_context()
        assert ctx is not None
        assert ctx.health_state == "thriving"

    def test_deferral_streak(self):
        mem = self._make()
        for i in range(4):
            c = mem.begin_cycle()
            mem.record_deferral(c.cycle_id, "persistent issue")
            mem.end_cycle(c.cycle_id)

        assert mem.get_deferral_streak("persistent issue") == 4
        assert mem.get_deferral_streak("nonexistent") == 0

    def test_total_counts(self):
        mem = self._make()
        c1 = mem.begin_cycle()
        mem.record_observation(c1.cycle_id, "a")
        mem.record_observation(c1.cycle_id, "b")
        mem.record_decision(c1.cycle_id, "d")
        mem.record_deferral(c1.cycle_id, "f")
        mem.end_cycle(c1.cycle_id)

        assert mem.total_observations == 2
        assert mem.total_decisions == 1
        assert mem.total_deferrals == 1

    def test_cycle_hash(self):
        mem = self._make()
        c = mem.begin_cycle()
        assert len(c.cycle_hash) == 16

    def test_cycle_to_dict(self):
        mem = self._make()
        c = mem.begin_cycle()
        mem.record_observation(c.cycle_id, "obs1")
        data = c.to_dict()
        assert data["cycle_number"] == 1
        assert "obs1" in data["observations"]
        assert "context_inherited" in data

    def test_context_to_dict_from_dict(self):
        from src.kortana.services.cycle_memory import CycleContext
        ctx = CycleContext(
            pending_deferrals=["a", "b"],
            active_concerns=["c"],
            health_state="strained",
        )
        data = ctx.to_dict()
        restored = CycleContext.from_dict(data)
        assert restored.pending_deferrals == ["a", "b"]
        assert restored.health_state == "strained"

    def test_summary(self):
        mem = self._make()
        c = mem.begin_cycle()
        mem.record_observation(c.cycle_id, "x")
        mem.end_cycle(c.cycle_id)
        summary = mem.get_summary()
        assert summary["cycle_count"] == 1
        assert summary["finalized_cycles"] == 1
        assert summary["total_observations"] == 1

    def test_module_singleton(self):
        from src.kortana.services.cycle_memory import get_cycle_memory
        m1 = get_cycle_memory()
        m2 = get_cycle_memory()
        assert m1 is m2


# ═══════════════════════════════════════════════════════════════════════════════
# V26C: Health Assessor Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestHealthAssessor:
    """Tests for multi-dimensional health assessment."""

    def _make(self):
        from src.kortana.services.health_assessor import HealthAssessor
        return HealthAssessor()

    def test_assess_healthy_system(self):
        from src.kortana.services.health_assessor import HealthLevel
        assessor = self._make()
        snapshot = assessor.assess(
            cycle_number=10,
            beat_count=10,
            uptime_beats=10,
            avg_duration_ms=500,
            total_observations=30,
            total_decisions=20,
            total_deferrals=2,
            total_actions=15,
            cycle_count=10,
            finalized_cycles=10,
        )
        assert snapshot.overall_level in (HealthLevel.THRIVING, HealthLevel.HEALTHY)
        assert snapshot.overall_score >= 60
        assert snapshot.snapshot_id.startswith("health-")

    def test_assess_degraded_system(self):
        assessor = self._make()
        snapshot = assessor.assess(
            cycle_number=10,
            beat_count=10,
            uptime_beats=3,  # low uptime
            avg_duration_ms=15000,  # slow
            total_observations=5,
            total_decisions=3,
            total_deferrals=20,  # high deferrals
            total_actions=1,
            cycle_count=10,
            finalized_cycles=4,  # many unfinalized
            deferral_streak=6,  # persistent
        )
        assert snapshot.overall_score < 60
        assert len(snapshot.anomalies) > 0
        assert len(snapshot.recommendations) > 0

    def test_assess_no_data(self):
        assessor = self._make()
        snapshot = assessor.assess()
        # Should not crash with all zeros
        assert snapshot.overall_score >= 0

    def test_continuity_dimension(self):
        assessor = self._make()
        snapshot = assessor.assess(beat_count=10, uptime_beats=10, cycle_count=10, finalized_cycles=10)
        dim = snapshot.dimensions["continuity"]
        assert dim.score >= 90

    def test_coherence_dimension(self):
        assessor = self._make()
        # Many deferrals relative to decisions
        snapshot = assessor.assess(total_decisions=5, total_deferrals=15)
        dim = snapshot.dimensions["coherence"]
        assert dim.score < 50

    def test_responsiveness_dimension(self):
        assessor = self._make()
        snapshot = assessor.assess(avg_duration_ms=100, beat_count=5)
        dim = snapshot.dimensions["responsiveness"]
        assert dim.score >= 90

    def test_capacity_dimension(self):
        assessor = self._make()
        snapshot = assessor.assess(
            total_observations=50, total_decisions=30,
            total_actions=20, cycle_count=10
        )
        dim = snapshot.dimensions["capacity"]
        assert dim.score >= 80

    def test_governance_dimension(self):
        assessor = self._make()
        snapshot = assessor.assess(cycle_count=10, finalized_cycles=10)
        dim = snapshot.dimensions["governance"]
        assert dim.score >= 90

    def test_learning_dimension_with_streak(self):
        assessor = self._make()
        snapshot = assessor.assess(
            cycle_count=10, total_deferrals=15, deferral_streak=7
        )
        dim = snapshot.dimensions["learning"]
        assert dim.score < 50

    def test_get_snapshot(self):
        assessor = self._make()
        s = assessor.assess(beat_count=1, uptime_beats=1)
        found = assessor.get_snapshot(s.snapshot_id)
        assert found is not None

    def test_get_recent(self):
        assessor = self._make()
        for i in range(5):
            assessor.assess(cycle_number=i + 1, beat_count=i + 1, uptime_beats=i + 1)
        recent = assessor.get_recent(3)
        assert len(recent) == 3

    def test_get_trends(self):
        assessor = self._make()
        for i in range(5):
            assessor.assess(
                cycle_number=i + 1,
                beat_count=i + 1,
                uptime_beats=i + 1,
            )
        trends = assessor.get_trends("continuity", 5)
        assert len(trends) == 5
        assert "score" in trends[0]

    def test_snapshot_hash(self):
        assessor = self._make()
        s = assessor.assess()
        assert len(s.snapshot_hash) == 16

    def test_snapshot_to_dict(self):
        assessor = self._make()
        s = assessor.assess(beat_count=5, uptime_beats=5, cycle_count=5, finalized_cycles=5)
        data = s.to_dict()
        assert "overall_level" in data
        assert "dimensions" in data
        assert "continuity" in data["dimensions"]

    def test_dimension_to_dict(self):
        assessor = self._make()
        s = assessor.assess(beat_count=5, uptime_beats=5)
        dim_data = s.dimensions["continuity"].to_dict()
        assert "dimension" in dim_data
        assert "score" in dim_data
        assert "level" in dim_data

    def test_summary(self):
        assessor = self._make()
        assessor.assess(beat_count=5, uptime_beats=5)
        summary = assessor.get_summary()
        assert summary["snapshot_count"] == 1
        assert "current_level" in summary

    def test_module_singleton(self):
        from src.kortana.services.health_assessor import get_health_assessor
        h1 = get_health_assessor()
        h2 = get_health_assessor()
        assert h1 is h2


# ═══════════════════════════════════════════════════════════════════════════════
# V26D: Graceful Degradation Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestGracefulDegradation:
    """Tests for adaptive degradation mode management."""

    def _make(self):
        from src.kortana.services.graceful_degradation import GracefulDegradation
        return GracefulDegradation()

    def test_initial_state(self):
        from src.kortana.services.graceful_degradation import DegradationMode
        gd = self._make()
        assert gd.current_mode == DegradationMode.FULL_OPERATION
        assert gd.is_operational
        assert not gd.is_degraded

    def test_evaluate_healthy(self):
        from src.kortana.services.graceful_degradation import DegradationMode
        gd = self._make()
        mode = gd.evaluate(85.0, anomaly_count=0)
        assert mode == DegradationMode.FULL_OPERATION

    def test_evaluate_moderate_degradation(self):
        from src.kortana.services.graceful_degradation import DegradationMode
        gd = self._make()
        mode = gd.evaluate(55.0, anomaly_count=1)
        assert mode == DegradationMode.REDUCED_SCOPE

    def test_evaluate_severe_degradation(self):
        from src.kortana.services.graceful_degradation import DegradationMode
        gd = self._make()
        mode = gd.evaluate(35.0, anomaly_count=3)
        assert mode == DegradationMode.ESSENTIAL_ONLY

    def test_evaluate_critical(self):
        from src.kortana.services.graceful_degradation import DegradationMode
        gd = self._make()
        mode = gd.evaluate(15.0, anomaly_count=5)
        assert mode == DegradationMode.SAFE_MODE

    def test_evaluate_suspended(self):
        from src.kortana.services.graceful_degradation import DegradationMode
        gd = self._make()
        mode = gd.evaluate(5.0, anomaly_count=6)
        assert mode == DegradationMode.SUSPENDED

    def test_enter_mode(self):
        from src.kortana.services.graceful_degradation import (
            DegradationMode,
            DegradationTrigger,
        )
        gd = self._make()
        record = gd.enter_mode(
            DegradationMode.SAFE_MODE,
            DegradationTrigger.MANUAL_OVERRIDE,
            "testing safe mode",
        )
        assert gd.current_mode == DegradationMode.SAFE_MODE
        assert record.previous_mode == DegradationMode.FULL_OPERATION

    def test_restore(self):
        from src.kortana.services.graceful_degradation import (
            DegradationMode,
            DegradationTrigger,
        )
        gd = self._make()
        gd.enter_mode(DegradationMode.ESSENTIAL_ONLY,
                      DegradationTrigger.HEALTH_DEGRADED, "test")
        record = gd.restore("conditions improved")
        assert gd.current_mode == DegradationMode.FULL_OPERATION
        assert record.trigger == DegradationTrigger.HEALTH_RECOVERED

    def test_automatic_recovery(self):
        from src.kortana.services.graceful_degradation import DegradationMode
        gd = self._make()
        # Degrade
        gd.evaluate(25.0, anomaly_count=3)
        assert gd.is_degraded
        # Recover
        gd.evaluate(85.0, anomaly_count=0)
        assert gd.current_mode == DegradationMode.FULL_OPERATION
        assert not gd.is_degraded

    def test_capability_check_full(self):
        gd = self._make()
        assert gd.is_allowed("observe")
        assert gd.is_allowed("decide")
        assert gd.is_allowed("act")
        assert gd.is_allowed("mutations")
        assert gd.is_allowed("external_calls")

    def test_capability_check_safe_mode(self):
        from src.kortana.services.graceful_degradation import (
            DegradationMode,
            DegradationTrigger,
        )
        gd = self._make()
        gd.enter_mode(DegradationMode.SAFE_MODE,
                      DegradationTrigger.HEALTH_DEGRADED, "test")
        assert gd.is_allowed("observe")
        assert gd.is_allowed("reflect")
        assert not gd.is_allowed("act")
        assert not gd.is_allowed("mutations")

    def test_capability_check_suspended(self):
        from src.kortana.services.graceful_degradation import (
            DegradationMode,
            DegradationTrigger,
        )
        gd = self._make()
        gd.enter_mode(DegradationMode.SUSPENDED,
                      DegradationTrigger.HEALTH_DEGRADED, "critical")
        assert gd.is_allowed("observe")
        assert not gd.is_allowed("decide")
        assert not gd.is_allowed("act")

    def test_get_allowed_capabilities(self):
        from src.kortana.services.graceful_degradation import (
            DegradationMode,
            DegradationTrigger,
        )
        gd = self._make()
        caps = gd.get_allowed_capabilities()
        assert "observe" in caps
        assert "mutations" in caps

        gd.enter_mode(DegradationMode.ESSENTIAL_ONLY,
                      DegradationTrigger.HEALTH_DEGRADED, "test")
        caps = gd.get_allowed_capabilities()
        assert "observe" in caps
        assert "governance" in caps
        assert "mutations" not in caps

    def test_transition_history(self):
        from src.kortana.services.graceful_degradation import (
            DegradationMode,
            DegradationTrigger,
        )
        gd = self._make()
        gd.enter_mode(DegradationMode.REDUCED_SCOPE,
                      DegradationTrigger.HEALTH_DEGRADED, "r1")
        gd.enter_mode(DegradationMode.ESSENTIAL_ONLY,
                      DegradationTrigger.HEALTH_DEGRADED, "r2")
        gd.restore("ok")
        history = gd.get_history()
        assert len(history) == 3

    def test_escalation_count(self):
        from src.kortana.services.graceful_degradation import (
            DegradationMode,
            DegradationTrigger,
        )
        gd = self._make()
        gd.enter_mode(DegradationMode.REDUCED_SCOPE,
                      DegradationTrigger.HEALTH_DEGRADED, "r1")
        gd.enter_mode(DegradationMode.ESSENTIAL_ONLY,
                      DegradationTrigger.SUBSYSTEM_DOWN, "r2")
        gd.restore("ok")
        assert gd.escalation_count == 2
        assert gd.recovery_count == 1

    def test_degradation_record_to_dict(self):
        from src.kortana.services.graceful_degradation import (
            DegradationMode,
            DegradationTrigger,
        )
        gd = self._make()
        record = gd.enter_mode(DegradationMode.SAFE_MODE,
                               DegradationTrigger.GOVERNANCE_FAILURE, "gov failed")
        data = record.to_dict()
        assert data["mode"] == "safe_mode"
        assert data["trigger"] == "governance_failure"

    def test_degradation_hash(self):
        from src.kortana.services.graceful_degradation import (
            DegradationMode,
            DegradationTrigger,
        )
        gd = self._make()
        record = gd.enter_mode(DegradationMode.REDUCED_SCOPE,
                               DegradationTrigger.HEALTH_DEGRADED, "test")
        assert len(record.degradation_hash) == 16

    def test_summary(self):
        gd = self._make()
        summary = gd.get_summary()
        assert summary["current_mode"] == "full_operation"
        assert summary["is_operational"] is True
        assert summary["transition_count"] == 0

    def test_module_singleton(self):
        from src.kortana.services.graceful_degradation import get_graceful_degradation
        g1 = get_graceful_degradation()
        g2 = get_graceful_degradation()
        assert g1 is g2


# ═══════════════════════════════════════════════════════════════════════════════
# V26 Pipeline: Living Process Integration
# ═══════════════════════════════════════════════════════════════════════════════


class TestV26Pipeline:
    """Integration tests for the heartbeat/cycle/health/degradation pipeline."""

    def test_full_living_cycle(self):
        """End-to-end: heartbeat → cycle memory → health assessment → degradation check."""
        from src.kortana.services.cycle_memory import CycleContext, CycleMemory
        from src.kortana.services.graceful_degradation import (
            DegradationMode,
            GracefulDegradation,
        )
        from src.kortana.services.health_assessor import HealthAssessor, HealthLevel
        from src.kortana.services.heartbeat_loop import HeartbeatLoop

        loop = HeartbeatLoop()
        mem = CycleMemory()
        assessor = HealthAssessor()
        degradation = GracefulDegradation()

        # Simulate 3 healthy heartbeat cycles
        for i in range(3):
            # Start heartbeat
            beat = loop.begin_beat()
            cycle = mem.begin_cycle()

            # Observe phase
            loop.add_observation(beat.beat_id, "health", "systems nominal")
            mem.record_observation(cycle.cycle_id, "all systems nominal")

            # Decide phase
            loop.add_decision(beat.beat_id, "continue", "no issues detected")
            mem.record_decision(cycle.cycle_id, "continue normal ops")

            # Act phase
            loop.record_action(beat.beat_id, "performed routine check")
            mem.record_action(cycle.cycle_id, "routine check completed")

            # Reflect phase
            loop.add_reflection(beat.beat_id, f"cycle {i + 1} was nominal")
            mem.record_reflection(cycle.cycle_id, f"cycle {i + 1} nominal")

            # Complete
            loop.complete_beat(beat.beat_id)
            mem.end_cycle(cycle.cycle_id, CycleContext(health_state="healthy"))

        # Health assessment
        loop_summary = loop.get_summary()
        mem_summary = mem.get_summary()
        snapshot = assessor.assess(
            cycle_number=loop_summary["cycle_number"],
            beat_count=loop_summary["beat_count"],
            uptime_beats=loop_summary["uptime_beats"],
            avg_duration_ms=loop_summary["avg_duration_ms"],
            total_observations=loop_summary["total_observations"],
            total_decisions=mem_summary["total_decisions"],
            total_deferrals=mem_summary["total_deferrals"],
            cycle_count=mem_summary["cycle_count"],
            finalized_cycles=mem_summary["finalized_cycles"],
        )
        assert snapshot.overall_level in (HealthLevel.THRIVING, HealthLevel.HEALTHY)

        # Degradation check
        mode = degradation.evaluate(snapshot.overall_score, len(snapshot.anomalies))
        assert mode == DegradationMode.FULL_OPERATION
        assert degradation.is_operational

    def test_degradation_and_recovery_cycle(self):
        """System detects poor health, degrades, then recovers."""
        from src.kortana.services.graceful_degradation import (
            DegradationMode,
            GracefulDegradation,
        )
        from src.kortana.services.health_assessor import HealthAssessor

        assessor = HealthAssessor()
        degradation = GracefulDegradation()

        # Unhealthy assessment
        bad = assessor.assess(
            beat_count=10, uptime_beats=3,
            avg_duration_ms=20000,
            total_decisions=5, total_deferrals=30,
            cycle_count=10, finalized_cycles=3,
            deferral_streak=8,
        )
        mode = degradation.evaluate(bad.overall_score, len(bad.anomalies))
        assert degradation.is_degraded
        assert not degradation.is_allowed("mutations")

        # Recovery assessment
        good = assessor.assess(
            beat_count=20, uptime_beats=20,
            avg_duration_ms=200,
            total_decisions=40, total_deferrals=2,
            cycle_count=20, finalized_cycles=20,
        )
        mode = degradation.evaluate(good.overall_score, len(good.anomalies))
        assert mode == DegradationMode.FULL_OPERATION
        assert degradation.is_operational
        assert degradation.recovery_count >= 1

    def test_context_carries_forward_across_cycles(self):
        """Context bequeathed from one cycle is inherited by the next."""
        from src.kortana.services.cycle_memory import CycleContext, CycleMemory

        mem = CycleMemory()

        # Cycle 1: observe concern, defer action
        c1 = mem.begin_cycle()
        mem.record_observation(c1.cycle_id, "latency spike detected")
        mem.record_deferral(c1.cycle_id, "investigate latency — need more data")
        mem.end_cycle(c1.cycle_id, CycleContext(
            pending_deferrals=["investigate latency"],
            active_concerns=["latency spike"],
            health_state="strained",
        ))

        # Cycle 2: inherits concerns
        c2 = mem.begin_cycle()
        assert "investigate latency" in c2.context_inherited.pending_deferrals
        assert "latency spike" in c2.context_inherited.active_concerns
        assert c2.context_inherited.health_state == "strained"

        # Address the concern
        mem.record_action(c2.cycle_id, "investigated latency — found slow query")
        mem.end_cycle(c2.cycle_id, CycleContext(
            pending_deferrals=[],
            active_concerns=[],
            health_state="healthy",
        ))

        # Cycle 3: clean slate
        c3 = mem.begin_cycle()
        assert len(c3.context_inherited.pending_deferrals) == 0
        assert c3.context_inherited.health_state == "healthy"

    def test_capability_gating_across_modes(self):
        """Capabilities are correctly gated as modes change."""
        from src.kortana.services.graceful_degradation import (
            DegradationMode,
            DegradationTrigger,
            GracefulDegradation,
        )

        gd = GracefulDegradation()

        # Full: everything allowed
        assert gd.is_allowed("mutations")
        assert gd.is_allowed("external_calls")

        # Reduced: no mutations or external
        gd.enter_mode(DegradationMode.REDUCED_SCOPE,
                      DegradationTrigger.HEALTH_DEGRADED, "moderate issues")
        assert gd.is_allowed("observe")
        assert gd.is_allowed("act")
        assert not gd.is_allowed("mutations")
        assert not gd.is_allowed("external_calls")

        # Essential: no act
        gd.enter_mode(DegradationMode.ESSENTIAL_ONLY,
                      DegradationTrigger.HEALTH_DEGRADED, "serious issues")
        assert gd.is_allowed("observe")
        assert gd.is_allowed("governance")
        assert not gd.is_allowed("act")

        # Restore
        gd.restore("all clear")
        assert gd.is_allowed("mutations")
        assert gd.is_allowed("external_calls")
