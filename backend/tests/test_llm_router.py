"""
Unit tests for Kor'tana backend - LLM Router
"""

import pytest
from unittest.mock import patch

from src.kortana.llm_router import LLMRouter, LLMResponse


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
    assert "gemini-2.0-flash" in llm_router.models


@pytest.mark.asyncio
async def test_available_models(llm_router):
    """Test listing available models"""
    models = llm_router.available_models()
    assert isinstance(models, list)
    assert len(models) > 0


@pytest.mark.asyncio
async def test_generate_with_fallback(llm_router):
    """Test generation with fallback to secondary model"""
    with patch.object(llm_router, '_call_gemini', side_effect=Exception("API Error")):
        with patch.object(llm_router, '_call_openai', return_value=LLMResponse(
            content="Test response",
            model="gpt-4o",
            provider="openai",
            tokens_used=10,
            temperature=0.7,
        )):
            response = await llm_router.generate("Test prompt")
            assert response.content == "Test response"
            assert response.model == "gpt-4o"


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
    assert "available_models" in info
    assert "fallback_order" in info
    assert isinstance(info["available_models"], list)
