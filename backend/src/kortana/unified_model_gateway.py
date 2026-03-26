"""
KOR'TANA Unified Model Gateway

Simplified integration layer for the cost-optimized multi-provider routing.
Works with existing API clients and adds intelligent provider selection.
"""

from __future__ import annotations

from typing import Optional

from src.kortana.cost_optimized_model_router import (
    CostOptimizedModelRouter,
    ModelProvider,
    TaskType,
)
from src.kortana.logger import get_logger

logger = get_logger(__name__)


class UnifiedModelGateway:
    """
    Central gateway for multi-provider model access.

    Routes requests to optimal provider based on:
    - Task type (code gen, analysis, decisions, etc.)
    - Cost constraints (budget per request)
    - Provider availability and quotas
    - Performance requirements
    """

    def __init__(self):
        """Initialize gateway with cost-optimized router"""
        self.router = CostOptimizedModelRouter()
        logger.info("✅ Unified Model Gateway initialized")
        self._log_available_providers()

    def _log_available_providers(self) -> None:
        """Log available providers and strategy"""
        strategy = self.router.get_routing_strategy()
        free_providers = strategy["free_providers"]
        logger.info(f"Free tier providers: {free_providers}")

        priorities = strategy["priorities"]
        logger.info("Provider priority order:")
        for provider_name, priority in priorities:
            logger.info(f"  {priority + 1}. {provider_name}")

    def get_optimal_provider(
        self,
        task_type: TaskType,
        budget_limit: float = 0.01,
    ) -> Optional[ModelProvider]:
        """
        Get single optimal provider for a task.

        Args:
            task_type: Type of work (code_generation, analysis, etc.)
            budget_limit: Maximum cost allowed (USD)

        Returns:
            Best provider for this task, or None if all unavailable
        """
        providers = self.router.select_for_task(task_type, budget_limit)
        return providers[0] if providers else None

    def get_provider_chain(
        self,
        task_type: TaskType,
        budget_limit: float = 0.01,
    ) -> list[ModelProvider]:
        """
        Get fallback chain of providers for a task.

        Use these in order: first succeeds, second is fallback, etc.
        """
        return self.router.select_for_task(task_type, budget_limit)

    def is_free_provider(self, provider: ModelProvider) -> bool:
        """Check if provider is free tier"""
        config = self.router.configs.get(provider)
        return config.is_free_tier if config else False

    def get_cost_estimate(
        self,
        provider: ModelProvider,
        task_type: TaskType,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Estimate cost for a request before making it"""
        return self.router.estimate_cost(
            provider, task_type, input_tokens, output_tokens
        )

    def record_api_call(
        self,
        provider: ModelProvider,
        task_type: TaskType,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """Record API usage for cost tracking"""
        self.router.record_usage(provider, task_type, input_tokens, output_tokens)

    def get_cost_report(self) -> dict:
        """Get comprehensive cost analysis"""
        return self.router.get_cost_report()

    def get_routing_strategy(self) -> dict:
        """Get full routing strategy details"""
        return self.router.get_routing_strategy()

    def can_handle_task(
        self,
        task_type: TaskType,
        budget_limit: float = 0.01,
    ) -> bool:
        """Check if any provider can handle this task within budget"""
        providers = self.router.select_for_task(task_type, budget_limit)
        return len(providers) > 0

    def get_provider_info(self, provider: ModelProvider) -> dict:
        """Get detailed info about a specific provider"""
        config = self.router.configs.get(provider)
        if not config:
            return {}

        return {
            "provider": provider.value,
            "model": config.model_name,
            "is_free": config.is_free_tier,
            "cost_per_1k_input": f"${config.cost_per_1k_input:.6f}",
            "cost_per_1k_output": f"${config.cost_per_1k_output:.6f}",
            "max_tokens": config.max_tokens,
            "quota_limit": config.quota_limit,
            "quota_period_hours": config.quota_period_seconds / 3600,
            "priority": config.priority,
        }

    def get_all_providers_info(self) -> dict:
        """Get info about all available providers"""
        return {
            provider.value: self.get_provider_info(provider)
            for provider in self.router.configs.keys()
        }
