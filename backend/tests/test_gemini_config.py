from __future__ import annotations

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.kortana.provider_model_defaults import (
    GEMINI_25_FLASH_MODEL,
    GEMINI_DEFAULT_MODEL,
)
from src.kortana.services.gemini_config import get_available_model


def _install_fake_google_module(monkeypatch, models: list[object]) -> None:
    client = MagicMock()
    client.models.list.return_value = models
    fake_genai = SimpleNamespace(Client=MagicMock(return_value=client))
    monkeypatch.setitem(
        sys.modules,
        "google",
        SimpleNamespace(genai=fake_genai),
    )


def test_get_available_model_prefers_first_allowed_fallback(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    models = [
        SimpleNamespace(name=f"models/{GEMINI_DEFAULT_MODEL}"),
        SimpleNamespace(name=f"models/{GEMINI_25_FLASH_MODEL}"),
    ]
    _install_fake_google_module(monkeypatch, models)

    with patch(
        "src.kortana.services.gemini_config.model_allowed",
        return_value=True,
    ):
        selected = get_available_model()

    assert selected == GEMINI_DEFAULT_MODEL


def test_get_available_model_skips_disallowed_fallback_candidates(
    monkeypatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    models = [
        SimpleNamespace(name=f"models/{GEMINI_25_FLASH_MODEL}"),
        SimpleNamespace(name=f"models/{GEMINI_DEFAULT_MODEL}"),
    ]
    _install_fake_google_module(monkeypatch, models)

    with patch(
        "src.kortana.services.gemini_config.model_allowed",
        side_effect=lambda model_name: model_name != GEMINI_25_FLASH_MODEL,
    ):
        selected = get_available_model()

    assert selected == GEMINI_DEFAULT_MODEL
