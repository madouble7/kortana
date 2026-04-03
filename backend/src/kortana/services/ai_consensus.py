"""
AI Consensus Engine — Multi-Provider Intelligence Router

Queries multiple AI providers in parallel, scores responses by quality,
and synthesises a consensus answer. Supports three modes:

  - FASTEST:   Return the first successful response (lowest latency)
  - BEST:      Query all providers, score & pick the best single answer
  - CONSENSUS: Query all providers, synthesise a unified answer from all

Providers are ranked dynamically based on historical success rate and latency.
"""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import httpx

from src.kortana.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class ConsensusMode(str, Enum):
    FASTEST = "fastest"
    BEST = "best"
    CONSENSUS = "consensus"


@dataclass
class ProviderResponse:
    provider: str
    text: str
    latency: float  # seconds
    success: bool = True
    error: str | None = None


@dataclass
class ProviderStats:
    calls: int = 0
    successes: int = 0
    total_latency: float = 0.0
    last_failure: float | None = None

    @property
    def success_rate(self) -> float:
        return self.successes / max(self.calls, 1)

    @property
    def avg_latency(self) -> float:
        return self.total_latency / max(self.successes, 1)

    @property
    def score(self) -> float:
        """Higher is better. Balances reliability vs speed."""
        return self.success_rate * 100 - self.avg_latency


@dataclass
class ConsensusResult:
    mode: str
    answer: str
    provider_used: str | list[str]
    responses: list[dict[str, Any]] = field(default_factory=list)
    latency: float = 0.0
    providers_queried: int = 0
    providers_succeeded: int = 0


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class AIConsensusEngine:
    """Multi-provider AI consensus engine with dynamic ranking."""

    def __init__(self) -> None:
        self._providers: dict[str, dict[str, Any]] = {}
        self._stats: dict[str, ProviderStats] = {}
        self._initialized = False

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        self._init_providers()
        self._initialized = True
        logger.info(
            f"Consensus engine online — {len(self._providers)} provider(s): "
            f"{', '.join(self._providers)}"
        )

    # ----- provider init (lazy, identical pattern to multi_model_ai) -----

    def _init_providers(self) -> None:
        self._try_gemini()
        self._try_openai()
        self._try_anthropic()
        self._try_groq()
        self._try_openrouter()

    def _try_gemini(self) -> None:
        key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not key:
            return
        try:
            from google.genai import Client

            from src.kortana.services.gemini_config import get_model_name

            client = Client(api_key=key)
            model = get_model_name()
            self._providers["gemini"] = {"client": client, "model": model}
            self._stats["gemini"] = ProviderStats()
        except Exception as e:
            logger.warning(f"Gemini init failed: {e}")

    def _try_openai(self) -> None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            return
        try:
            import openai

            client = openai.AsyncOpenAI(
                api_key=key,
                http_client=httpx.AsyncClient(timeout=30.0),
            )
            self._providers["openai"] = {"client": client, "model": "gpt-4o-mini"}
            self._stats["openai"] = ProviderStats()
        except Exception as e:
            logger.warning(f"OpenAI init failed: {e}")

    def _try_anthropic(self) -> None:
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            return
        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=key)
            self._providers["anthropic"] = {
                "client": client,
                "model": "claude-3-5-sonnet-20241022",
            }
            self._stats["anthropic"] = ProviderStats()
        except Exception as e:
            logger.warning(f"Anthropic init failed: {e}")

    def _try_groq(self) -> None:
        key = os.getenv("GROQ_API_KEY")
        if not key:
            return
        try:
            import groq

            client = groq.AsyncGroq(api_key=key)
            self._providers["groq"] = {
                "client": client,
                "model": "llama-3.3-70b-versatile",
            }
            self._stats["groq"] = ProviderStats()
        except Exception as e:
            logger.warning(f"Groq init failed: {e}")

    def _try_openrouter(self) -> None:
        key = os.getenv("OPENROUTER_API_KEY")
        if not key:
            return
        try:
            import openai as openai_mod

            client = openai_mod.AsyncOpenAI(
                api_key=key,
                base_url="https://openrouter.ai/api/v1",
                http_client=httpx.AsyncClient(timeout=30.0),
            )
            self._providers["openrouter"] = {
                "client": client,
                "model": "meta-llama/llama-3-70b-instruct",
            }
            self._stats["openrouter"] = ProviderStats()
        except Exception as e:
            logger.warning(f"OpenRouter init failed: {e}")

    # ----- provider dispatch -----

    async def _call_provider(
        self, name: str, prompt: str, system: str | None = None, max_tokens: int = 1024
    ) -> ProviderResponse:
        prov = self._providers[name]
        t0 = time.monotonic()
        try:
            text = await self._dispatch(name, prov, prompt, system, max_tokens)
            latency = time.monotonic() - t0
            self._record(name, success=True, latency=latency)
            return ProviderResponse(provider=name, text=text, latency=latency)
        except Exception as e:
            latency = time.monotonic() - t0
            self._record(name, success=False, latency=latency)
            return ProviderResponse(
                provider=name, text="", latency=latency, success=False, error=str(e)
            )

    async def _dispatch(
        self,
        name: str,
        prov: dict[str, Any],
        prompt: str,
        system: str | None,
        max_tokens: int,
    ) -> str:
        if name == "gemini":
            resp = prov["client"].models.generate_content(
                model=f"models/{prov['model']}", contents=prompt
            )
            return resp.text or ""

        # OpenAI-compatible (openai / groq / openrouter)
        if name in ("openai", "groq", "openrouter"):
            messages: list[dict[str, str]] = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            resp = await prov["client"].chat.completions.create(
                model=prov["model"], messages=messages, max_tokens=max_tokens
            )
            return resp.choices[0].message.content or "" if resp.choices else ""

        if name == "anthropic":
            kwargs: dict[str, Any] = {
                "model": prov["model"],
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                kwargs["system"] = system
            resp = await prov["client"].messages.create(**kwargs)
            return resp.content[0].text if resp.content else ""

        raise ValueError(f"Unknown provider: {name}")

    def _record(self, name: str, *, success: bool, latency: float) -> None:
        s = self._stats[name]
        s.calls += 1
        if success:
            s.successes += 1
            s.total_latency += latency
        else:
            s.last_failure = time.time()

    def _ranked_providers(self) -> list[str]:
        """Return provider names sorted by score (best first)."""
        return sorted(self._stats, key=lambda n: self._stats[n].score, reverse=True)

    # ----- public API -----

    async def query(
        self,
        prompt: str,
        *,
        mode: ConsensusMode = ConsensusMode.BEST,
        system: str | None = None,
        max_tokens: int = 1024,
        timeout: float = 30.0,
    ) -> ConsensusResult:
        """Query AI providers according to the selected consensus mode."""
        self._ensure_initialized()

        if not self._providers:
            return ConsensusResult(
                mode=mode.value,
                answer="[ERROR] No AI providers available",
                provider_used="none",
            )

        if mode == ConsensusMode.FASTEST:
            return await self._query_fastest(prompt, system, max_tokens, timeout)
        elif mode == ConsensusMode.BEST:
            return await self._query_best(prompt, system, max_tokens, timeout)
        else:
            return await self._query_consensus(prompt, system, max_tokens, timeout)

    async def _query_fastest(
        self, prompt: str, system: str | None, max_tokens: int, timeout: float
    ) -> ConsensusResult:
        """Return the first successful response, skipping fast failures."""
        ranked = self._ranked_providers()
        t0 = time.monotonic()
        deadline = t0 + timeout

        pending: set[asyncio.Task[ProviderResponse]] = {
            asyncio.create_task(self._call_provider(name, prompt, system, max_tokens))
            for name in ranked
        }

        try:
            while pending:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                done, pending = await asyncio.wait(
                    pending,
                    timeout=remaining,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if not done:
                    break  # timed out
                for t in done:
                    resp: ProviderResponse = t.result()
                    if resp.success:
                        # Cancel remaining and return winner
                        for p in pending:
                            p.cancel()
                        return ConsensusResult(
                            mode="fastest",
                            answer=resp.text,
                            provider_used=resp.provider,
                            latency=time.monotonic() - t0,
                            providers_queried=len(ranked),
                            providers_succeeded=1,
                        )
        finally:
            for t in pending:
                t.cancel()

        return ConsensusResult(
            mode="fastest",
            answer="[ERROR] All providers failed or timed out",
            provider_used="none",
            providers_queried=len(ranked),
        )

    async def _query_best(
        self, prompt: str, system: str | None, max_tokens: int, timeout: float
    ) -> ConsensusResult:
        """Query all providers, pick the longest/best single answer."""
        responses = await self._query_all(prompt, system, max_tokens, timeout)
        succeeded = [r for r in responses if r.success]

        if not succeeded:
            return ConsensusResult(
                mode="best",
                answer="[ERROR] All providers failed",
                provider_used="none",
                providers_queried=len(responses),
            )

        # Score: prefer longer answers from faster, more reliable providers
        best = max(
            succeeded,
            key=lambda r: len(r.text) * 0.3 + (1 / max(r.latency, 0.01)) * 0.7,
        )

        return ConsensusResult(
            mode="best",
            answer=best.text,
            provider_used=best.provider,
            responses=[
                {
                    "provider": r.provider,
                    "latency": round(r.latency, 3),
                    "success": r.success,
                    "length": len(r.text),
                }
                for r in responses
            ],
            latency=best.latency,
            providers_queried=len(responses),
            providers_succeeded=len(succeeded),
        )

    async def _query_consensus(
        self, prompt: str, system: str | None, max_tokens: int, timeout: float
    ) -> ConsensusResult:
        """Query all providers, then synthesise a unified answer."""
        responses = await self._query_all(prompt, system, max_tokens, timeout)
        succeeded = [r for r in responses if r.success and r.text.strip()]

        if not succeeded:
            return ConsensusResult(
                mode="consensus",
                answer="[ERROR] All providers failed",
                provider_used="none",
                providers_queried=len(responses),
            )

        if len(succeeded) == 1:
            return ConsensusResult(
                mode="consensus",
                answer=succeeded[0].text,
                provider_used=succeeded[0].provider,
                providers_queried=len(responses),
                providers_succeeded=1,
            )

        # Use the top-ranked available provider to synthesise
        synthesis_prompt = self._build_synthesis_prompt(prompt, succeeded)
        synthesiser = self._ranked_providers()[0]
        synth_resp = await self._call_provider(
            synthesiser, synthesis_prompt, system=None, max_tokens=max_tokens
        )

        providers_used = [r.provider for r in succeeded]
        return ConsensusResult(
            mode="consensus",
            answer=synth_resp.text if synth_resp.success else succeeded[0].text,
            provider_used=providers_used,
            responses=[
                {
                    "provider": r.provider,
                    "latency": round(r.latency, 3),
                    "success": r.success,
                    "length": len(r.text),
                }
                for r in responses
            ],
            latency=max(r.latency for r in responses),
            providers_queried=len(responses),
            providers_succeeded=len(succeeded),
        )

    async def _query_all(
        self, prompt: str, system: str | None, max_tokens: int, timeout: float
    ) -> list[ProviderResponse]:
        ranked = self._ranked_providers()
        coros = [
            self._call_provider(name, prompt, system, max_tokens) for name in ranked
        ]
        results = await asyncio.gather(*coros, return_exceptions=True)
        out: list[ProviderResponse] = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                out.append(
                    ProviderResponse(
                        provider=ranked[i],
                        text="",
                        latency=0,
                        success=False,
                        error=str(r),
                    )
                )
            else:
                out.append(r)
        return out

    @staticmethod
    def _build_synthesis_prompt(
        original: str, responses: list[ProviderResponse]
    ) -> str:
        parts = [
            "we are a synthesis engine. Multiple AI providers answered the same question.",
            "Combine the best elements of each response into one authoritative answer.",
            "Be concise and accurate. Do not mention the providers by name.\n",
            f"ORIGINAL QUESTION:\n{original}\n",
        ]
        for i, r in enumerate(responses, 1):
            parts.append(f"RESPONSE {i} ({r.provider}):\n{r.text}\n")
        parts.append("YOUR SYNTHESISED ANSWER:")
        return "\n".join(parts)

    # ----- introspection -----

    def get_status(self) -> dict[str, Any]:
        self._ensure_initialized()
        return {
            "providers": {
                name: {
                    "model": self._providers[name].get("model", "unknown"),
                    "calls": self._stats[name].calls,
                    "success_rate": round(self._stats[name].success_rate, 3),
                    "avg_latency": round(self._stats[name].avg_latency, 3),
                    "score": round(self._stats[name].score, 2),
                }
                for name in self._providers
            },
            "ranking": self._ranked_providers(),
            "total_providers": len(self._providers),
        }


# Singleton
_engine: AIConsensusEngine | None = None


def get_consensus_engine() -> AIConsensusEngine:
    global _engine
    if _engine is None:
        _engine = AIConsensusEngine()
    return _engine
