"""Tests for the canonical provider model defaults catalog."""

from src.kortana.provider_model_defaults import (
    AI_CONSENSUS_DEFAULTS,
    ANTHROPIC_SONNET_MODEL,
    DEFAULT_CORE_MODEL_CATALOG,
    GEMINI_DEFAULT_MODEL,
    GEMINI_DISCOVERY_FALLBACK_MODELS,
    GEMINI_EMBEDDING_FALLBACK_MODEL_PATH,
    GEMINI_EMBEDDING_MODEL_NAME,
    GEMINI_EMBEDDING_MODEL_PATH,
    LLM_ROUTER_DEFAULTS,
    LLM_ROUTER_FALLBACK_ORDER,
    MEMORY_ENGINE_EMBEDDING_MODEL,
    MULTI_MODEL_DEFAULTS,
)


def test_llm_router_defaults_match_expected_primary_and_fallbacks() -> None:
    assert LLM_ROUTER_DEFAULTS.gemini == "gemini-2.0-flash"
    assert LLM_ROUTER_FALLBACK_ORDER == (
        "gpt-4o",
        ANTHROPIC_SONNET_MODEL,
        "mixtral-8x7b-32768",
    )


def test_ai_consensus_defaults_match_expected_provider_models() -> None:
    assert AI_CONSENSUS_DEFAULTS.openai == "gpt-4o-mini"
    assert AI_CONSENSUS_DEFAULTS.anthropic == ANTHROPIC_SONNET_MODEL
    assert AI_CONSENSUS_DEFAULTS.groq == "llama-3.3-70b-versatile"
    assert AI_CONSENSUS_DEFAULTS.openrouter == "meta-llama/llama-3-70b-instruct"


def test_multi_model_defaults_match_expected_provider_models() -> None:
    assert MULTI_MODEL_DEFAULTS.openai == "gpt-3.5-turbo"
    assert MULTI_MODEL_DEFAULTS.anthropic == ANTHROPIC_SONNET_MODEL
    assert MULTI_MODEL_DEFAULTS.groq == "mixtral-8x7b-32768"
    assert MULTI_MODEL_DEFAULTS.openrouter == "meta-llama/llama-2-70b-chat"


def test_gemini_discovery_fallbacks_are_all_core_catalog_models() -> None:
    assert GEMINI_DEFAULT_MODEL == "gemini-3.1-flash-lite-preview"
    assert set(GEMINI_DISCOVERY_FALLBACK_MODELS).issubset(DEFAULT_CORE_MODEL_CATALOG)


def test_embedding_model_constants_are_consistent() -> None:
    assert GEMINI_EMBEDDING_MODEL_PATH == "models/gemini-embedding-001"
    assert GEMINI_EMBEDDING_MODEL_NAME == "gemini-embedding-001"
    assert GEMINI_EMBEDDING_FALLBACK_MODEL_PATH.endswith("gemini-embedding-2-preview")
    assert MEMORY_ENGINE_EMBEDDING_MODEL == "text-embedding-004"
