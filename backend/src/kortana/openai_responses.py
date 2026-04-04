"""Shared OpenAI text generation helpers with GPT-5 Responses API support."""

from __future__ import annotations

from typing import Any

from src.kortana.provider_model_defaults import (
    OPENAI_GPT_54_MINI_MODEL,
    OPENAI_GPT_54_MODEL,
    OPENAI_GPT_54_NANO_MODEL,
)


def is_gpt5_family_model(model_name: str) -> bool:
    """Return True when the model belongs to the GPT-5 family."""
    return model_name.strip().startswith("gpt-5")


def _default_reasoning_effort(model_name: str) -> str:
    normalized = model_name.strip()
    if normalized == OPENAI_GPT_54_NANO_MODEL:
        return "none"
    if normalized == OPENAI_GPT_54_MINI_MODEL:
        return "low"
    if normalized == OPENAI_GPT_54_MODEL:
        return "medium"
    return "none"


def _default_verbosity(model_name: str) -> str:
    normalized = model_name.strip()
    if normalized == OPENAI_GPT_54_NANO_MODEL:
        return "low"
    if normalized == OPENAI_GPT_54_MINI_MODEL:
        return "medium"
    if normalized == OPENAI_GPT_54_MODEL:
        return "medium"
    return "medium"


def _usage_tokens(response: Any) -> tuple[int | None, int | None]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return None, None

    return (
        getattr(usage, "input_tokens", None),
        getattr(usage, "output_tokens", None),
    )


def _response_text(response: Any) -> str:
    return str(getattr(response, "output_text", "") or "")


def _chat_message_content(response: Any) -> str:
    choices = getattr(response, "choices", None) or []
    if not choices:
        return ""
    return str(getattr(choices[0].message, "content", "") or "")


def _chat_usage_tokens(response: Any) -> tuple[int | None, int | None]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return None, None
    return (
        getattr(usage, "prompt_tokens", None),
        getattr(usage, "completion_tokens", None),
    )


def _build_responses_kwargs(
    *,
    model_name: str,
    prompt: str,
    system: str | None,
    max_output_tokens: int,
    temperature: float | None,
    timeout: float | None,
) -> dict[str, Any]:
    reasoning_effort = _default_reasoning_effort(model_name)
    kwargs: dict[str, Any] = {
        "model": model_name,
        "input": prompt,
        "max_output_tokens": max_output_tokens,
        "reasoning": {"effort": reasoning_effort},
        "text": {"verbosity": _default_verbosity(model_name)},
    }
    if system:
        kwargs["instructions"] = system
    if timeout is not None:
        kwargs["timeout"] = timeout
    if temperature is not None and reasoning_effort == "none":
        kwargs["temperature"] = temperature
    return kwargs


async def async_generate_text(
    client: Any,
    *,
    model_name: str,
    prompt: str,
    system: str | None = None,
    max_output_tokens: int = 1024,
    temperature: float | None = None,
    timeout: float | None = None,
) -> tuple[str, int | None, int | None]:
    """Generate text using Responses API for GPT-5 models, chat completions otherwise."""
    if is_gpt5_family_model(model_name):
        response = await client.responses.create(
            **_build_responses_kwargs(
                model_name=model_name,
                prompt=prompt,
                system=system,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
                timeout=timeout,
            )
        )
        input_tokens, output_tokens = _usage_tokens(response)
        return _response_text(response), input_tokens, output_tokens

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    response = await client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_tokens=max_output_tokens,
        temperature=temperature,
        timeout=timeout,
    )
    input_tokens, output_tokens = _chat_usage_tokens(response)
    return _chat_message_content(response), input_tokens, output_tokens


def sync_generate_text(
    client: Any,
    *,
    model_name: str,
    prompt: str,
    system: str | None = None,
    max_output_tokens: int = 1024,
    temperature: float | None = None,
) -> tuple[str, int | None, int | None]:
    """Sync variant for worker-style OpenAI clients."""
    if is_gpt5_family_model(model_name):
        response = client.responses.create(
            **_build_responses_kwargs(
                model_name=model_name,
                prompt=prompt,
                system=system,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
                timeout=None,
            )
        )
        input_tokens, output_tokens = _usage_tokens(response)
        return _response_text(response), input_tokens, output_tokens

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_tokens=max_output_tokens,
        temperature=temperature,
    )
    input_tokens, output_tokens = _chat_usage_tokens(response)
    return _chat_message_content(response), input_tokens, output_tokens
