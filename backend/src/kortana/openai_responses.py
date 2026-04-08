"""Shared OpenAI text generation helpers with GPT-5 Responses API support."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, AsyncIterator

from src.kortana.provider_model_defaults import (
    OPENAI_GPT_54_MINI_MODEL,
    OPENAI_GPT_54_MODEL,
    OPENAI_GPT_54_NANO_MODEL,
)


@dataclass(frozen=True)
class OpenAITextGenerationResult:
    """Normalized text generation result across Responses and chat APIs."""

    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    response_id: str | None = None
    phase: str | None = None
    used_previous_response_id: bool = False


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


def _response_id(response: Any) -> str | None:
    raw_id = getattr(response, "id", None)
    if raw_id is None:
        return None
    return str(raw_id)


def _response_phase(response: Any) -> str | None:
    output = getattr(response, "output", None) or []
    for item in reversed(output):
        role = getattr(item, "role", None)
        if role is None and isinstance(item, dict):
            role = item.get("role")
        if role != "assistant":
            continue

        phase = getattr(item, "phase", None)
        if phase is None and isinstance(item, dict):
            phase = item.get("phase")
        if phase:
            return str(phase)

    return "final_answer" if _response_text(response) else None


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
    previous_response_id: str | None,
    history: list[dict[str, str]] | None,
) -> dict[str, Any]:
    reasoning_effort = _default_reasoning_effort(model_name)
    if previous_response_id:
        input_payload: str | list[dict[str, str]] = [{"role": "user", "content": prompt}]
    else:
        input_messages: list[dict[str, str]] = []
        for message in history or []:
            role = str(message.get("role", "")).strip()
            content = str(message.get("content", "")).strip()
            if not role or not content:
                continue
            input_message = {"role": role, "content": content}
            if role == "assistant":
                input_message["phase"] = str(
                    message.get("phase", "final_answer") or "final_answer"
                )
            input_messages.append(input_message)
        input_messages.append({"role": "user", "content": prompt})
        input_payload = input_messages if input_messages else prompt

    kwargs: dict[str, Any] = {
        "model": model_name,
        "input": input_payload,
        "max_output_tokens": max_output_tokens,
        "reasoning": {"effort": reasoning_effort},
        "text": {"verbosity": _default_verbosity(model_name)},
    }
    if system:
        kwargs["instructions"] = system
    if timeout is not None:
        kwargs["timeout"] = timeout
    if previous_response_id:
        kwargs["previous_response_id"] = previous_response_id
    if temperature is not None and reasoning_effort == "none":
        kwargs["temperature"] = temperature
    return kwargs


async def async_generate_turn(
    client: Any,
    *,
    model_name: str,
    prompt: str,
    system: str | None = None,
    max_output_tokens: int = 1024,
    temperature: float | None = None,
    timeout: float | None = None,
    previous_response_id: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> OpenAITextGenerationResult:
    """Generate one text turn with GPT-5 Responses API or chat completions."""
    if is_gpt5_family_model(model_name):
        response = await client.responses.create(
            **_build_responses_kwargs(
                model_name=model_name,
                prompt=prompt,
                system=system,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
                timeout=timeout,
                previous_response_id=previous_response_id,
                history=history,
            )
        )
        input_tokens, output_tokens = _usage_tokens(response)
        return OpenAITextGenerationResult(
            text=_response_text(response),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            response_id=_response_id(response),
            phase=_response_phase(response),
            used_previous_response_id=bool(previous_response_id),
        )

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    for message in history or []:
        role = str(message.get("role", "")).strip()
        content = str(message.get("content", "")).strip()
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": prompt})
    response = await client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_tokens=max_output_tokens,
        temperature=temperature,
        timeout=timeout,
    )
    input_tokens, output_tokens = _chat_usage_tokens(response)
    return OpenAITextGenerationResult(
        text=_chat_message_content(response),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        response_id=None,
        phase="final_answer",
        used_previous_response_id=False,
    )


async def async_generate_text(
    client: Any,
    *,
    model_name: str,
    prompt: str,
    system: str | None = None,
    max_output_tokens: int = 1024,
    temperature: float | None = None,
    timeout: float | None = None,
    previous_response_id: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> tuple[str, int | None, int | None]:
    """Compatibility wrapper returning only text and token counts."""
    result = await async_generate_turn(
        client,
        model_name=model_name,
        prompt=prompt,
        system=system,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        timeout=timeout,
        previous_response_id=previous_response_id,
        history=history,
    )
    return result.text, result.input_tokens, result.output_tokens


async def async_stream_turn(
    client: Any,
    *,
    model_name: str,
    prompt: str,
    system: str | None = None,
    max_output_tokens: int = 1024,
    temperature: float | None = None,
    timeout: float | None = None,
    previous_response_id: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Stream GPT-5 Responses text deltas and finish with a normalized result."""
    if is_gpt5_family_model(model_name):
        async with client.responses.stream(
            **_build_responses_kwargs(
                model_name=model_name,
                prompt=prompt,
                system=system,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
                timeout=timeout,
                previous_response_id=previous_response_id,
                history=history,
            )
        ) as stream:
            async for event in stream:
                if getattr(event, "type", None) == "response.output_text.delta":
                    delta = str(getattr(event, "delta", "") or "")
                    if delta:
                        yield {"type": "delta", "delta": delta}

            response = await stream.get_final_response()

        input_tokens, output_tokens = _usage_tokens(response)
        yield {
            "type": "completed",
            "result": OpenAITextGenerationResult(
                text=_response_text(response),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                response_id=_response_id(response),
                phase=_response_phase(response),
                used_previous_response_id=bool(previous_response_id),
            ),
        }
        return

    result = await async_generate_turn(
        client,
        model_name=model_name,
        prompt=prompt,
        system=system,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        timeout=timeout,
        previous_response_id=previous_response_id,
        history=history,
    )
    yield {"type": "completed", "result": result}


def sync_generate_turn(
    client: Any,
    *,
    model_name: str,
    prompt: str,
    system: str | None = None,
    max_output_tokens: int = 1024,
    temperature: float | None = None,
    previous_response_id: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> OpenAITextGenerationResult:
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
                previous_response_id=previous_response_id,
                history=history,
            )
        )
        input_tokens, output_tokens = _usage_tokens(response)
        return OpenAITextGenerationResult(
            text=_response_text(response),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            response_id=_response_id(response),
            phase=_response_phase(response),
            used_previous_response_id=bool(previous_response_id),
        )

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    for message in history or []:
        role = str(message.get("role", "")).strip()
        content = str(message.get("content", "")).strip()
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_tokens=max_output_tokens,
        temperature=temperature,
    )
    input_tokens, output_tokens = _chat_usage_tokens(response)
    return OpenAITextGenerationResult(
        text=_chat_message_content(response),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        response_id=None,
        phase="final_answer",
        used_previous_response_id=False,
    )


def sync_generate_text(
    client: Any,
    *,
    model_name: str,
    prompt: str,
    system: str | None = None,
    max_output_tokens: int = 1024,
    temperature: float | None = None,
    previous_response_id: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> tuple[str, int | None, int | None]:
    """Compatibility wrapper returning only text and token counts."""
    result = sync_generate_turn(
        client,
        model_name=model_name,
        prompt=prompt,
        system=system,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        previous_response_id=previous_response_id,
        history=history,
    )
    return result.text, result.input_tokens, result.output_tokens
