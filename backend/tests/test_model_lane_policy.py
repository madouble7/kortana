"""Tests for lightweight model lane governance."""

from types import SimpleNamespace

from src.kortana.model_lane_policy import (
    ModelLane,
    classify_model_lane,
    get_active_model_lane,
    model_allowed,
)


def _settings(**overrides: object) -> SimpleNamespace:
    defaults = {
        "KORTANA_MODEL_USAGE_LANE": "core",
        "KORTANA_CORE_MODELS": [],
        "KORTANA_EXPERIMENTAL_MODELS": [],
        "KORTANA_QUARANTINE_MODELS": [],
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_fine_tuned_models_default_to_quarantine() -> None:
    settings = _settings()

    assert (
        classify_model_lane(
            "ft:gpt-4o-mini-2024-07-18:personal::example", settings
        )
        == ModelLane.QUARANTINE
    )


def test_unknown_base_models_default_to_experimental() -> None:
    settings = _settings()

    assert classify_model_lane("gpt-5-future-preview", settings) == ModelLane.EXPERIMENTAL


def test_explicit_core_promotion_overrides_fine_tune_default() -> None:
    model_name = "ft:gpt-4o-mini-2024-07-18:personal::promoted"
    settings = _settings(KORTANA_CORE_MODELS=[model_name])

    assert classify_model_lane(model_name, settings) == ModelLane.CORE


def test_model_allowed_tracks_active_lane() -> None:
    model_name = "gpt-5-future-preview"
    core_settings = _settings(KORTANA_MODEL_USAGE_LANE="core")
    experimental_settings = _settings(KORTANA_MODEL_USAGE_LANE="experimental")
    quarantine_settings = _settings(KORTANA_MODEL_USAGE_LANE="quarantine")

    assert get_active_model_lane(core_settings) == ModelLane.CORE
    assert model_allowed(model_name, settings=core_settings) is False
    assert model_allowed(model_name, settings=experimental_settings) is True
    assert model_allowed(
        "ft:gpt-4o-mini-2024-07-18:personal::rogue",
        settings=quarantine_settings,
    ) is True
