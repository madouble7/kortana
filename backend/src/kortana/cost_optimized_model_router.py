"""
KOR'TANA Cost-Optimized Multi-Model Router

Maximizes autonomy and cost efficiency by intelligently routing to:
- Groq (free tier, blazingly fast, unlimited)
- OpenRouter (cost-efficient model aggregation)
- Gemini (free tier with quota limits)
- Claude/Anthropic (for critical decisions, premium quality)
- OpenAI (fallback for specialized tasks)

Strategy:
1. Groq for all standard inference (free, fast, no quota limits)
2. OpenRouter for fallback/load balancing (cost-aware routing)
3. Gemini for quota-dependent tasks (budget tracking)
4. Claude for decision verification (critical path only)
5. OpenAI fast lane for low-stakes summaries and lightweight analysis
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from src.kortana.logger import get_logger
from src.kortana.model_lane_policy import (
    describe_model_lane,
    get_active_model_lane,
    model_allowed,
)
from src.kortana.provider_model_defaults import COST_ROUTER_DEFAULTS
from src.kortana.services.gemini_config import get_model_name

logger = get_logger(__name__)


class ModelProvider(Enum):
    """Available model providers"""

    OLLAMA = "ollama"  # Local, free, unlimited, private
    GROQ = "groq"  # Free, fast, unlimited
    OPENROUTER = "openrouter"  # Cost-efficient routing
    GEMINI = "gemini"  # Free tier with quotas
    CLAUDE = "claude"  # Premium, for critical decisions
    OPENAI = "openai"  # Expensive, use sparingly


class TaskType(Enum):
    """Task categories with optimal model selection"""

    CODE_GENERATION = "code_generation"  # Best: Groq, Fallback: OpenRouter
    ANALYSIS = "analysis"  # Best: Groq, Fallback: Gemini
    DECISION = "decision"  # Best: Claude, Fallback: Groq
    VERIFICATION = "verification"  # Best: Claude (consensus voting)
    PLANNING = "planning"  # Best: Groq, Fallback: OpenRouter
    SUMMARY = "summary"  # Best: Groq
    RETRIEVAL = "retrieval"  # Best: Groq
    CORRECTION = "correction"  # Best: Claude


@dataclass
class ModelConfig:
    """Configuration for each model provider"""

    provider: ModelProvider
    api_key: str
    model_name: str
    cost_per_1k_input: float = 0.0  # USD per 1000 input tokens
    cost_per_1k_output: float = 0.0  # USD per 1000 output tokens
    quota_limit: Optional[int] = None  # Requests per period
    quota_period_seconds: int = 3600  # Period for quota
    max_tokens: int = 4096
    priority: int = 0  # Lower = higher priority
    is_free_tier: bool = False
    lane: str = "core"


@dataclass
class CostEstimate:
    """Cost tracking and estimation"""

    provider: ModelProvider
    task_type: TaskType
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    estimated_cost: float = 0.0
    daily_spend: float = field(default_factory=float)
    monthly_spend: float = field(default_factory=float)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_requests: int = 0
    last_task_type: str | None = None
    last_used_at: str | None = None
    last_reset: datetime = field(default_factory=datetime.utcnow)

    def calculate_cost(self, config: ModelConfig) -> float:
        """Calculate total cost for this request"""
        input_cost = self.estimated_input_tokens / 1000 * config.cost_per_1k_input
        output_cost = self.estimated_output_tokens / 1000 * config.cost_per_1k_output
        return input_cost + output_cost

    def record_usage(
        self,
        *,
        cost: float,
        task_type: TaskType,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """Update rolling spend and token counters for a completed request."""
        now = datetime.utcnow()
        if (now - self.last_reset).days >= 1:
            self.daily_spend = 0.0
            self.last_reset = now
        self.daily_spend += cost
        self.monthly_spend += cost
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_requests += 1
        self.last_task_type = task_type.value
        self.last_used_at = now.isoformat()


class CostOptimizedModelRouter:
    """
    Intelligently routes requests to minimize costs while maximizing autonomy.

    Priority Order by Task Type:
    - FREE TIER FIRST: Groq (unlimited, fast)
    - FALLBACK 1: OpenRouter (cost-efficient)
    - FALLBACK 2: Gemini (free tier, quota-limited)
    - FALLBACK 3: Claude (critical decisions only)
    - FALLBACK 4: OpenAI fast lane (paid, low-latency worker path)
    """

    def __init__(self) -> None:
        self.configs: dict[ModelProvider, ModelConfig] = {}
        self.cost_tracking: dict[ModelProvider, CostEstimate] = {}
        self.request_counts: dict[ModelProvider, int] = {}
        self.provider_cooldowns: dict[ModelProvider, datetime] = {}
        self.provider_last_errors: dict[ModelProvider, str] = {}
        self.model_usage_lane = get_active_model_lane()
        self.init_providers()

    def _get_cooldown_seconds(self, provider: ModelProvider) -> int:
        """Return active cooldown seconds remaining for a provider."""
        cooldown_until = self.provider_cooldowns.get(provider)
        if cooldown_until is None:
            return 0

        remaining = int((cooldown_until - datetime.utcnow()).total_seconds())
        if remaining <= 0:
            self.provider_cooldowns.pop(provider, None)
            return 0
        return remaining

    def _provider_available(self, provider: ModelProvider, budget_limit: float) -> bool:
        """Return True when the provider is not cooling down and within budget."""
        return (
            provider in self.configs
            and self._get_cooldown_seconds(provider) == 0
            and self._within_budget(provider, budget_limit)
        )

    def mark_rate_limited(
        self,
        provider: ModelProvider,
        retry_after_seconds: int | None = None,
        reason: str | None = None,
    ) -> None:
        """Put a provider on temporary cooldown after a rate-limit response."""
        retry_after = max(retry_after_seconds or 60, 1)
        self.provider_cooldowns[provider] = datetime.utcnow().replace(
            microsecond=0
        ) + timedelta(seconds=retry_after)
        self.provider_last_errors[provider] = reason or "rate_limited"
        logger.warning(
            "Cooling down %s for %ss after rate limit: %s",
            provider.value,
            retry_after,
            self.provider_last_errors[provider],
        )

    def record_provider_failure(
        self,
        provider: ModelProvider,
        reason: str,
    ) -> None:
        """Store the most recent provider failure reason for operator visibility."""
        self.provider_last_errors[provider] = reason

    def _register_provider(self, config: ModelConfig) -> None:
        """Register a provider when its model is allowed in the active lane."""
        if not model_allowed(config.model_name, active_lane=self.model_usage_lane):
            logger.info(
                "Skipping %s provider model %s (%s lane) under %s runtime",
                config.provider.value,
                config.model_name,
                describe_model_lane(config.model_name),
                self.model_usage_lane.value,
            )
            return

        config.lane = describe_model_lane(config.model_name)
        self.configs[config.provider] = config

    def init_providers(self) -> None:
        """Initialize all available providers from environment"""
        import os

        # Ollama: Local, free, unlimited, private (highest priority)
        ollama_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
        if os.getenv("OLLAMA_ENABLED", "true").lower() == "true":
            self._register_provider(
                ModelConfig(
                    provider=ModelProvider.OLLAMA,
                    api_key="ollama",  # Ollama needs no real key
                    model_name=COST_ROUTER_DEFAULTS.ollama,
                    cost_per_1k_input=0.0,
                    cost_per_1k_output=0.0,
                    quota_limit=None,
                    max_tokens=8192,
                    priority=0,  # Highest priority (local, free)
                    is_free_tier=True,
                )
            )
            logger.info("✅ Ollama provider initialized (LOCAL, FREE, %s)", ollama_url)

        # Groq: Free tier, unlimited, fast
        if groq_key := os.getenv("GROQ_API_KEY"):
            self._register_provider(
                ModelConfig(
                    provider=ModelProvider.GROQ,
                    api_key=groq_key,
                    model_name=COST_ROUTER_DEFAULTS.groq,  # Free tier model
                    cost_per_1k_input=0.0,
                    cost_per_1k_output=0.0,
                    quota_limit=None,  # Unlimited
                    max_tokens=32768,
                    priority=1,  # Highest priority (cheapest)
                    is_free_tier=True,
                )
            )
            logger.info("✅ Groq provider initialized (FREE TIER)")

        # OpenRouter: Cost-efficient aggregation
        if openrouter_key := os.getenv("OPENROUTER_API_KEY"):
            self._register_provider(
                ModelConfig(
                    provider=ModelProvider.OPENROUTER,
                    api_key=openrouter_key,
                    model_name=COST_ROUTER_DEFAULTS.openrouter,  # Auto-routes to cheapest
                    cost_per_1k_input=0.00001,  # Approximately (varies by model)
                    cost_per_1k_output=0.00001,
                    quota_limit=None,
                    max_tokens=4096,
                    priority=2,
                    is_free_tier=False,
                )
            )
            logger.info("✅ OpenRouter provider initialized (cost-efficient)")

        # Gemini: Free tier with quotas
        if gemini_key := os.getenv("GEMINI_API_KEY"):
            gemini_model_name = get_model_name()
            self._register_provider(
                ModelConfig(
                    provider=ModelProvider.GEMINI,
                    api_key=gemini_key,
                    model_name=gemini_model_name,
                    cost_per_1k_input=0.0,
                    cost_per_1k_output=0.0,
                    quota_limit=1500,  # 1,500 requests/day
                    quota_period_seconds=86400,  # 24 hours
                    max_tokens=4096,
                    priority=3,
                    is_free_tier=True,
                )
            )
            logger.info("✅ Gemini provider initialized (FREE, quota-limited)")

        # Claude: Premium, for critical decisions
        if anthropic_key := os.getenv("ANTHROPIC_API_KEY"):
            self._register_provider(
                ModelConfig(
                    provider=ModelProvider.CLAUDE,
                    api_key=anthropic_key,
                    model_name=COST_ROUTER_DEFAULTS.anthropic,
                    cost_per_1k_input=0.003,  # Premium pricing
                    cost_per_1k_output=0.015,
                    quota_limit=None,
                    max_tokens=4096,
                    priority=4,
                    is_free_tier=False,
                )
            )
            logger.info("✅ Claude provider initialized (premium, use sparingly)")

        # OpenAI: Fast paid worker lane for lightweight tasks
        if openai_key := os.getenv("OPENAI_API_KEY"):
            self._register_provider(
                ModelConfig(
                    provider=ModelProvider.OPENAI,
                    api_key=openai_key,
                    model_name=COST_ROUTER_DEFAULTS.openai,
                    cost_per_1k_input=0.0002,
                    cost_per_1k_output=0.00125,
                    quota_limit=None,
                    max_tokens=4096,
                    priority=4,
                    is_free_tier=False,
                )
            )
            logger.info("✅ OpenAI provider initialized (fast paid worker lane)")

    def select_for_task(
        self, task_type: TaskType, budget_limit: float = 0.01
    ) -> list[ModelProvider]:
        """
        Select models for task type in priority order.

        Args:
            task_type: Type of work to perform
            budget_limit: Maximum cost acceptable (USD)

        Returns:
            List of providers in recommended order
        """
        # Map task types to preferred providers (cost-first: free → cheap → premium)
        task_preferences = {
            TaskType.CODE_GENERATION: [
                ModelProvider.OLLAMA,
                ModelProvider.GROQ,
                ModelProvider.GEMINI,
                ModelProvider.OPENROUTER,
                ModelProvider.OPENAI,
            ],
            TaskType.ANALYSIS: [
                ModelProvider.OLLAMA,
                ModelProvider.GROQ,
                ModelProvider.GEMINI,
                ModelProvider.OPENROUTER,
                ModelProvider.OPENAI,
            ],
            TaskType.DECISION: [
                ModelProvider.OLLAMA,
                ModelProvider.GROQ,
                ModelProvider.GEMINI,
                ModelProvider.OPENROUTER,
                ModelProvider.CLAUDE,
            ],
            TaskType.VERIFICATION: [
                ModelProvider.OLLAMA,
                ModelProvider.GROQ,
                ModelProvider.GEMINI,
                ModelProvider.CLAUDE,
            ],
            TaskType.PLANNING: [
                ModelProvider.OLLAMA,
                ModelProvider.GROQ,
                ModelProvider.GEMINI,
                ModelProvider.OPENROUTER,
            ],
            TaskType.SUMMARY: [
                ModelProvider.OLLAMA,
                ModelProvider.GROQ,
                ModelProvider.GEMINI,
                ModelProvider.OPENROUTER,
            ],
            TaskType.RETRIEVAL: [
                ModelProvider.OLLAMA,
                ModelProvider.GROQ,
                ModelProvider.GEMINI,
                ModelProvider.OPENROUTER,
            ],
            TaskType.CORRECTION: [
                ModelProvider.OLLAMA,
                ModelProvider.GROQ,
                ModelProvider.GEMINI,
                ModelProvider.CLAUDE,
            ],
        }

        preferred = task_preferences.get(task_type, [ModelProvider.GROQ])
        available = [p for p in preferred if self._provider_available(p, budget_limit)]

        if not available:
            # Fallback: use any configured provider that is not cooling down.
            available = [
                provider
                for provider in self.configs.keys()
                if self._get_cooldown_seconds(provider) == 0
            ]

        logger.info(f"Route {task_type.value}: {[p.value for p in available[:3]]}")
        return available

    def _within_budget(self, provider: ModelProvider, limit: float) -> bool:
        """Check if provider is within budget constraints"""
        config = self.configs[provider]

        # Free tier providers always allowed
        if config.is_free_tier:
            return True

        # Check daily cost limits
        if provider in self.cost_tracking:
            cost_data = self.cost_tracking[provider]
            if cost_data.daily_spend >= limit:
                logger.warning(
                    f"Provider {provider.value} daily budget exceeded: "
                    f"${cost_data.daily_spend:.4f} >= ${limit:.4f}"
                )
                return False

        return True

    def estimate_cost(
        self,
        provider: ModelProvider,
        task_type: TaskType,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Estimate cost for a operation"""
        config = self.configs.get(provider)
        if not config:
            return 0.0

        input_cost = input_tokens / 1000 * config.cost_per_1k_input
        output_cost = output_tokens / 1000 * config.cost_per_1k_output
        total_cost = input_cost + output_cost

        logger.debug(
            f"Cost estimate for {provider.value}/{task_type.value}: "
            f"${total_cost:.4f} ({input_tokens}→{output_tokens} tokens)"
        )

        return total_cost

    def record_usage(
        self,
        provider: ModelProvider,
        task_type: TaskType,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """Record API usage for cost tracking"""
        config = self.configs.get(provider)
        if not config:
            return

        cost = self.estimate_cost(provider, task_type, input_tokens, output_tokens)

        if provider not in self.cost_tracking:
            self.cost_tracking[provider] = CostEstimate(
                provider=provider, task_type=task_type
            )

        self.cost_tracking[provider].record_usage(
            cost=cost,
            task_type=task_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        self.provider_cooldowns.pop(provider, None)
        self.provider_last_errors.pop(provider, None)

        self.request_counts[provider] = self.request_counts.get(provider, 0) + 1

        logger.info(
            f"Recorded usage: {provider.value}, "
            f"Cost: ${cost:.4f}, "
            f"Daily total: ${self.cost_tracking[provider].daily_spend:.2f}"
        )

    def get_cost_report(self) -> dict[str, object]:
        """Get comprehensive cost analysis"""
        total_daily = sum(c.daily_spend for c in self.cost_tracking.values())
        total_monthly = sum(c.monthly_spend for c in self.cost_tracking.values())
        total_requests = sum(c.total_requests for c in self.cost_tracking.values())
        total_input_tokens = sum(
            c.total_input_tokens for c in self.cost_tracking.values()
        )
        total_output_tokens = sum(
            c.total_output_tokens for c in self.cost_tracking.values()
        )

        provider_breakdown = {
            provider.value: {
                "model": self.configs[provider].model_name,
                "lane": self.configs[provider].lane,
                "is_free_tier": self.configs[provider].is_free_tier,
                "input_cost_per_1k": self.configs[provider].cost_per_1k_input,
                "output_cost_per_1k": self.configs[provider].cost_per_1k_output,
                "daily": self.cost_tracking.get(
                    provider,
                    CostEstimate(provider=provider, task_type=TaskType.ANALYSIS),
                ).daily_spend,
                "daily_spend_usd": round(
                    self.cost_tracking.get(
                        provider,
                        CostEstimate(provider=provider, task_type=TaskType.ANALYSIS),
                    ).daily_spend,
                    6,
                ),
                "monthly": self.cost_tracking.get(
                    provider,
                    CostEstimate(provider=provider, task_type=TaskType.ANALYSIS),
                ).monthly_spend,
                "monthly_spend_usd": round(
                    self.cost_tracking.get(
                        provider,
                        CostEstimate(provider=provider, task_type=TaskType.ANALYSIS),
                    ).monthly_spend,
                    6,
                ),
                "requests": self.request_counts.get(provider, 0),
                "input_tokens": self.cost_tracking.get(
                    provider,
                    CostEstimate(provider=provider, task_type=TaskType.ANALYSIS),
                ).total_input_tokens,
                "output_tokens": self.cost_tracking.get(
                    provider,
                    CostEstimate(provider=provider, task_type=TaskType.ANALYSIS),
                ).total_output_tokens,
                "total_tokens": (
                    self.cost_tracking.get(
                        provider,
                        CostEstimate(provider=provider, task_type=TaskType.ANALYSIS),
                    ).total_input_tokens
                    + self.cost_tracking.get(
                        provider,
                        CostEstimate(provider=provider, task_type=TaskType.ANALYSIS),
                    ).total_output_tokens
                ),
                "last_task_type": self.cost_tracking.get(
                    provider,
                    CostEstimate(provider=provider, task_type=TaskType.ANALYSIS),
                ).last_task_type,
                "last_used_at": self.cost_tracking.get(
                    provider,
                    CostEstimate(provider=provider, task_type=TaskType.ANALYSIS),
                ).last_used_at,
                "cooldown_seconds": self._get_cooldown_seconds(provider),
                "cooling_down": self._get_cooldown_seconds(provider) > 0,
                "last_error": self.provider_last_errors.get(provider),
            }
            for provider in self.configs.keys()
        }

        return {
            "report_generated_at": datetime.utcnow().isoformat(),
            "total_daily_spend": f"${total_daily:.2f}",
            "total_monthly_spend": f"${total_monthly:.2f}",
            "totals": {
                "daily_spend_usd": round(total_daily, 6),
                "monthly_spend_usd": round(total_monthly, 6),
                "requests": total_requests,
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "total_tokens": total_input_tokens + total_output_tokens,
            },
            "providers": provider_breakdown,
            "model_usage_lane": self.model_usage_lane.value,
            "free_tier_usage": {
                p.value: self.request_counts.get(p, 0)
                for p in [ModelProvider.GROQ, ModelProvider.GEMINI]
                if p in self.configs
            },
        }

    def get_routing_strategy(self) -> dict[str, object]:
        """Get current routing strategy"""
        return {
            "model_usage_lane": self.model_usage_lane.value,
            "priorities": [
                (p.value, c.priority)
                for p, c in sorted(
                    self.configs.items(),
                    key=lambda x: x[1].priority,
                )
            ],
            "model_lanes": {p.value: c.lane for p, c in self.configs.items()},
            "free_providers": [
                p.value for p, c in self.configs.items() if c.is_free_tier
            ],
            "quota_limited": {
                p.value: {
                    "limit": c.quota_limit,
                    "period_hours": c.quota_period_seconds / 3600,
                    "cooldown_seconds": self._get_cooldown_seconds(p),
                }
                for p, c in self.configs.items()
                if c.quota_limit
            },
            "cost_per_request": {
                p.value: c.cost_per_1k_input + c.cost_per_1k_output
                for p, c in self.configs.items()
            },
        }


_cost_optimized_model_router: CostOptimizedModelRouter | None = None


def get_cost_optimized_model_router() -> CostOptimizedModelRouter:
    """Return the process-wide cost router so usage and cooldown state persist."""
    global _cost_optimized_model_router
    if _cost_optimized_model_router is None:
        _cost_optimized_model_router = CostOptimizedModelRouter()
    return _cost_optimized_model_router


def reset_cost_optimized_model_router() -> None:
    """Reset the process-wide cost router. Intended for tests only."""
    global _cost_optimized_model_router
    _cost_optimized_model_router = None
