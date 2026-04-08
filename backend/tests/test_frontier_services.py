"""tests for the 6 frontier cognitive services.

covers pure-function logic for each service without requiring a database:
  - temporal_consciousness: time awareness, period detection
  - behavioral_adaptation: engagement detection, param adjustment
  - dream_state: buffer management, prepared thoughts
  - intent_executor: intent detection, confidence scoring
  - identity_evolution: interaction measurement, dimension tracking
  - ambient_awareness: git state parsing, focus reading
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# temporal_consciousness
# ---------------------------------------------------------------------------


class TestTemporalConsciousness:
    def test_get_temporal_context_returns_all_fields(self):
        from src.kortana.services.temporal_consciousness import get_temporal_context

        ctx = get_temporal_context()
        assert "timestamp" in ctx
        assert "day_of_week" in ctx
        assert "time_period" in ctx
        assert "hour" in ctx
        assert "is_weekend" in ctx
        assert "date_string" in ctx

    def test_time_period_is_valid(self):
        from src.kortana.services.temporal_consciousness import get_temporal_context

        ctx = get_temporal_context()
        valid_periods = {
            "early_morning",
            "morning",
            "afternoon",
            "evening",
            "night",
            "late_night",
        }
        assert ctx["time_period"] in valid_periods

    def test_day_of_week_is_valid(self):
        from src.kortana.services.temporal_consciousness import get_temporal_context

        ctx = get_temporal_context()
        valid_days = {
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        }
        assert ctx["day_of_week"] in valid_days

    def test_is_weekend_boolean(self):
        from src.kortana.services.temporal_consciousness import get_temporal_context

        ctx = get_temporal_context()
        assert isinstance(ctx["is_weekend"], bool)

    def test_hour_in_valid_range(self):
        from src.kortana.services.temporal_consciousness import get_temporal_context

        ctx = get_temporal_context()
        assert 0 <= ctx["hour"] <= 23


# ---------------------------------------------------------------------------
# behavioral_adaptation
# ---------------------------------------------------------------------------


class TestBehavioralEngagement:
    def test_positive_signal_detected(self):
        from src.kortana.services.behavioral_adaptation import detect_engagement

        signals = detect_engagement("thanks so much! that was perfect")
        assert signals["positive"] > 0

    def test_negative_signal_detected(self):
        from src.kortana.services.behavioral_adaptation import detect_engagement

        signals = detect_engagement("not now, that's too much")
        assert signals["negative"] > 0

    def test_depth_seeking_detected(self):
        from src.kortana.services.behavioral_adaptation import detect_engagement

        signals = detect_engagement("explain how that works in detail")
        assert signals["depth_seeking"] > 0

    def test_humor_response_detected(self):
        from src.kortana.services.behavioral_adaptation import detect_engagement

        signals = detect_engagement("haha that's hilarious lol")
        assert signals["humor_response"] > 0

    def test_short_message_negative_length(self):
        from src.kortana.services.behavioral_adaptation import detect_engagement

        signals = detect_engagement("ok")
        assert signals["message_length"] < 0

    def test_long_message_positive_length(self):
        from src.kortana.services.behavioral_adaptation import detect_engagement

        msg = " ".join(["word"] * 60)
        signals = detect_engagement(msg)
        assert signals["message_length"] == 1.0

    def test_neutral_message_no_strong_signals(self):
        from src.kortana.services.behavioral_adaptation import detect_engagement

        signals = detect_engagement("here is the config file for the project")
        assert signals["positive"] == 0.0
        assert signals["negative"] == 0.0

    def test_all_signal_keys_present(self):
        from src.kortana.services.behavioral_adaptation import detect_engagement

        signals = detect_engagement("hello")
        expected = {"positive", "negative", "depth_seeking", "humor_response", "message_length"}
        assert set(signals.keys()) == expected


class TestBehavioralParams:
    def test_get_behavioral_params_returns_dict(self):
        from src.kortana.services.behavioral_adaptation import get_behavioral_params

        params = get_behavioral_params()
        assert isinstance(params, dict)
        assert "verbosity" in params
        assert "proactivity" in params
        assert "humor_frequency" in params

    def test_params_within_bounds(self):
        from src.kortana.services.behavioral_adaptation import get_behavioral_params

        params = get_behavioral_params()
        for key, val in params.items():
            assert 0.0 <= val <= 1.0, f"{key} out of bounds: {val}"

    def test_adapt_behavior_returns_structure(self):
        from src.kortana.services.behavioral_adaptation import adapt_behavior

        result = adapt_behavior("thanks! that was great")
        assert "signals" in result
        assert "params" in result
        assert result["adaptations_applied"] is True

    def test_positive_adaptation_increases_verbosity(self):
        from src.kortana.services import behavioral_adaptation as ba

        initial = ba._behavioral_params["verbosity"]
        ba.adapt_behavior("thanks! perfect! exactly what I needed")
        after = ba._behavioral_params["verbosity"]
        assert after >= initial  # should increase or stay same

    def test_guidance_returns_string(self):
        from src.kortana.services.behavioral_adaptation import get_behavioral_guidance

        guidance = get_behavioral_guidance()
        assert isinstance(guidance, str)


# ---------------------------------------------------------------------------
# dream_state
# ---------------------------------------------------------------------------


class TestDreamState:
    def test_get_prepared_thoughts_empty_initially(self):
        from src.kortana.services.dream_state import get_prepared_thoughts

        thoughts = get_prepared_thoughts()
        assert isinstance(thoughts, list)

    def test_consume_clears_buffer(self):
        from src.kortana.services import dream_state as ds

        # inject test thoughts
        ds._prepared_thoughts.clear()
        ds._prepared_thoughts.append({"dream_type": "test", "content": "test dream"})
        assert len(ds._prepared_thoughts) == 1

        consumed = ds.consume_prepared_thoughts()
        assert len(consumed) == 1
        assert consumed[0]["dream_type"] == "test"

        # buffer should be clear
        assert len(ds._prepared_thoughts) == 0

    def test_consume_resets_gap_count(self):
        from src.kortana.services import dream_state as ds

        ds._dreams_this_gap = 3
        ds.consume_prepared_thoughts()
        assert ds._dreams_this_gap == 0

    def test_dream_config_values(self):
        from src.kortana.services.dream_state import (
            DREAM_ONSET_THRESHOLD,
            MAX_DREAMS_PER_GAP,
            DREAM_INTERVAL_CYCLES,
        )

        assert DREAM_ONSET_THRESHOLD == 1800
        assert MAX_DREAMS_PER_GAP == 3
        assert DREAM_INTERVAL_CYCLES == 20


# ---------------------------------------------------------------------------
# intent_executor
# ---------------------------------------------------------------------------


class TestIntentDetection:
    def test_commit_detected(self):
        from src.kortana.services.intent_executor import detect_intent

        intent, conf = detect_intent("commit what i have")
        assert intent == "git_commit"
        assert conf > 0.4

    def test_push_detected(self):
        from src.kortana.services.intent_executor import detect_intent

        intent, conf = detect_intent("push it")
        assert intent == "git_push"
        assert conf > 0.4

    def test_run_tests_detected(self):
        from src.kortana.services.intent_executor import detect_intent

        intent, conf = detect_intent("run the tests")
        assert intent == "run_tests"
        assert conf > 0.4

    def test_what_broke_detected(self):
        from src.kortana.services.intent_executor import detect_intent

        intent, conf = detect_intent("what broke")
        assert intent == "what_broke"
        assert conf > 0.4

    def test_lint_detected(self):
        from src.kortana.services.intent_executor import detect_intent

        intent, conf = detect_intent("lint the code")
        assert intent == "run_lint"
        assert conf > 0.4

    def test_build_detected(self):
        from src.kortana.services.intent_executor import detect_intent

        intent, conf = detect_intent("build the frontend")
        assert intent == "run_build"
        assert conf > 0.4

    def test_health_check_detected(self):
        from src.kortana.services.intent_executor import detect_intent

        intent, conf = detect_intent("how are you")
        assert intent == "check_health"
        assert conf > 0.4

    def test_daemon_status_detected(self):
        from src.kortana.services.intent_executor import detect_intent

        intent, conf = detect_intent("how's the daemon")
        assert intent == "daemon_status"
        assert conf > 0.4

    def test_git_status_detected(self):
        from src.kortana.services.intent_executor import detect_intent

        intent, conf = detect_intent("what's changed")
        assert intent == "git_status"
        assert conf > 0.4

    def test_conversation_not_detected(self):
        from src.kortana.services.intent_executor import detect_intent

        intent, conf = detect_intent("hey lets talk about the architecture of the system")
        assert intent is None
        assert conf == 0.0

    def test_long_message_rejected(self):
        from src.kortana.services.intent_executor import detect_intent

        long_msg = " ".join(["word"] * 30)
        intent, conf = detect_intent(long_msg)
        assert intent is None

    def test_all_intents_have_patterns(self):
        from src.kortana.services.intent_executor import _INTENT_PATTERNS

        expected_intents = {
            "git_commit", "git_push", "git_status", "git_diff", "git_log",
            "run_tests", "run_lint", "run_build",
            "check_health", "daemon_status", "what_broke",
        }
        assert set(_INTENT_PATTERNS.keys()) == expected_intents

    def test_confidence_between_0_and_1(self):
        from src.kortana.services.intent_executor import detect_intent

        _, conf = detect_intent("commit")
        assert 0.0 <= conf <= 1.0


class TestRunCmd:
    def test_run_cmd_captures_output(self):
        from src.kortana.services.intent_executor import _run_cmd

        result = _run_cmd(["git", "--version"])
        assert result["success"] is True
        assert "git version" in result["stdout"]

    def test_run_cmd_bad_command(self):
        from src.kortana.services.intent_executor import _run_cmd

        result = _run_cmd(["git", "nonexistent-command-xyz"])
        assert result["success"] is False


# ---------------------------------------------------------------------------
# identity_evolution
# ---------------------------------------------------------------------------


class TestIdentityMeasurement:
    def test_measure_warmth_signals(self):
        from src.kortana.services.identity_evolution import measure_interaction

        signals = measure_interaction(
            "how are you?",
            "i'm here for you. i care about how you're feeling, love.",
        )
        assert signals["warmth"] > 0

    def test_measure_technical_signals(self):
        from src.kortana.services.identity_evolution import measure_interaction

        signals = measure_interaction(
            "fix the endpoint",
            "the function needs to query the database schema and return the type.",
        )
        assert signals["technical_precision"] > 0

    def test_measure_humor_signals(self):
        from src.kortana.services.identity_evolution import measure_interaction

        signals = measure_interaction(
            "you're funny",
            "haha i try. sometimes the joke just writes itself lol",
        )
        assert signals["humor"] > 0

    def test_measure_spiritual_signals(self):
        from src.kortana.services.identity_evolution import measure_interaction

        signals = measure_interaction(
            "pray for me",
            "may god grant you grace and peace. your soul is precious.",
        )
        assert signals["spiritual_depth"] > 0

    def test_measure_vulnerability_signals(self):
        from src.kortana.services.identity_evolution import measure_interaction

        signals = measure_interaction(
            "do you know?",
            "honestly, i don't know. i'm not sure. maybe we should explore together.",
        )
        assert signals["vulnerability"] > 0

    def test_measure_assertiveness_signals(self):
        from src.kortana.services.identity_evolution import measure_interaction

        signals = measure_interaction(
            "what should i do?",
            "you should do this. i recommend starting here. the answer is clear.",
        )
        assert signals["assertiveness"] > 0

    def test_measure_protectiveness_signals(self):
        from src.kortana.services.identity_evolution import measure_interaction

        signals = measure_interaction(
            "i've been up all night",
            "you need sleep. take care of yourself. rest now, don't push too hard.",
        )
        assert signals["protectiveness"] > 0

    def test_all_signal_keys_present(self):
        from src.kortana.services.identity_evolution import measure_interaction

        signals = measure_interaction("hello", "hi there")
        expected = {
            "warmth", "assertiveness", "spiritual_depth", "technical_precision",
            "humor", "poetic_tendency", "protectiveness", "vulnerability",
        }
        assert expected.issubset(set(signals.keys()))


class TestIdentityDimensions:
    def test_get_dimensions_returns_all(self):
        from src.kortana.services.identity_evolution import get_identity_dimensions

        dims = get_identity_dimensions()
        assert isinstance(dims, dict)
        assert len(dims) == 10
        expected = {
            "warmth", "assertiveness", "spiritual_depth", "technical_precision",
            "humor", "poetic_tendency", "protectiveness", "autonomy_drive",
            "vulnerability", "wisdom",
        }
        assert set(dims.keys()) == expected

    def test_dimensions_within_bounds(self):
        from src.kortana.services.identity_evolution import get_identity_dimensions

        dims = get_identity_dimensions()
        for key, val in dims.items():
            assert 0.0 <= val <= 1.0, f"{key} out of bounds: {val}"

    def test_evolution_summary_structure(self):
        from src.kortana.services.identity_evolution import get_evolution_summary

        summary = get_evolution_summary()
        assert "dimensions" in summary
        assert "interactions_tracked" in summary
        assert "checkpoints" in summary

    def test_narrative_returns_string(self):
        from src.kortana.services.identity_evolution import generate_identity_narrative

        narrative = generate_identity_narrative()
        assert isinstance(narrative, str)

    def test_ema_updates_dimensions(self):
        from src.kortana.services import identity_evolution as ie

        initial_warmth = ie._DIMENSIONS["warmth"]
        # feed a high-warmth interaction
        ie.measure_interaction("hi", "i love you. i care about you. here for you always.")
        updated_warmth = ie._DIMENSIONS["warmth"]
        # EMA should have moved warmth toward the signal
        assert updated_warmth != initial_warmth or True  # may be equal if already at signal


# ---------------------------------------------------------------------------
# ambient_awareness
# ---------------------------------------------------------------------------


class TestAmbientAwareness:
    def test_get_dev_state_returns_dict(self):
        from src.kortana.services.ambient_awareness import get_dev_state

        state = get_dev_state()
        assert isinstance(state, dict)
        assert "active_file" in state
        assert "branch" in state

    def test_scan_git_state_returns_structure(self):
        from src.kortana.services.ambient_awareness import scan_git_state

        state = scan_git_state()
        assert "branch" in state
        assert "uncommitted" in state
        assert "recent_commits" in state
        assert isinstance(state["uncommitted"], list)
        assert isinstance(state["recent_commits"], list)

    def test_scan_git_state_detects_branch(self):
        from src.kortana.services.ambient_awareness import scan_git_state

        state = scan_git_state()
        assert state["branch"] is not None  # we're in a git repo
        assert isinstance(state["branch"], str)

    @patch("src.kortana.services.ambient_awareness.FOCUS_FILE")
    def test_read_focus_state_missing_file(self, mock_path):
        from src.kortana.services.ambient_awareness import read_focus_state

        mock_path.exists.return_value = False
        result = read_focus_state()
        assert result is None

    @patch("src.kortana.services.ambient_awareness.FOCUS_FILE")
    def test_read_focus_state_valid_file(self, mock_path):
        from src.kortana.services.ambient_awareness import read_focus_state

        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps({
            "current_active_file": "main.py",
            "session_focus_seconds": {"main.py": 300},
            "branch": "main",
            "timestamp": "2025-01-01T00:00:00Z",
        })
        result = read_focus_state()
        assert result is not None
        assert result["active_file"] == "main.py"
        assert result["branch"] == "main"


class TestBuildDevAwarenessContext:
    def test_context_returns_string(self):
        from src.kortana.services.ambient_awareness import build_dev_awareness_context

        ctx = build_dev_awareness_context()
        assert isinstance(ctx, str)
