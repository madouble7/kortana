"""Canonical provider model defaults for each Kor'tana subsystem."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderModelDefaults:
    """Default provider model selections for a specific subsystem."""

    gemini: str = ""
    openai: str = ""
    anthropic: str = ""
    groq: str = ""
    openrouter: str = ""


ANTHROPIC_SONNET_MODEL = "claude-3-5-sonnet-20241022"
GEMINI_DEFAULT_MODEL = "gemini-2.5-flash-lite"
GEMINI_FLASH_LITE_MODEL = "gemini-3.1-flash-lite-preview"
GEMINI_FLASH_LITE_LATEST_MODEL = "gemini-flash-lite-latest"
GEMINI_25_FLASH_MODEL = "gemini-2.5-flash"
GEMINI_25_PRO_MODEL = "gemini-2.5-pro"
GEMINI_20_FLASH_LITE_MODEL = "gemini-2.5-flash-lite"  # was 2.0 (deprecated)
GEMINI_15_FLASH_MODEL = "gemini-2.5-flash"  # was 1.5 (deprecated)
GEMINI_15_PRO_MODEL = "gemini-2.5-pro"  # was 1.5 (deprecated)
GROQ_MIXTRAL_MODEL = "mixtral-8x7b-32768"
GROQ_LLAMA_VERSATILE_MODEL = "llama-3.3-70b-versatile"
OPENAI_GPT_35_TURBO_MODEL = "gpt-3.5-turbo"
OPENAI_GPT_4O_MODEL = "gpt-4o"
OPENAI_GPT_4O_MINI_MODEL = "gpt-4o-mini"
OPENAI_GPT_54_MODEL = "gpt-4o"  # gpt-5.4 doesn't exist yet
OPENAI_GPT_54_MINI_MODEL = "gpt-4o-mini"  # gpt-5.4-mini doesn't exist yet
OPENAI_GPT_54_NANO_MODEL = "gpt-4o-mini"  # gpt-5.4-nano doesn't exist yet
OPENAI_FRONTIER_MODEL = OPENAI_GPT_54_MODEL
OPENAI_OPERATIONAL_MODEL = OPENAI_GPT_54_MINI_MODEL
OPENAI_FAST_MODEL = OPENAI_GPT_54_NANO_MODEL
OPENROUTER_AUTO_MODEL = "openrouter/auto"
OPENROUTER_LLAMA2_CHAT_MODEL = "meta-llama/llama-2-70b-chat"
OPENROUTER_LLAMA3_INSTRUCT_MODEL = "meta-llama/llama-3-70b-instruct"
LLM_ROUTER_GEMINI_MODEL = "gemini-2.5-flash"  # was 2.0 (deprecated)
GEMINI_EMBEDDING_MODEL_PATH = "models/gemini-embedding-001"
GEMINI_EMBEDDING_MODEL_NAME = "gemini-embedding-001"
GEMINI_EMBEDDING_FALLBACK_MODEL_PATH = "models/gemini-embedding-2-preview"
MEMORY_ENGINE_EMBEDDING_MODEL = "text-embedding-004"

GEMINI_DISCOVERY_FALLBACK_MODELS = (
    GEMINI_DEFAULT_MODEL,         # gemini-2.5-flash-lite (cheapest stable)
    GEMINI_FLASH_LITE_MODEL,      # gemini-3.1-flash-lite-preview
    GEMINI_25_FLASH_MODEL,        # gemini-2.5-flash
    LLM_ROUTER_GEMINI_MODEL,      # gemini-2.5-flash (same)
    GEMINI_FLASH_LITE_LATEST_MODEL,
    GEMINI_25_PRO_MODEL,          # gemini-2.5-pro (quality fallback)
)

DEFAULT_CORE_MODEL_CATALOG = frozenset(
    {
        *GEMINI_DISCOVERY_FALLBACK_MODELS,
        OPENAI_GPT_54_MODEL,
        OPENAI_GPT_54_MINI_MODEL,
        OPENAI_GPT_54_NANO_MODEL,
        OPENAI_GPT_4O_MODEL,
        OPENAI_GPT_4O_MINI_MODEL,
        OPENAI_GPT_35_TURBO_MODEL,
        ANTHROPIC_SONNET_MODEL,
        GROQ_MIXTRAL_MODEL,
        GROQ_LLAMA_VERSATILE_MODEL,
        OPENROUTER_LLAMA2_CHAT_MODEL,
        OPENROUTER_LLAMA3_INSTRUCT_MODEL,
        OPENROUTER_AUTO_MODEL,
    }
)


LLM_ROUTER_DEFAULTS = ProviderModelDefaults(
    gemini=LLM_ROUTER_GEMINI_MODEL,
    openai=OPENAI_GPT_4O_MINI_MODEL,
    anthropic=ANTHROPIC_SONNET_MODEL,
    groq=GROQ_MIXTRAL_MODEL,
)

# Cost-efficient fallback: free Groq first, then cheap OpenAI, Anthropic last resort
LLM_ROUTER_FALLBACK_ORDER = tuple(
    model_name
    for model_name in (
        LLM_ROUTER_DEFAULTS.groq,
        LLM_ROUTER_DEFAULTS.openai,
        LLM_ROUTER_DEFAULTS.anthropic,
    )
    if model_name
)

AI_CONSENSUS_DEFAULTS = ProviderModelDefaults(
    openai=OPENAI_GPT_4O_MINI_MODEL,
    anthropic=ANTHROPIC_SONNET_MODEL,
    groq=GROQ_LLAMA_VERSATILE_MODEL,
    openrouter=OPENROUTER_LLAMA3_INSTRUCT_MODEL,
)

MULTI_MODEL_DEFAULTS = ProviderModelDefaults(
    openai=OPENAI_GPT_4O_MINI_MODEL,
    anthropic=ANTHROPIC_SONNET_MODEL,
    groq=GROQ_MIXTRAL_MODEL,
    openrouter=OPENROUTER_LLAMA2_CHAT_MODEL,
)

COST_ROUTER_DEFAULTS = ProviderModelDefaults(
    openai=OPENAI_FAST_MODEL,
    anthropic=ANTHROPIC_SONNET_MODEL,
    groq=GROQ_MIXTRAL_MODEL,
    openrouter=OPENROUTER_AUTO_MODEL,
)

API_INTEGRATION_FALLBACK_DEFAULTS = ProviderModelDefaults(
    openai=OPENAI_FAST_MODEL,
    anthropic=ANTHROPIC_SONNET_MODEL,
    groq=GROQ_MIXTRAL_MODEL,
)
