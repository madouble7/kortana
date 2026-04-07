"""
Unit tests for Kor'tana backend - LLM Router
"""

from unittest.mock import patch

import pytest
from src.kortana.llm_router import LLMResponse, LLMRouter
from src.kortana.model_lane_policy import get_active_model_lane
from src.kortana.model_usage_telemetry import get_model_usage_telemetry
from src.kortana.provider_model_defaults import (
    LLM_ROUTER_DEFAULTS,
    LLM_ROUTER_FALLBACK_ORDER,
)


@pytest.fixture
def llm_router():
    """Fixture for LLM router"""
    with patch.dict('os.environ', {
        'GEMINI_API_KEY': 'test_gemini_key',
        'OPENAI_API_KEY': 'test_openai_key',
        'GROQ_API_KEY': 'test_groq_key',
        'ANTHROPIC_API_KEY': 'test_anthropic_key',
    }):
        return LLMRouter()


@pytest.mark.asyncio
async def test_llm_router_initialization(llm_router):
    """Test LLM router initialization with multiple models"""
    assert llm_router.primary_model is not None
    assert len(llm_router.models) > 0
    assert LLM_ROUTER_DEFAULTS.gemini in llm_router.models
    assert llm_router.primary_model.model_name == LLM_ROUTER_DEFAULTS.gemini


@pytest.mark.asyncio
async def test_available_models(llm_router):
    """Test listing available models"""
    models = llm_router.available_models()
    assert isinstance(models, list)
    assert len(models) > 0


def test_llm_router_fallback_order_uses_catalog(llm_router):
    """Fallback ordering should come from the shared defaults catalog."""
    assert [config.model_name for config in llm_router.fallback_models] == [
        model_name for model_name in LLM_ROUTER_FALLBACK_ORDER if model_name in llm_router.models
    ]


@pytest.mark.asyncio
async def test_generate_with_fallback(llm_router):
    """Test generation with fallback to secondary model"""
    with patch.object(llm_router, '_call_gemini', side_effect=Exception("API Error")):
        with patch.object(llm_router, '_call_openai', return_value=LLMResponse(
            content="Test response",
            model=LLM_ROUTER_DEFAULTS.openai,
            provider="openai",
            tokens_used=10,
            temperature=0.7,
        )):
            response = await llm_router.generate("Test prompt")
            assert response.content == "Test response"
            assert response.model == LLM_ROUTER_DEFAULTS.openai


@pytest.mark.asyncio
async def test_generate_all_models_fail(llm_router):
    """Test generation when all models fail"""
    with patch.object(llm_router, '_call_gemini', side_effect=Exception("Error 1")):
        with patch.object(llm_router, '_call_openai', side_effect=Exception("Error 2")):
            with patch.object(llm_router, '_call_groq', side_effect=Exception("Error 3")):
                with patch.object(llm_router, '_call_anthropic', side_effect=Exception("Error 4")):
                    with pytest.raises(RuntimeError) as exc_info:
                        await llm_router.generate("Test prompt")
                    assert "All LLM models exhausted" in str(exc_info.value)


@pytest.mark.asyncio
async def test_model_info(llm_router):
    """Test getting model information"""
    info = llm_router.get_model_info()
    assert "primary" in info
    assert "model_usage_lane" in info
    assert "available_models" in info
    assert "fallback_order" in info
    assert "model_lanes" in info
    assert isinstance(info["available_models"], list)


def test_quarantined_models_are_filtered_from_core_lane(llm_router):
    """Core lane should exclude explicitly quarantined models."""
    llm_router.settings.KORTANA_QUARANTINE_MODELS = [LLM_ROUTER_DEFAULTS.openai]
    llm_router.settings.KORTANA_MODEL_USAGE_LANE = "core"
    llm_router.model_usage_lane = get_active_model_lane(llm_router.settings)

    models = llm_router._initialize_models()

    assert LLM_ROUTER_DEFAULTS.openai not in models
    assert LLM_ROUTER_DEFAULTS.gemini in models


@pytest.mark.asyncio
async def test_generate_rejects_unavailable_requested_model(llm_router):
    """Explicit model requests should fail loudly instead of silently rerouting."""
    with pytest.raises(ValueError, match="Requested model"):
        await llm_router.generate(
            "Test prompt", model="ft:gpt-4o-mini-2024-07-18:personal::rogue"
        )


@pytest.mark.asyncio
async def test_generate_records_runtime_usage(llm_router):
    telemetry = get_model_usage_telemetry()
    telemetry.reset()

    with patch.object(
        llm_router,
        "_call_gemini",
        return_value=LLMResponse(
            content="Telemetry test",
            model=LLM_ROUTER_DEFAULTS.gemini,
            provider="gemini",
            tokens_used=12,
            temperature=0.7,
        ),
    ):
        await llm_router.generate("Record this generation")
        await telemetry.flush_persistence()

    summary = telemetry.get_summary()
    assert summary["total_generations"] == 1
    assert summary["by_subsystem"]["llm_router"] == 1
    assert summary["recent"][0]["catalog"] == "llm_router_defaults"
    assert summary["recent"][0]["selection"] == "primary_default"
