"""Tests for cost-optimized routing model lane behavior."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from src.kortana.config import get_settings
from src.kortana.cost_optimized_model_router import (
    CostOptimizedModelRouter,
    ModelProvider,
    TaskType,
    get_cost_optimized_model_router,
    reset_cost_optimized_model_router,
)
from src.kortana.api_integration import UnifiedAPIClient
from src.kortana.api_integration import ProviderRateLimitError
from src.kortana.model_usage_telemetry import get_model_usage_telemetry


def test_cost_router_skips_quarantined_openai_model(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("GROQ_API_KEY", "groq-test")
    monkeypatch.setenv("KORTANA_MODEL_USAGE_LANE", "core")
    get_settings.cache_clear()

    with patch(
        "src.kortana.cost_optimized_model_router.model_allowed",
        side_effect=lambda model_name, active_lane=None: model_name != "gpt-5.4-nano",
    ):
        router = CostOptimizedModelRouter()

    assert ModelProvider.OPENAI not in router.configs
    assert ModelProvider.GROQ in router.configs
    strategy = router.get_routing_strategy()
    assert strategy["model_usage_lane"] == "core"
    assert strategy["model_lanes"]["groq"] == "core"


def test_cost_router_singleton_reuses_runtime_state(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("KORTANA_MODEL_USAGE_LANE", "core")
    get_settings.cache_clear()
    reset_cost_optimized_model_router()

    router = get_cost_optimized_model_router()
    router.record_usage(ModelProvider.OPENAI, TaskType.SUMMARY, 10, 5)

    same_router = get_cost_optimized_model_router()

    assert same_router is router
    assert same_router.get_cost_report()["totals"]["requests"] == 1


def test_unified_api_client_uses_router_configured_models(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("GROQ_API_KEY", "groq-test")
    monkeypatch.setenv("KORTANA_MODEL_USAGE_LANE", "core")
    get_settings.cache_clear()

    client = UnifiedAPIClient()

    assert client.clients[ModelProvider.OPENAI].model == "gpt-5.4-nano"
    assert client.clients[ModelProvider.GROQ].model == "mixtral-8x7b-32768"


def test_cost_report_includes_model_metadata(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("KORTANA_MODEL_USAGE_LANE", "core")
    get_settings.cache_clear()

    router = CostOptimizedModelRouter()
    report = router.get_cost_report()

    assert report["model_usage_lane"] == "core"
    assert report["providers"]["openai"]["model"] == "gpt-5.4-nano"
    assert report["providers"]["openai"]["lane"] == "core"
    assert report["providers"]["openai"]["input_cost_per_1k"] == 0.0002
    assert report["providers"]["openai"]["output_cost_per_1k"] == 0.00125
    assert report["totals"]["requests"] == 0
    assert report["providers"]["openai"]["total_tokens"] == 0


def test_cost_report_tracks_usage_metadata(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("KORTANA_MODEL_USAGE_LANE", "core")
    get_settings.cache_clear()

    router = CostOptimizedModelRouter()
    router.record_usage(ModelProvider.OPENAI, TaskType.SUMMARY, 120, 30)
    report = router.get_cost_report()
    openai = report["providers"]["openai"]

    assert report["totals"]["requests"] == 1
    assert report["totals"]["input_tokens"] == 120
    assert report["totals"]["output_tokens"] == 30
    assert report["totals"]["total_tokens"] == 150
    assert openai["requests"] == 1
    assert openai["input_tokens"] == 120
    assert openai["output_tokens"] == 30
    assert openai["total_tokens"] == 150
    assert openai["last_task_type"] == "summary"
    assert openai["last_used_at"] is not None


def test_summary_tasks_enable_openai_fast_lane(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("GROQ_API_KEY", "groq-test")
    monkeypatch.setenv("GEMINI_API_KEY", "gm-test")
    monkeypatch.setenv("KORTANA_MODEL_USAGE_LANE", "core")
    get_settings.cache_clear()

    with patch(
        "src.kortana.cost_optimized_model_router.get_model_name",
        return_value="gemini-2.0-flash",
    ):
        router = CostOptimizedModelRouter()

    providers = router.select_for_task(TaskType.SUMMARY)
    assert providers[:2] == [
        ModelProvider.GROQ,
        ModelProvider.GEMINI,
    ]


def test_rate_limited_provider_is_temporarily_skipped(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("GROQ_API_KEY", "groq-test")
    monkeypatch.setenv("KORTANA_MODEL_USAGE_LANE", "core")
    get_settings.cache_clear()

    router = CostOptimizedModelRouter()
    router.mark_rate_limited(ModelProvider.GROQ, retry_after_seconds=30)

    providers = router.select_for_task(TaskType.SUMMARY)

    assert ModelProvider.GROQ not in providers
    # With Groq cooled down, fallback to any available configured provider
    assert len(providers) >= 1


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


def test_cost_report_includes_provider_cooldown(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("KORTANA_MODEL_USAGE_LANE", "core")
    get_settings.cache_clear()

    router = CostOptimizedModelRouter()
    router.mark_rate_limited(
        ModelProvider.OPENAI,
        retry_after_seconds=45,
        reason="OpenAI API rate limit",
    )

    report = router.get_cost_report()
    openai = report["providers"]["openai"]

    assert openai["cooling_down"] is True
    assert openai["cooldown_seconds"] > 0
    assert openai["last_error"] == "OpenAI API rate limit"


@pytest.mark.asyncio
@patch("src.kortana.api_integration.get_cost_optimized_model_router")
async def test_unified_api_client_records_runtime_usage(mock_get_router) -> None:
    telemetry = get_model_usage_telemetry()
    telemetry.reset()

    mock_router = mock_get_router.return_value
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


@pytest.mark.asyncio
@patch("src.kortana.api_integration.get_cost_optimized_model_router")
async def test_unified_api_client_cools_down_rate_limited_provider(mock_get_router) -> None:
    mock_router = mock_get_router.return_value
    mock_router.configs = {}
    mock_router.model_usage_lane = SimpleNamespace(value="core")
    mock_router.select_for_task.return_value = [
        ModelProvider.GROQ,
        ModelProvider.OPENAI,
    ]
    mock_router.estimate_cost.return_value = 0.0
    mock_router.record_usage.return_value = None
    mock_router.mark_rate_limited.return_value = None
    mock_router.record_provider_failure.return_value = None

    client = UnifiedAPIClient()
    groq_client = AsyncMock()
    groq_client.model = "mixtral-8x7b-32768"
    groq_client.generate.side_effect = ProviderRateLimitError(
        ModelProvider.GROQ,
        "Groq API rate limit",
        retry_after_seconds=25,
    )
    openai_client = AsyncMock()
    openai_client.model = "gpt-5.4-nano"
    openai_client.generate.return_value = ("ok", 12, 8)
    client.clients = {
        ModelProvider.GROQ: groq_client,
        ModelProvider.OPENAI: openai_client,
    }

    content, provider, cost = await client.generate("hello", TaskType.SUMMARY)

    assert content == "ok"
    assert provider == ModelProvider.OPENAI
    assert cost == 0.0
    mock_router.mark_rate_limited.assert_called_once_with(
        ModelProvider.GROQ,
        retry_after_seconds=25,
        reason="Groq API rate limit",
    )


@pytest.mark.asyncio
@patch("src.kortana.api_integration.asyncio.sleep", new_callable=AsyncMock)
@patch("src.kortana.api_integration.get_adaptive_retry_engine")
@patch("src.kortana.api_integration.get_cost_optimized_model_router")
async def test_unified_api_client_retries_transient_provider_failures(
    mock_get_router,
    mock_get_retry_engine,
    mock_sleep,
) -> None:
    mock_router = mock_get_router.return_value
    mock_router.configs = {}
    mock_router.model_usage_lane = SimpleNamespace(value="core")
    mock_router.select_for_task.return_value = [ModelProvider.GROQ]
    mock_router.estimate_cost.return_value = 0.0
    mock_router.record_usage.return_value = None
    mock_router.record_provider_failure.return_value = None

    retry_engine = mock_get_retry_engine.return_value
    retry_engine.should_retry.return_value = True
    retry_engine.get_retry_delay.return_value = 0.25

    client = UnifiedAPIClient()
    groq_client = AsyncMock()
    groq_client.model = "mixtral-8x7b-32768"
    transient_error = Exception("connection timed out")
    groq_client.generate.side_effect = [
        transient_error,
        ("ok", 20, 10),
    ]
    client.clients = {ModelProvider.GROQ: groq_client}

    content, provider, cost = await client.generate("hello", TaskType.SUMMARY)

    assert content == "ok"
    assert provider == ModelProvider.GROQ
    assert cost == 0.0
    assert groq_client.generate.await_count == 2
    retry_engine.should_retry.assert_called_once()
    retry_engine.get_retry_delay.assert_called_once()
    retry_engine.record_retry.assert_called_once_with(
        "groq:summary",
        transient_error,
        0,
        will_retry=True,
        delay_seconds=0.25,
        provider="groq",
        task_type="summary",
    )
    mock_sleep.assert_awaited_once_with(0.25)
    mock_router.record_provider_failure.assert_not_called()
