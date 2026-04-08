"""Tests for the canonical provider model defaults catalog."""

from src.kortana.provider_model_defaults import (
    AI_CONSENSUS_DEFAULTS,
    ANTHROPIC_SONNET_MODEL,
    DEFAULT_CORE_MODEL_CATALOG,
    GEMINI_25_FLASH_MODEL,
    GEMINI_DEFAULT_MODEL,
    GEMINI_DISCOVERY_FALLBACK_MODELS,
    GEMINI_EMBEDDING_FALLBACK_MODEL_PATH,
    GEMINI_EMBEDDING_MODEL_NAME,
    GEMINI_EMBEDDING_MODEL_PATH,
    GEMINI_FLASH_LITE_LATEST_MODEL,
    GEMINI_FLASH_LITE_MODEL,
    LLM_ROUTER_DEFAULTS,
    LLM_ROUTER_FALLBACK_ORDER,
    LLM_ROUTER_GEMINI_MODEL,
    MEMORY_ENGINE_EMBEDDING_MODEL,
    MULTI_MODEL_DEFAULTS,
    OPENAI_FAST_MODEL,
    OPENAI_GPT_54_MINI_MODEL,
    OPENAI_GPT_54_MODEL,
    OPENAI_GPT_54_NANO_MODEL,
)


def test_llm_router_defaults_match_expected_primary_and_fallbacks() -> None:
    assert LLM_ROUTER_DEFAULTS.gemini == "gemini-2.5-flash"
    assert LLM_ROUTER_FALLBACK_ORDER == (
        "mixtral-8x7b-32768",
        OPENAI_GPT_54_MINI_MODEL,
        ANTHROPIC_SONNET_MODEL,
    )


def test_ai_consensus_defaults_match_expected_provider_models() -> None:
    assert AI_CONSENSUS_DEFAULTS.openai == OPENAI_GPT_54_MINI_MODEL
    assert AI_CONSENSUS_DEFAULTS.anthropic == ANTHROPIC_SONNET_MODEL
    assert AI_CONSENSUS_DEFAULTS.groq == "llama-3.3-70b-versatile"
    assert AI_CONSENSUS_DEFAULTS.openrouter == "meta-llama/llama-3-70b-instruct"


def test_multi_model_defaults_match_expected_provider_models() -> None:
    assert MULTI_MODEL_DEFAULTS.openai == OPENAI_FAST_MODEL
    assert MULTI_MODEL_DEFAULTS.anthropic == ANTHROPIC_SONNET_MODEL
    assert MULTI_MODEL_DEFAULTS.groq == "mixtral-8x7b-32768"
    assert MULTI_MODEL_DEFAULTS.openrouter == "meta-llama/llama-2-70b-chat"


def test_gemini_discovery_fallbacks_are_all_core_catalog_models() -> None:
    assert GEMINI_DEFAULT_MODEL == "gemini-2.5-flash-lite"
    assert set(GEMINI_DISCOVERY_FALLBACK_MODELS).issubset(DEFAULT_CORE_MODEL_CATALOG)


def test_gemini_discovery_fallbacks_prefer_stable_flash_models_first() -> None:
    assert GEMINI_DISCOVERY_FALLBACK_MODELS[:5] == (
        GEMINI_DEFAULT_MODEL,
        GEMINI_FLASH_LITE_MODEL,
        GEMINI_25_FLASH_MODEL,
        LLM_ROUTER_GEMINI_MODEL,
        GEMINI_FLASH_LITE_LATEST_MODEL,
    )


def test_openai_gpt54_family_is_in_core_catalog() -> None:
    assert OPENAI_GPT_54_MODEL in DEFAULT_CORE_MODEL_CATALOG
    assert OPENAI_GPT_54_MINI_MODEL in DEFAULT_CORE_MODEL_CATALOG
    assert OPENAI_GPT_54_NANO_MODEL in DEFAULT_CORE_MODEL_CATALOG


def test_embedding_model_constants_are_consistent() -> None:
    assert GEMINI_EMBEDDING_MODEL_PATH == "models/gemini-embedding-001"
    assert GEMINI_EMBEDDING_MODEL_NAME == "gemini-embedding-001"
    assert GEMINI_EMBEDDING_FALLBACK_MODEL_PATH.endswith("gemini-embedding-2-preview")
    assert MEMORY_ENGINE_EMBEDDING_MODEL == "gemini-embedding-001"
