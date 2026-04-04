"""Tests for cost-optimized routing model lane behavior."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from src.kortana.config import get_settings
from src.kortana.cost_optimized_model_router import (
    CostOptimizedModelRouter,
    ModelProvider,
    TaskType,
)
from src.kortana.api_integration import UnifiedAPIClient
from src.kortana.model_usage_telemetry import get_model_usage_telemetry


def test_cost_router_skips_quarantined_openai_model(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("GROQ_API_KEY", "groq-test")
    monkeypatch.setenv("KORTANA_MODEL_USAGE_LANE", "core")
    get_settings.cache_clear()

    with patch(
        "src.kortana.cost_optimized_model_router.model_allowed",
        side_effect=lambda model_name, active_lane=None: model_name != "gpt-4o-mini",
    ):
        router = CostOptimizedModelRouter()

    assert ModelProvider.OPENAI not in router.configs
    assert ModelProvider.GROQ in router.configs
    strategy = router.get_routing_strategy()
    assert strategy["model_usage_lane"] == "core"
    assert strategy["model_lanes"]["groq"] == "core"


def test_unified_api_client_uses_router_configured_models(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("GROQ_API_KEY", "groq-test")
    monkeypatch.setenv("KORTANA_MODEL_USAGE_LANE", "core")
    get_settings.cache_clear()

    client = UnifiedAPIClient()

    assert client.clients[ModelProvider.OPENAI].model == "gpt-4o-mini"
    assert client.clients[ModelProvider.GROQ].model == "mixtral-8x7b-32768"


def test_cost_report_includes_model_metadata(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("KORTANA_MODEL_USAGE_LANE", "core")
    get_settings.cache_clear()

    router = CostOptimizedModelRouter()
    report = router.get_cost_report()

    assert report["model_usage_lane"] == "core"
    assert report["providers"]["openai"]["model"] == "gpt-4o-mini"
    assert report["providers"]["openai"]["lane"] == "core"


def test_cost_router_uses_gemini_service_model_selection(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "gm-test")
    monkeypatch.setenv("KORTANA_MODEL_USAGE_LANE", "core")
    get_settings.cache_clear()

    with patch(
        "src.kortana.cost_optimized_model_router.get_model_name",
        return_value="gemini-2.0-flash",
    ):
        router = CostOptimizedModelRouter()

    assert router.configs[ModelProvider.GEMINI].model_name == "gemini-2.0-flash"


@pytest.mark.asyncio
@patch("src.kortana.api_integration.CostOptimizedModelRouter")
async def test_unified_api_client_records_runtime_usage(mock_router_cls) -> None:
    telemetry = get_model_usage_telemetry()
    telemetry.reset()

    mock_router = mock_router_cls.return_value
    mock_router.configs = {}
    mock_router.model_usage_lane = SimpleNamespace(value="core")
    mock_router.select_for_task.return_value = [ModelProvider.GROQ]
    mock_router.estimate_cost.return_value = 0.0
    mock_router.record_usage.return_value = None

    client = UnifiedAPIClient()
    mock_client = AsyncMock()
    mock_client.model = "mixtral-8x7b-32768"
    mock_client.generate.return_value = ("ok", 10, 5)
    client.clients = {ModelProvider.GROQ: mock_client}

    content, provider, cost = await client.generate("hello", TaskType.SUMMARY)
    await telemetry.flush_persistence()

    assert content == "ok"
    assert provider == ModelProvider.GROQ
    assert cost == 0.0
    summary = telemetry.get_summary()
    assert summary["total_generations"] == 1
    assert summary["by_subsystem"]["api_integration"] == 1
    assert summary["recent"][0]["selection"] == "task:summary"
