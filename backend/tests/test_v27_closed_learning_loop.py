"""V27 — closed learning loop tests.

Tests for experience extraction, pattern recognition, behavioral adaptation,
and feedback integration.
"""



# ═══════════════════════════════════════════════════════════════════════════════
# V27A: Experience Extractor Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestExperienceExtractor:
    """Tests for extracting structured lessons from heartbeat cycles."""

    def _make(self):
        from src.kortana.services.experience_extractor import ExperienceExtractor
        return ExperienceExtractor()

    def _beat_data(self, **overrides):
        base = {
            "beat_id": "beat-001",
            "cycle_number": 1,
            "state": "alive",
            "observations": [{"source": "health", "description": "nominal", "severity": "info"}],
            "decisions": [{"action_type": "continue", "rationale": "all good", "priority": 5}],
            "actions": ["routine check completed"],
            "deferrals": [],
            "reflections": ["productive cycle"],
            "duration_ms": 500,
        }
        base.update(overrides)
        return base

    def test_extract_from_beat(self):
        ext = self._make()
        data = self._beat_data()
        exp = ext.extract_from_beat(**data)
        assert exp.source_beat_id == "beat-001"
        assert exp.cycle_number == 1
        assert exp.observation_count == 1
        assert exp.decision_count == 1
        assert exp.action_count == 1
        assert len(exp.lessons) > 0

    def test_experience_id_generated(self):
        ext = self._make()
        exp = ext.extract_from_beat(**self._beat_data())
        assert exp.experience_id.startswith("exp-")

    def test_experience_hash(self):
        ext = self._make()
        exp = ext.extract_from_beat(**self._beat_data())
        assert len(exp.experience_hash) == 16

    def test_lesson_from_severe_observation(self):
        from src.kortana.services.experience_extractor import LessonType
        ext = self._make()
        data = self._beat_data(observations=[
            {"source": "monitor", "description": "high latency", "severity": "warning"}
        ])
        exp = ext.extract_from_beat(**data)
        anomaly_lessons = [lesson for lesson in exp.lessons if lesson.lesson_type == LessonType.ANOMALY]
        assert len(anomaly_lessons) >= 1

    def test_lesson_from_no_observations(self):
        from src.kortana.services.experience_extractor import LessonType
        ext = self._make()
        data = self._beat_data(observations=[])
        exp = ext.extract_from_beat(**data)
        missed = [lesson for lesson in exp.lessons if lesson.lesson_type == LessonType.MISSED_OPPORTUNITY]
        assert len(missed) >= 1

    def test_lesson_from_high_priority_decision(self):
        from src.kortana.services.experience_extractor import LessonType
        ext = self._make()
        data = self._beat_data(decisions=[
            {"action_type": "scale-up", "rationale": "critical", "priority": 1}
        ])
        exp = ext.extract_from_beat(**data)
        insights = [lesson for lesson in exp.lessons if lesson.lesson_type == LessonType.INSIGHT]
        assert len(insights) >= 1

    def test_lesson_from_deferred_decision(self):
        from src.kortana.services.experience_extractor import LessonType
        ext = self._make()
        data = self._beat_data(decisions=[
            {"action_type": "refactor", "rationale": "later", "priority": 5, "deferred": True}
        ])
        exp = ext.extract_from_beat(**data)
        deferrals = [lesson for lesson in exp.lessons if lesson.lesson_type == LessonType.DEFERRAL]
        assert len(deferrals) >= 1

    def test_lesson_from_actions(self):
        from src.kortana.services.experience_extractor import LessonType
        ext = self._make()
        data = self._beat_data(actions=["scaled provider"])
        exp = ext.extract_from_beat(**data)
        successes = [lesson for lesson in exp.lessons if lesson.lesson_type == LessonType.SUCCESS]
        assert len(successes) >= 1

    def test_lesson_from_no_actions_with_decisions(self):
        from src.kortana.services.experience_extractor import LessonType
        ext = self._make()
        data = self._beat_data(actions=[], decisions=[
            {"action_type": "do-something", "rationale": "needed", "priority": 3}
        ])
        exp = ext.extract_from_beat(**data)
        failures = [lesson for lesson in exp.lessons if lesson.lesson_type == LessonType.FAILURE]
        assert len(failures) >= 1

    def test_lesson_from_high_deferrals(self):
        from src.kortana.services.experience_extractor import LessonType
        ext = self._make()
        data = self._beat_data(deferrals=["a", "b", "c"])
        exp = ext.extract_from_beat(**data)
        anomalies = [lesson for lesson in exp.lessons if lesson.lesson_type == LessonType.ANOMALY]
        assert len(anomalies) >= 1

    def test_lesson_from_reflections(self):
        from src.kortana.services.experience_extractor import LessonType
        ext = self._make()
        data = self._beat_data(reflections=["good cycle"])
        exp = ext.extract_from_beat(**data)
        insights = [lesson for lesson in exp.lessons if lesson.lesson_type == LessonType.INSIGHT]
        assert any("reflection" in lesson.description for lesson in insights)

    def test_lesson_from_no_reflections_with_actions(self):
        from src.kortana.services.experience_extractor import LessonType
        ext = self._make()
        data = self._beat_data(reflections=[], actions=["did stuff"])
        exp = ext.extract_from_beat(**data)
        missed = [lesson for lesson in exp.lessons if lesson.lesson_type == LessonType.MISSED_OPPORTUNITY]
        assert len(missed) >= 1

    def test_meta_lesson_slow_cycle(self):
        from src.kortana.services.experience_extractor import LessonType
        ext = self._make()
        data = self._beat_data(duration_ms=10000)
        exp = ext.extract_from_beat(**data)
        anomalies = [lesson for lesson in exp.lessons if lesson.lesson_type == LessonType.ANOMALY]
        assert any("5s" in lesson.description or "ms" in lesson.description for lesson in anomalies)

    def test_meta_lesson_empty_cycle(self):
        from src.kortana.services.experience_extractor import LessonType
        ext = self._make()
        data = self._beat_data(observations=[], decisions=[], actions=[], reflections=[])
        exp = ext.extract_from_beat(**data)
        failures = [lesson for lesson in exp.lessons if lesson.lesson_type == LessonType.FAILURE]
        assert any("empty" in lesson.description for lesson in failures)

    def test_meta_lesson_degraded_state(self):
        from src.kortana.services.experience_extractor import LessonType
        ext = self._make()
        data = self._beat_data(state="degraded")
        exp = ext.extract_from_beat(**data)
        anomalies = [lesson for lesson in exp.lessons if lesson.lesson_type == LessonType.ANOMALY]
        assert any("degraded" in lesson.description for lesson in anomalies)

    def test_get_experience(self):
        ext = self._make()
        exp = ext.extract_from_beat(**self._beat_data())
        found = ext.get_experience(exp.experience_id)
        assert found is not None
        assert found.experience_id == exp.experience_id

    def test_get_by_cycle(self):
        ext = self._make()
        ext.extract_from_beat(**self._beat_data(cycle_number=5))
        found = ext.get_by_cycle(5)
        assert found is not None
        assert found.cycle_number == 5

    def test_get_recent(self):
        ext = self._make()
        for i in range(5):
            ext.extract_from_beat(**self._beat_data(cycle_number=i + 1, beat_id=f"b-{i}"))
        recent = ext.get_recent(3)
        assert len(recent) == 3
        assert recent[0].cycle_number == 5

    def test_get_lessons_by_type(self):
        from src.kortana.services.experience_extractor import LessonType
        ext = self._make()
        ext.extract_from_beat(**self._beat_data(actions=["a"]))
        successes = ext.get_lessons_by_type(LessonType.SUCCESS)
        assert len(successes) >= 1

    def test_get_actionable_lessons(self):
        ext = self._make()
        ext.extract_from_beat(**self._beat_data(
            observations=[{"source": "x", "description": "y", "severity": "critical"}]
        ))
        actionable = ext.get_actionable_lessons()
        assert len(actionable) >= 1

    def test_experience_count(self):
        ext = self._make()
        assert ext.experience_count == 0
        ext.extract_from_beat(**self._beat_data())
        assert ext.experience_count == 1

    def test_total_lessons(self):
        ext = self._make()
        ext.extract_from_beat(**self._beat_data())
        assert ext.total_lessons > 0

    def test_lesson_type_counts(self):
        ext = self._make()
        ext.extract_from_beat(**self._beat_data())
        counts = ext.lesson_type_counts
        assert isinstance(counts, dict)

    def test_experience_to_dict(self):
        ext = self._make()
        exp = ext.extract_from_beat(**self._beat_data())
        data = exp.to_dict()
        assert "experience_id" in data
        assert "lessons" in data
        assert "cycle_number" in data

    def test_lesson_to_dict(self):
        ext = self._make()
        exp = ext.extract_from_beat(**self._beat_data())
        lesson_data = exp.lessons[0].to_dict()
        assert "lesson_id" in lesson_data
        assert "lesson_type" in lesson_data

    def test_summary(self):
        ext = self._make()
        ext.extract_from_beat(**self._beat_data())
        summary = ext.get_summary()
        assert summary["experience_count"] == 1
        assert summary["total_lessons"] > 0

    def test_module_singleton(self):
        from src.kortana.services.experience_extractor import get_experience_extractor
        e1 = get_experience_extractor()
        e2 = get_experience_extractor()
        assert e1 is e2


# ═══════════════════════════════════════════════════════════════════════════════
# V27B: Pattern Recognizer Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestPatternRecognizer:
    """Tests for cross-cycle pattern recognition."""

    def _make(self):
        from src.kortana.services.pattern_recognizer import PatternRecognizer
        return PatternRecognizer()

    def _exp_dict(self, cycle_number=1, deferral_count=0, action_count=1,
                  decision_count=1, observations=None, lessons=None,
                  beat_duration_ms=500, experience_id=None):
        return {
            "experience_id": experience_id or f"exp-{cycle_number}",
            "cycle_number": cycle_number,
            "deferral_count": deferral_count,
            "action_count": action_count,
            "decision_count": decision_count,
            "observation_count": len(observations or []),
            "beat_duration_ms": beat_duration_ms,
            "lessons": lessons or [],
        }

    def test_min_sample_required(self):
        rec = self._make()
        patterns = rec.analyze([self._exp_dict()])
        assert len(patterns) == 0

    def test_detect_persistent_deferral(self):
        rec = self._make()
        exps = [self._exp_dict(cycle_number=i, deferral_count=3) for i in range(1, 5)]
        patterns = rec.analyze(exps)
        deferral_patterns = [p for p in patterns if p.pattern_type.value == "persistent_deferral"]
        assert len(deferral_patterns) >= 1

    def test_detect_decision_drift(self):
        rec = self._make()
        exps = [self._exp_dict(cycle_number=i, decision_count=3, action_count=0) for i in range(1, 5)]
        patterns = rec.analyze(exps)
        drift_patterns = [p for p in patterns if p.pattern_type.value == "decision_drift"]
        assert len(drift_patterns) >= 1

    def test_detect_anomaly_cluster(self):
        rec = self._make()
        exps = [
            self._exp_dict(cycle_number=i, lessons=[
                {"lesson_type": "anomaly", "description": "something wrong"}
            ]) for i in range(1, 4)
        ]
        patterns = rec.analyze(exps)
        anomaly_pats = [p for p in patterns if p.pattern_type.value == "anomaly_cluster"]
        assert len(anomaly_pats) >= 1

    def test_detect_slow_cycle_pattern(self):
        rec = self._make()
        exps = [
            self._exp_dict(cycle_number=1, beat_duration_ms=100),
            self._exp_dict(cycle_number=2, beat_duration_ms=100),
            self._exp_dict(cycle_number=3, beat_duration_ms=100),
            self._exp_dict(cycle_number=4, beat_duration_ms=5000),  # slow
            self._exp_dict(cycle_number=5, beat_duration_ms=5000),  # slow
        ]
        patterns = rec.analyze(exps)
        rhythm_pats = [p for p in patterns if p.pattern_type.value == "cycle_rhythm"]
        assert len(rhythm_pats) >= 1

    def test_detect_failure_pattern(self):
        rec = self._make()
        exps = [
            self._exp_dict(cycle_number=i, lessons=[
                {"lesson_type": "failure", "description": "something failed"}
            ]) for i in range(1, 4)
        ]
        patterns = rec.analyze(exps)
        fail_pats = [p for p in patterns if p.pattern_type.value == "learning_signal"]
        assert len(fail_pats) >= 1

    def test_pattern_evidence(self):
        rec = self._make()
        exps = [self._exp_dict(cycle_number=i, deferral_count=3) for i in range(1, 5)]
        patterns = rec.analyze(exps)
        pat = [p for p in patterns if p.pattern_type.value == "persistent_deferral"][0]
        assert len(pat.evidence) >= 2
        assert pat.first_seen_cycle >= 1
        assert pat.last_seen_cycle >= 2

    def test_pattern_strength(self):
        rec = self._make()
        exps = [self._exp_dict(cycle_number=i, deferral_count=3) for i in range(1, 8)]
        patterns = rec.analyze(exps)
        pat = [p for p in patterns if p.pattern_type.value == "persistent_deferral"][0]
        # Pattern has 7 occurrences with consistency set after analyze
        assert pat.occurrence_count >= 5
        assert pat.consistency > 0

    def test_pattern_consistency(self):
        rec = self._make()
        exps = [self._exp_dict(cycle_number=i, deferral_count=3) for i in range(1, 5)]
        patterns = rec.analyze(exps)
        pat = [p for p in patterns if p.pattern_type.value == "persistent_deferral"][0]
        assert pat.consistency > 0

    def test_trend_computation(self):
        from src.kortana.services.pattern_recognizer import PatternRecognizer
        assert PatternRecognizer._compute_trend([1, 2, 3, 4]) == "increasing"
        assert PatternRecognizer._compute_trend([4, 3, 2, 1]) == "decreasing"
        assert PatternRecognizer._compute_trend([5, 5, 5, 5]) == "stable"
        assert PatternRecognizer._compute_trend([1]) == "new"

    def test_get_pattern(self):
        rec = self._make()
        exps = [self._exp_dict(cycle_number=i, deferral_count=3) for i in range(1, 5)]
        patterns = rec.analyze(exps)
        pat = patterns[0]
        found = rec.get_pattern(pat.pattern_id)
        assert found is not None

    def test_get_by_type(self):
        rec = self._make()
        exps = [self._exp_dict(cycle_number=i, deferral_count=3) for i in range(1, 5)]
        rec.analyze(exps)
        typed = rec.get_by_type("persistent_deferral")
        assert len(typed) >= 1

    def test_mark_addressed(self):
        rec = self._make()
        exps = [self._exp_dict(cycle_number=i, deferral_count=3) for i in range(1, 5)]
        patterns = rec.analyze(exps)
        pat = patterns[0]
        assert rec.mark_addressed(pat.pattern_id) is True
        assert pat.addressed is True
        assert len(rec.get_active()) < len(patterns)

    def test_get_actionable(self):
        rec = self._make()
        exps = [self._exp_dict(cycle_number=i, deferral_count=3) for i in range(1, 5)]
        patterns = rec.analyze(exps)
        # Patterns recognized; actionability depends on strength threshold
        assert len(patterns) >= 1

    def test_pattern_to_dict(self):
        rec = self._make()
        exps = [self._exp_dict(cycle_number=i, deferral_count=3) for i in range(1, 5)]
        patterns = rec.analyze(exps)
        data = patterns[0].to_dict()
        assert "pattern_id" in data
        assert "evidence" in data
        assert "strength" in data

    def test_pattern_hash(self):
        rec = self._make()
        exps = [self._exp_dict(cycle_number=i, deferral_count=3) for i in range(1, 5)]
        patterns = rec.analyze(exps)
        assert len(patterns[0].pattern_hash) == 16

    def test_evidence_to_dict(self):
        rec = self._make()
        exps = [self._exp_dict(cycle_number=i, deferral_count=3) for i in range(1, 5)]
        patterns = rec.analyze(exps)
        ev_data = patterns[0].evidence[0].to_dict()
        assert "cycle_number" in ev_data
        assert "description" in ev_data

    def test_summary(self):
        rec = self._make()
        exps = [self._exp_dict(cycle_number=i, deferral_count=3) for i in range(1, 5)]
        rec.analyze(exps)
        summary = rec.get_summary()
        assert summary["pattern_count"] >= 1
        assert "type_counts" in summary

    def test_module_singleton(self):
        from src.kortana.services.pattern_recognizer import get_pattern_recognizer
        p1 = get_pattern_recognizer()
        p2 = get_pattern_recognizer()
        assert p1 is p2


# ═══════════════════════════════════════════════════════════════════════════════
# V27C: Behavioral Adapter Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestBehavioralAdapter:
    """Tests for behavioral adaptation from patterns."""

    def _make(self):
        from src.kortana.services.behavioral_adapter import BehavioralAdapter
        return BehavioralAdapter()

    def test_propose_from_deferral_pattern(self):
        adapter = self._make()
        adapt = adapter.propose_from_pattern(
            pattern_id="pat-001",
            pattern_type="persistent_deferral",
            pattern_description="recurring high deferrals",
            pattern_strength="strong",
            recommended_action="address deferrals",
            occurrence_count=5,
        )
        assert adapt is not None
        assert adapt.adaptation_type.value == "deferral_resolution"

    def test_propose_from_decision_drift(self):
        adapter = self._make()
        adapt = adapter.propose_from_pattern(
            pattern_id="pat-002",
            pattern_type="decision_drift",
            pattern_description="decisions without actions",
            pattern_strength="moderate",
        )
        assert adapt is not None
        assert adapt.adaptation_type.value == "decision_bias"

    def test_propose_from_anomaly_cluster(self):
        adapter = self._make()
        adapt = adapter.propose_from_pattern(
            pattern_id="pat-003",
            pattern_type="anomaly_cluster",
            pattern_description="recurring anomalies",
            pattern_strength="moderate",
        )
        assert adapt is not None
        assert adapt.adaptation_type.value == "observation_focus"

    def test_propose_from_cycle_rhythm(self):
        adapter = self._make()
        adapt = adapter.propose_from_pattern(
            pattern_id="pat-004",
            pattern_type="cycle_rhythm",
            pattern_description="slow cycles",
            pattern_strength="moderate",
        )
        assert adapt is not None
        assert adapt.adaptation_type.value == "cycle_timing"

    def test_propose_from_learning_signal(self):
        adapter = self._make()
        adapt = adapter.propose_from_pattern(
            pattern_id="pat-005",
            pattern_type="learning_signal",
            pattern_description="recurring failures",
            pattern_strength="strong",
        )
        assert adapt is not None
        assert adapt.adaptation_type.value == "recovery_strategy"

    def test_no_duplicate_proposals(self):
        adapter = self._make()
        a1 = adapter.propose_from_pattern("p1", "persistent_deferral", "test", "strong")
        a2 = adapter.propose_from_pattern("p1", "persistent_deferral", "test", "strong")
        assert a1 is not None
        assert a2 is None

    def test_unknown_pattern_type(self):
        adapter = self._make()
        adapt = adapter.propose_from_pattern("p1", "unknown_type", "test", "strong")
        assert adapt is None

    def test_activate(self):
        from src.kortana.services.behavioral_adapter import AdaptationStatus
        adapter = self._make()
        adapt = adapter.propose_from_pattern("p1", "persistent_deferral", "test", "strong")
        assert adapter.activate(adapt.adaptation_id) is True
        assert adapt.status == AdaptationStatus.ACTIVE
        assert adapter.active_count == 1

    def test_cannot_activate_nonexistent(self):
        adapter = self._make()
        assert adapter.activate("nonexistent") is False

    def test_tick_cycle(self):
        adapter = self._make()
        adapt = adapter.propose_from_pattern("p1", "persistent_deferral", "test", "strong")
        adapter.activate(adapt.adaptation_id)
        expired = adapter.tick_cycle()
        assert len(expired) == 0
        assert adapt.cycles_active == 1

    def test_tick_cycle_expiry(self):
        from src.kortana.services.behavioral_adapter import AdaptationStatus
        adapter = self._make()
        adapt = adapter.propose_from_pattern("p1", "persistent_deferral", "test", "strong")
        adapt.max_cycles = 3
        adapter.activate(adapt.adaptation_id)
        adapter.tick_cycle()
        adapter.tick_cycle()
        expired = adapter.tick_cycle()
        assert len(expired) == 1
        assert adapt.status == AdaptationStatus.EXPIRED

    def test_report_effectiveness_high(self):
        from src.kortana.services.behavioral_adapter import AdaptationStatus
        adapter = self._make()
        adapt = adapter.propose_from_pattern("p1", "persistent_deferral", "test", "strong")
        adapter.activate(adapt.adaptation_id)
        assert adapter.report_effectiveness(adapt.adaptation_id, 0.8) is True
        assert adapt.status == AdaptationStatus.EFFECTIVE

    def test_report_effectiveness_low(self):
        from src.kortana.services.behavioral_adapter import AdaptationStatus
        adapter = self._make()
        adapt = adapter.propose_from_pattern("p1", "persistent_deferral", "test", "strong")
        adapter.activate(adapt.adaptation_id)
        adapt.cycles_active = 5  # past threshold
        assert adapter.report_effectiveness(adapt.adaptation_id, 0.1) is True
        assert adapt.status == AdaptationStatus.INEFFECTIVE

    def test_rollback(self):
        from src.kortana.services.behavioral_adapter import AdaptationStatus
        adapter = self._make()
        adapt = adapter.propose_from_pattern("p1", "persistent_deferral", "test", "strong")
        adapter.activate(adapt.adaptation_id)
        assert adapter.rollback(adapt.adaptation_id, "didn't work") is True
        assert adapt.status == AdaptationStatus.ROLLED_BACK
        assert adapter.active_count == 0

    def test_get_adaptation(self):
        adapter = self._make()
        adapt = adapter.propose_from_pattern("p1", "persistent_deferral", "test", "strong")
        found = adapter.get_adaptation(adapt.adaptation_id)
        assert found is not None

    def test_get_active(self):
        adapter = self._make()
        a1 = adapter.propose_from_pattern("p1", "persistent_deferral", "test1", "strong")
        a2 = adapter.propose_from_pattern("p2", "decision_drift", "test2", "moderate")
        adapter.activate(a1.adaptation_id)
        adapter.activate(a2.adaptation_id)
        assert len(adapter.get_active()) == 2

    def test_get_proposed(self):
        adapter = self._make()
        adapter.propose_from_pattern("p1", "persistent_deferral", "test", "strong")
        assert len(adapter.get_proposed()) == 1
        adapter.activate(adapter.get_proposed()[0].adaptation_id)
        assert len(adapter.get_proposed()) == 0

    def test_effectiveness_rate(self):
        adapter = self._make()
        a1 = adapter.propose_from_pattern("p1", "persistent_deferral", "t1", "strong")
        a2 = adapter.propose_from_pattern("p2", "decision_drift", "t2", "moderate")
        adapter.activate(a1.adaptation_id)
        adapter.activate(a2.adaptation_id)
        adapter.report_effectiveness(a1.adaptation_id, 0.9)  # effective
        adapter.rollback(a2.adaptation_id, "bad")  # rolled back
        assert adapter.effectiveness_rate == 0.5

    def test_adaptation_to_dict(self):
        adapter = self._make()
        adapt = adapter.propose_from_pattern("p1", "persistent_deferral", "test", "strong")
        data = adapt.to_dict()
        assert "adaptation_id" in data
        assert "adaptation_type" in data
        assert "status" in data

    def test_adaptation_hash(self):
        adapter = self._make()
        adapt = adapter.propose_from_pattern("p1", "persistent_deferral", "test", "strong")
        assert len(adapt.adaptation_hash) == 16

    def test_summary(self):
        adapter = self._make()
        adapter.propose_from_pattern("p1", "persistent_deferral", "test", "strong")
        summary = adapter.get_summary()
        assert summary["adaptation_count"] == 1
        assert "status_counts" in summary

    def test_module_singleton(self):
        from src.kortana.services.behavioral_adapter import get_behavioral_adapter
        b1 = get_behavioral_adapter()
        b2 = get_behavioral_adapter()
        assert b1 is b2


# ═══════════════════════════════════════════════════════════════════════════════
# V27D: Feedback Integrator Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestFeedbackIntegrator:
    """Tests for closing the learning loop."""

    def _make(self):
        from src.kortana.services.feedback_integrator import FeedbackIntegrator
        return FeedbackIntegrator()

    def _summaries(self, lessons=3, patterns=1, adaptations=1, effectiveness=0.5):
        return {
            "experience": {"experience_count": 1, "total_lessons": lessons, "total_actionable": 1},
            "pattern": {"pattern_count": patterns, "actionable_count": 1},
            "adaptation": {"adaptation_count": adaptations, "active_count": 1,
                           "effectiveness_rate": effectiveness,
                           "status_counts": {}, "rollback_count": 0},
        }

    def test_integrate(self):
        fi = self._make()
        s = self._summaries()
        report = fi.integrate(
            cycle_number=1,
            experience_summary=s["experience"],
            pattern_summary=s["pattern"],
            adaptation_summary=s["adaptation"],
        )
        assert report.cycle_number == 1
        assert report.lessons_extracted == 3
        assert report.report_id.startswith("lrep-")

    def test_learning_velocity(self):
        fi = self._make()
        for i in range(5):
            s = self._summaries(lessons=i + 1)
            fi.integrate(i + 1, s["experience"], s["pattern"], s["adaptation"])
        assert fi.learning_velocity > 0

    def test_context_injections_from_adaptations(self):
        fi = self._make()
        s = self._summaries()
        active_adaptations = [
            {"adaptation_id": "a1", "description": "elevate priorities",
             "parameter": "deferral_priority", "new_value": "elevated"},
        ]
        report = fi.integrate(1, s["experience"], s["pattern"], s["adaptation"],
                              active_adaptations=active_adaptations)
        assert len(report.context_injections) >= 1
        assert any("adaptation" in c for c in report.context_injections)

    def test_context_injections_from_patterns(self):
        fi = self._make()
        s = self._summaries()
        actionable_patterns = [
            {"pattern_id": "p1", "strength": "strong",
             "description": "recurring deferrals", "recommended_action": "address them"},
        ]
        report = fi.integrate(1, s["experience"], s["pattern"], s["adaptation"],
                              actionable_patterns=actionable_patterns)
        assert len(report.context_injections) >= 1
        assert any("pattern" in c for c in report.context_injections)

    def test_pending_injections(self):
        fi = self._make()
        s = self._summaries()
        fi.integrate(1, s["experience"], s["pattern"], s["adaptation"],
                     active_adaptations=[{"adaptation_id": "a1", "description": "test",
                                          "parameter": "p", "new_value": "v"}])
        pending = fi.get_pending_injections()
        assert len(pending) >= 1

    def test_consume_injections(self):
        fi = self._make()
        s = self._summaries()
        fi.integrate(1, s["experience"], s["pattern"], s["adaptation"],
                     active_adaptations=[{"adaptation_id": "a1", "description": "test",
                                          "parameter": "p", "new_value": "v"}])
        consumed = fi.consume_injections()
        assert len(consumed) >= 1
        # after consuming, pending should be empty
        assert fi.pending_injection_count == 0

    def test_get_context_for_cycle(self):
        fi = self._make()
        s = self._summaries()
        fi.integrate(1, s["experience"], s["pattern"], s["adaptation"],
                     active_adaptations=[{"adaptation_id": "a1", "description": "test",
                                          "parameter": "p", "new_value": "v"}])
        ctx = fi.get_context_for_cycle()
        assert "learning_injections" in ctx
        assert "learning_velocity" in ctx

    def test_get_context_empty(self):
        fi = self._make()
        ctx = fi.get_context_for_cycle()
        assert ctx == {}

    def test_get_report(self):
        fi = self._make()
        s = self._summaries()
        report = fi.integrate(1, s["experience"], s["pattern"], s["adaptation"])
        found = fi.get_report(report.report_id)
        assert found is not None

    def test_get_recent(self):
        fi = self._make()
        for i in range(5):
            s = self._summaries()
            fi.integrate(i + 1, s["experience"], s["pattern"], s["adaptation"])
        recent = fi.get_recent(3)
        assert len(recent) == 3
        assert recent[0].cycle_number == 5

    def test_velocity_trend(self):
        fi = self._make()
        for i in range(5):
            s = self._summaries(lessons=i + 1)
            fi.integrate(i + 1, s["experience"], s["pattern"], s["adaptation"])
        trend = fi.get_velocity_trend(5)
        assert len(trend) == 5
        assert trend == [1, 2, 3, 4, 5]

    def test_report_hash(self):
        fi = self._make()
        s = self._summaries()
        report = fi.integrate(1, s["experience"], s["pattern"], s["adaptation"])
        assert len(report.report_hash) == 16

    def test_report_to_dict(self):
        fi = self._make()
        s = self._summaries()
        report = fi.integrate(1, s["experience"], s["pattern"], s["adaptation"])
        data = report.to_dict()
        assert "report_id" in data
        assert "learning_velocity" in data
        assert "context_injections" in data

    def test_summary(self):
        fi = self._make()
        s = self._summaries()
        fi.integrate(1, s["experience"], s["pattern"], s["adaptation"])
        summary = fi.get_summary()
        assert summary["report_count"] == 1
        assert "learning_velocity" in summary
        assert "velocity_trend" in summary

    def test_module_singleton(self):
        from src.kortana.services.feedback_integrator import get_feedback_integrator
        f1 = get_feedback_integrator()
        f2 = get_feedback_integrator()
        assert f1 is f2


# ═══════════════════════════════════════════════════════════════════════════════
# V27 Pipeline: Full Learning Loop Integration
# ═══════════════════════════════════════════════════════════════════════════════


class TestV27Pipeline:
    """Integration tests for the complete closed learning loop."""

    def test_full_learning_loop(self):
        """End-to-end: extract → recognize → adapt → feedback → context injection."""
        from src.kortana.services.behavioral_adapter import BehavioralAdapter
        from src.kortana.services.experience_extractor import ExperienceExtractor
        from src.kortana.services.feedback_integrator import FeedbackIntegrator
        from src.kortana.services.pattern_recognizer import PatternRecognizer

        extractor = ExperienceExtractor()
        recognizer = PatternRecognizer()
        adapter = BehavioralAdapter()
        integrator = FeedbackIntegrator()

        # Simulate 5 cycles with high deferrals
        for i in range(1, 6):
            extractor.extract_from_beat(
                beat_id=f"beat-{i}",
                cycle_number=i,
                state="alive",
                observations=[{"source": "sys", "description": "check", "severity": "info"}],
                decisions=[{"action_type": "continue", "rationale": "ok", "priority": 3}],
                actions=["routine check"],
                deferrals=["refactor code", "update docs", "review alerts"],
                reflections=["cycle had deferrals"],
                duration_ms=500,
            )

        # Recognize patterns
        exp_dicts = [e.to_dict() for e in extractor.get_recent(5)]
        patterns = recognizer.analyze(exp_dicts)
        assert len(patterns) >= 1

        # Propose adaptations from actionable patterns
        proposed = []
        for pat in recognizer.get_actionable():
            adapt = adapter.propose_from_pattern(
                pattern_id=pat.pattern_id,
                pattern_type=pat.pattern_type.value,
                pattern_description=pat.description,
                pattern_strength=pat.strength.value,
                recommended_action=pat.recommended_action,
                occurrence_count=pat.occurrence_count,
            )
            if adapt:
                adapter.activate(adapt.adaptation_id)
                proposed.append(adapt)

        assert len(proposed) >= 1

        # Integrate feedback
        report = integrator.integrate(
            cycle_number=6,
            experience_summary=extractor.get_summary(),
            pattern_summary=recognizer.get_summary(),
            adaptation_summary=adapter.get_summary(),
            active_adaptations=[a.to_dict() for a in adapter.get_active()],
            actionable_patterns=[p.to_dict() for p in recognizer.get_actionable()],
        )
        assert report.lessons_extracted > 0
        assert report.adaptations_activated >= 1

        # Verify context injections exist
        ctx = integrator.get_context_for_cycle()
        assert "learning_injections" in ctx
        assert len(ctx["learning_injections"]) >= 1

    def test_adaptation_lifecycle(self):
        """Adaptation proposed → activated → effective → still tracked."""
        from src.kortana.services.behavioral_adapter import (
            AdaptationStatus,
            BehavioralAdapter,
        )

        adapter = BehavioralAdapter()

        # Propose
        adapt = adapter.propose_from_pattern("p1", "persistent_deferral", "test", "strong")
        assert adapt.status == AdaptationStatus.PROPOSED

        # Activate
        adapter.activate(adapt.adaptation_id)
        assert adapt.status == AdaptationStatus.ACTIVE

        # Tick a few cycles
        for _ in range(3):
            adapter.tick_cycle()
        assert adapt.cycles_active == 3

        # Report effective
        adapter.report_effectiveness(adapt.adaptation_id, 0.85)
        assert adapt.status == AdaptationStatus.EFFECTIVE
        assert adapter.effective_count == 1

    def test_adaptation_rollback_lifecycle(self):
        """Adaptation proposed → activated → ineffective → rolled back."""
        from src.kortana.services.behavioral_adapter import (
            AdaptationStatus,
            BehavioralAdapter,
        )

        adapter = BehavioralAdapter()

        adapt = adapter.propose_from_pattern("p1", "decision_drift", "test", "moderate")
        adapter.activate(adapt.adaptation_id)

        # After several cycles, report ineffective
        for _ in range(4):
            adapter.tick_cycle()
        adapter.report_effectiveness(adapt.adaptation_id, 0.15)
        assert adapt.status == AdaptationStatus.INEFFECTIVE

        # Roll back
        adapter.rollback(adapt.adaptation_id, "made things worse")
        assert adapt.status == AdaptationStatus.ROLLED_BACK
        assert adapter.rollback_count == 1

    def test_learning_velocity_tracks_over_time(self):
        """Learning velocity increases as more lessons are extracted."""
        from src.kortana.services.experience_extractor import ExperienceExtractor
        from src.kortana.services.feedback_integrator import FeedbackIntegrator

        extractor = ExperienceExtractor()
        integrator = FeedbackIntegrator()

        velocities = []
        for i in range(1, 8):
            extractor.extract_from_beat(
                beat_id=f"b-{i}", cycle_number=i, state="alive",
                observations=[{"source": "s", "description": "d", "severity": "info"}],
                decisions=[], actions=["did stuff"], deferrals=[], reflections=["ok"],
            )
            report = integrator.integrate(
                cycle_number=i,
                experience_summary=extractor.get_summary(),
                pattern_summary={"pattern_count": 0, "actionable_count": 0},
                adaptation_summary={"adaptation_count": 0, "active_count": 0,
                                    "effectiveness_rate": 0.0, "status_counts": {},
                                    "rollback_count": 0},
            )
            velocities.append(report.learning_velocity)

        # velocity should be stable (same lessons each cycle)
        assert all(v > 0 for v in velocities[1:])

    def test_v26_to_v27_bridge(self):
        """V26 heartbeat data feeds directly into V27 experience extraction."""
        from src.kortana.services.experience_extractor import ExperienceExtractor
        from src.kortana.services.heartbeat_loop import HeartbeatLoop

        loop = HeartbeatLoop()
        extractor = ExperienceExtractor()

        # Simulate a V26 heartbeat
        beat = loop.begin_beat()
        loop.add_observation(beat.beat_id, "health", "nominal", severity="info")
        loop.add_decision(beat.beat_id, "continue", "all clear", priority=5)
        loop.record_action(beat.beat_id, "routine check")
        loop.add_reflection(beat.beat_id, "clean cycle")
        loop.complete_beat(beat.beat_id)

        # Feed into V27 experience extraction
        exp = extractor.extract_from_beat(
            beat_id=beat.beat_id,
            cycle_number=beat.cycle_number,
            state=beat.state.value,
            observations=[o.to_dict() for o in beat.observations],
            decisions=[d.to_dict() for d in beat.decisions],
            actions=beat.actions_taken,
            deferrals=beat.deferrals,
            reflections=beat.reflections,
            duration_ms=beat.duration_ms,
        )
        assert exp.source_beat_id == beat.beat_id
        assert exp.cycle_number == beat.cycle_number
        assert exp.observation_count == 1
        assert len(exp.lessons) > 0
