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
5. OpenAI as last resort (most expensive)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from src.kortana.logger import get_logger

logger = get_logger(__name__)


class ModelProvider(Enum):
    """Available model providers"""

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
    last_reset: datetime = field(default_factory=datetime.utcnow)

    def calculate_cost(self, config: ModelConfig) -> float:
        """Calculate total cost for this request"""
        input_cost = (
            self.estimated_input_tokens / 1000 * config.cost_per_1k_input
        )
        output_cost = (
            self.estimated_output_tokens / 1000 * config.cost_per_1k_output
        )
        return input_cost + output_cost

    def update_daily_spend(self, cost: float) -> None:
        """Update daily spending and reset if needed"""
        now = datetime.utcnow()
        if (now - self.last_reset).days >= 1:
            self.daily_spend = 0.0
            self.last_reset = now
        self.daily_spend += cost
        self.monthly_spend += cost


class CostOptimizedModelRouter:
    """
    Intelligently routes requests to minimize costs while maximizing autonomy.
    
    Priority Order by Task Type:
    - FREE TIER FIRST: Groq (unlimited, fast)
    - FALLBACK 1: OpenRouter (cost-efficient)
    - FALLBACK 2: Gemini (free tier, quota-limited)
    - FALLBACK 3: Claude (critical decisions only)
    - FALLBACK 4: OpenAI (expensive, use sparingly)
    """

    def __init__(self):
        self.configs: dict[ModelProvider, ModelConfig] = {}
        self.cost_tracking: dict[ModelProvider, CostEstimate] = {}
        self.request_counts: dict[ModelProvider, int] = {}
        self.init_providers()

    def init_providers(self) -> None:
        """Initialize all available providers from environment"""
        import os

        # Groq: Free tier, unlimited, fast
        if groq_key := os.getenv("GROQ_API_KEY"):
            self.configs[ModelProvider.GROQ] = ModelConfig(
                provider=ModelProvider.GROQ,
                api_key=groq_key,
                model_name="mixtral-8x7b-32768",  # Free tier model
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
                quota_limit=None,  # Unlimited
                max_tokens=32768,
                priority=1,  # Highest priority (cheapest)
                is_free_tier=True,
            )
            logger.info("✅ Groq provider initialized (FREE TIER)")

        # OpenRouter: Cost-efficient aggregation
        if openrouter_key := os.getenv("OPENROUTER_API_KEY"):
            self.configs[ModelProvider.OPENROUTER] = ModelConfig(
                provider=ModelProvider.OPENROUTER,
                api_key=openrouter_key,
                model_name="openrouter/auto",  # Auto-routes to cheapest
                cost_per_1k_input=0.00001,  # Approximately (varies by model)
                cost_per_1k_output=0.00001,
                quota_limit=None,
                max_tokens=4096,
                priority=2,
                is_free_tier=False,
            )
            logger.info("✅ OpenRouter provider initialized (cost-efficient)")

        # Gemini: Free tier with quotas
        if gemini_key := os.getenv("GEMINI_API_KEY"):
            self.configs[ModelProvider.GEMINI] = ModelConfig(
                provider=ModelProvider.GEMINI,
                api_key=gemini_key,
                model_name="gemini-3.1-flash-lite-preview",
                cost_per_1k_input=0.0,
                cost_per_1k_output=0.0,
                quota_limit=1500,  # 1,500 requests/day
                quota_period_seconds=86400,  # 24 hours
                max_tokens=4096,
                priority=3,
                is_free_tier=True,
            )
            logger.info("✅ Gemini provider initialized (FREE, quota-limited)")

        # Claude: Premium, for critical decisions
        if anthropic_key := os.getenv("ANTHROPIC_API_KEY"):
            self.configs[ModelProvider.CLAUDE] = ModelConfig(
                provider=ModelProvider.CLAUDE,
                api_key=anthropic_key,
                model_name="claude-3-5-sonnet-20241022",
                cost_per_1k_input=0.003,  # Premium pricing
                cost_per_1k_output=0.015,
                quota_limit=None,
                max_tokens=4096,
                priority=4,
                is_free_tier=False,
            )
            logger.info("✅ Claude provider initialized (premium, use sparingly)")

        # OpenAI: Expensive, fallback only
        if openai_key := os.getenv("OPENAI_API_KEY"):
            self.configs[ModelProvider.OPENAI] = ModelConfig(
                provider=ModelProvider.OPENAI,
                api_key=openai_key,
                model_name="gpt-4o-mini",  # Fast, cheaper than full GPT-4
                cost_per_1k_input=0.00015,
                cost_per_1k_output=0.0006,
                quota_limit=None,
                max_tokens=4096,
                priority=5,  # Lowest priority (most expensive)
                is_free_tier=False,
            )
            logger.info("✅ OpenAI provider initialized (expensive, last resort)")

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
        # Map task types to preferred providers
        task_preferences = {
            TaskType.CODE_GENERATION: [
                ModelProvider.GROQ,
                ModelProvider.OPENROUTER,
                ModelProvider.OPENAI,
            ],
            TaskType.ANALYSIS: [
                ModelProvider.GROQ,
                ModelProvider.GEMINI,
                ModelProvider.OPENROUTER,
            ],
            TaskType.DECISION: [
                ModelProvider.CLAUDE,
                ModelProvider.GROQ,
                ModelProvider.OPENROUTER,
            ],
            TaskType.VERIFICATION: [
                ModelProvider.CLAUDE,
                ModelProvider.GROQ,
            ],
            TaskType.PLANNING: [
                ModelProvider.GROQ,
                ModelProvider.OPENROUTER,
                ModelProvider.GEMINI,
            ],
            TaskType.SUMMARY: [
                ModelProvider.GROQ,
                ModelProvider.GEMINI,
            ],
            TaskType.RETRIEVAL: [
                ModelProvider.GROQ,
                ModelProvider.GEMINI,
            ],
            TaskType.CORRECTION: [
                ModelProvider.CLAUDE,
                ModelProvider.GROQ,
            ],
        }

        preferred = task_preferences.get(task_type, [ModelProvider.GROQ])
        available = [
            p for p in preferred
            if p in self.configs and self._within_budget(p, budget_limit)
        ]

        if not available:
            # Fallback: use any available provider
            available = list(self.configs.keys())

        logger.info(
            f"Route {task_type.value}: {[p.value for p in available[:3]]}"
        )
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

        cost = self.estimate_cost(
            provider, task_type, input_tokens, output_tokens
        )

        if provider not in self.cost_tracking:
            self.cost_tracking[provider] = CostEstimate(
                provider=provider, task_type=task_type
            )

        self.cost_tracking[provider].update_daily_spend(cost)

        self.request_counts[provider] = (
            self.request_counts.get(provider, 0) + 1
        )

        logger.info(
            f"Recorded usage: {provider.value}, "
            f"Cost: ${cost:.4f}, "
            f"Daily total: ${self.cost_tracking[provider].daily_spend:.2f}"
        )

    def get_cost_report(self) -> dict:
        """Get comprehensive cost analysis"""
        total_daily = sum(
            c.daily_spend for c in self.cost_tracking.values()
        )
        total_monthly = sum(
            c.monthly_spend for c in self.cost_tracking.values()
        )

        provider_breakdown = {
            provider: {
                "daily": self.cost_tracking.get(provider, CostEstimate(
                    provider=provider, task_type=TaskType.ANALYSIS
                )).daily_spend,
                "monthly": self.cost_tracking.get(provider, CostEstimate(
                    provider=provider, task_type=TaskType.ANALYSIS
                )).monthly_spend,
                "requests": self.request_counts.get(provider, 0),
            }
            for provider in self.configs.keys()
        }

        return {
            "total_daily_spend": f"${total_daily:.2f}",
            "total_monthly_spend": f"${total_monthly:.2f}",
            "providers": provider_breakdown,
            "free_tier_usage": {
                p.value: self.request_counts.get(p, 0)
                for p in [ModelProvider.GROQ, ModelProvider.GEMINI]
                if p in self.configs
            },
        }

    def get_routing_strategy(self) -> dict:
        """Get current routing strategy"""
        return {
            "priorities": [
                (p.value, c.priority)
                for p, c in sorted(
                    self.configs.items(),
                    key=lambda x: x[1].priority,
                )
            ],
            "free_providers": [
                p.value for p, c in self.configs.items() if c.is_free_tier
            ],
            "quota_limited": {
                p.value: {
                    "limit": c.quota_limit,
                    "period_hours": c.quota_period_seconds / 3600,
                }
                for p, c in self.configs.items()
                if c.quota_limit
            },
            "cost_per_request": {
                p.value: c.cost_per_1k_input + c.cost_per_1k_output
                for p, c in self.configs.items()
            },
        }
