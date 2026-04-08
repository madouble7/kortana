"""Lightweight model lane policy for governed experimentation."""

from __future__ import annotations

from enum import Enum
from typing import Protocol

from src.kortana.config import get_settings
from src.kortana.provider_model_defaults import DEFAULT_CORE_MODEL_CATALOG


class SupportsModelLaneSettings(Protocol):
    """Subset of settings required by the model lane policy."""

    KORTANA_MODEL_USAGE_LANE: str
    KORTANA_CORE_MODELS: list[str]
    KORTANA_EXPERIMENTAL_MODELS: list[str]
    KORTANA_QUARANTINE_MODELS: list[str]


class ModelLane(str, Enum):
    CORE = "core"
    EXPERIMENTAL = "experimental"
    QUARANTINE = "quarantine"


_LANE_RANK = {
    ModelLane.CORE: 0,
    ModelLane.EXPERIMENTAL: 1,
    ModelLane.QUARANTINE: 2,
}

def _normalize_model_name(model_name: str) -> str:
    return model_name.strip()


def _settings(settings: SupportsModelLaneSettings | None = None) -> SupportsModelLaneSettings:
    return settings or get_settings()


def _as_set(values: list[str]) -> set[str]:
    return {_normalize_model_name(value) for value in values if value.strip()}


def get_active_model_lane(
    settings: SupportsModelLaneSettings | None = None,
) -> ModelLane:
    """Resolve the active runtime lane for model selection."""
    raw_lane = _settings(settings).KORTANA_MODEL_USAGE_LANE.strip().lower()
    try:
        return ModelLane(raw_lane)
    except ValueError:
        return ModelLane.CORE


def classify_model_lane(
    model_name: str,
    settings: SupportsModelLaneSettings | None = None,
) -> ModelLane:
    """Classify a model into core, experimental, or quarantine."""
    normalized = _normalize_model_name(model_name)
    active_settings = _settings(settings)

    if normalized in _as_set(active_settings.KORTANA_CORE_MODELS):
        return ModelLane.CORE
    if normalized in _as_set(active_settings.KORTANA_EXPERIMENTAL_MODELS):
        return ModelLane.EXPERIMENTAL
    if normalized in _as_set(active_settings.KORTANA_QUARANTINE_MODELS):
        return ModelLane.QUARANTINE
    if normalized.startswith("ft:"):
        return ModelLane.QUARANTINE
    if normalized in DEFAULT_CORE_MODEL_CATALOG:
        return ModelLane.CORE
    return ModelLane.EXPERIMENTAL


def model_allowed(
    model_name: str,
    *,
    active_lane: ModelLane | None = None,
    settings: SupportsModelLaneSettings | None = None,
) -> bool:
    """Return True when a model is allowed under the active lane."""
    resolved_lane = active_lane or get_active_model_lane(settings)
    model_lane = classify_model_lane(model_name, settings)
    return _LANE_RANK[model_lane] <= _LANE_RANK[resolved_lane]


def describe_model_lane(
    model_name: str,
    settings: SupportsModelLaneSettings | None = None,
) -> str:
    """Return the lane label for a model."""
    return classify_model_lane(model_name, settings).value
