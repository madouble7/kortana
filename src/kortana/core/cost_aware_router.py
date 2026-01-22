"""
Cost-Aware Model Router for Kor'tana

This module provides intelligent model routing with cost optimization,
automatic fallbacks, and usage tracking to maximize operational efficiency
while maintaining quality.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from kortana.config.schema import KortanaConfig

from .enhanced_model_router import EnhancedModelRouter, TaskType

logger = logging.getLogger(__name__)


@dataclass
class UsageStats:
    """Track model usage statistics."""

    model_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    average_latency: float = 0.0
    last_used: datetime = field(default_factory=datetime.now)


@dataclass
class RequestMetrics:
    """Metrics for a single request."""

    model_id: str
    task_type: str
    input_tokens: int
    output_tokens: int
    cost: float
    latency: float
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)


class CostAwareRouter(EnhancedModelRouter):
    """
    Enhanced router with cost optimization and usage tracking.

    Features:
    - Automatic fallback to free models when possible
    - Usage tracking and cost monitoring
    - Smart caching for repeated queries
    - Dynamic model selection based on usage patterns
    - Cost budgets and alerts
    """

    def __init__(self, settings: KortanaConfig, cost_budget_daily: float = 1.0):
        """
        Initialize the cost-aware router.

        Args:
            settings: The application configuration.
            cost_budget_daily: Daily cost budget in USD (default: $1.00).
        """
        super().__init__(settings)

        self.cost_budget_daily = cost_budget_daily
        self.usage_stats: dict[str, UsageStats] = {}
        self.request_history: list[RequestMetrics] = []
        self.cache: dict[str, tuple[str, float]] = {}  # query -> (response, timestamp)
        self.cache_ttl = 3600  # 1 hour cache TTL
        self.fallback_chains = self._build_fallback_chains()

        # Load usage stats from disk if available
        self._load_usage_stats()

        logger.info(
            f"CostAwareRouter initialized with daily budget: ${cost_budget_daily:.2f}"
        )

    def _build_fallback_chains(self) -> dict[str, list[str]]:
        """Build fallback chains for each task type prioritizing free models."""
        routing = self.models_config.get("routing", {})

        return {
            "general_chat": [
                routing.get("general_chat", "deepseek/deepseek-r1-0528-qwen3-8b:free"),
                routing.get(
                    "general_chat_fallback", "meta-llama/llama-3.1-8b-instruct:free"
                ),
                routing.get("premium_general", "openai/gpt-4.1-nano"),
            ],
            "reasoning": [
                routing.get("reasoning_tasks", "deepseek/deepseek-r1-0528:free"),
                routing.get("reasoning_fallback", "qwen/qwen-2-7b-instruct:free"),
                routing.get("premium_analysis", "meta-llama/llama-4-maverick"),
            ],
            "coding": [
                routing.get("coding", "mistralai/mistral-7b-instruct:free"),
                routing.get(
                    "coding_fallback", "meta-llama/llama-3.1-8b-instruct:free"
                ),
                routing.get("premium_general", "openai/gpt-4.1-nano"),
            ],
            "analysis": [
                routing.get("analysis", "deepseek/deepseek-r1-0528:free"),
                routing.get("analysis_fallback", "qwen/qwen-2-7b-instruct:free"),
                routing.get("premium_analysis", "meta-llama/llama-4-maverick"),
            ],
            "creative_writing": [
                routing.get("creative_writing", "google/gemma-2-9b-it:free"),
                routing.get("general_chat", "deepseek/deepseek-r1-0528-qwen3-8b:free"),
                routing.get("creative_writing_premium", "x-ai/grok-3-mini-beta"),
            ],
            "vision": [
                routing.get("vision_tasks", "google/gemini-2.5-flash-preview-05-20"),
                routing.get("vision_fallback", "google/gemini-2.0-flash-001"),
            ],
        }

    def _get_daily_cost(self) -> float:
        """Calculate total cost for today."""
        today = datetime.now().date()
        daily_cost = sum(
            metric.cost
            for metric in self.request_history
            if metric.timestamp.date() == today
        )
        return daily_cost

    def _is_within_budget(self, estimated_cost: float) -> bool:
        """Check if a request would exceed daily budget."""
        current_cost = self._get_daily_cost()
        return (current_cost + estimated_cost) <= self.cost_budget_daily

    def _get_cache_key(self, user_input: str, context: dict[str, Any]) -> str:
        """Generate a cache key for the request."""
        # Simple hash-based cache key
        context_str = json.dumps(context, sort_keys=True)
        return f"{hash(user_input)}_{hash(context_str)}"

    def _check_cache(self, cache_key: str) -> str | None:
        """Check if a cached response exists and is still valid."""
        if cache_key in self.cache:
            response, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                logger.info("Cache hit - returning cached response")
                return response
            else:
                # Cache expired, remove it
                del self.cache[cache_key]
        return None

    def _update_cache(self, cache_key: str, response: str) -> None:
        """Update the cache with a new response."""
        self.cache[cache_key] = (response, time.time())

        # Limit cache size
        if len(self.cache) > 1000:
            # Remove oldest entries
            sorted_items = sorted(
                self.cache.items(), key=lambda x: x[1][1]
            )  # Sort by timestamp
            self.cache = dict(sorted_items[-500:])  # Keep newest 500

    def _update_usage_stats(self, metrics: RequestMetrics) -> None:
        """Update usage statistics with request metrics."""
        model_id = metrics.model_id

        if model_id not in self.usage_stats:
            self.usage_stats[model_id] = UsageStats(model_id=model_id)

        stats = self.usage_stats[model_id]
        stats.total_requests += 1

        if metrics.success:
            stats.successful_requests += 1
            stats.total_input_tokens += metrics.input_tokens
            stats.total_output_tokens += metrics.output_tokens
            stats.total_cost += metrics.cost

            # Update average latency
            total_successful = stats.successful_requests
            stats.average_latency = (
                stats.average_latency * (total_successful - 1) + metrics.latency
            ) / total_successful
        else:
            stats.failed_requests += 1

        stats.last_used = metrics.timestamp

        # Add to request history
        self.request_history.append(metrics)

        # Limit history size
        if len(self.request_history) > 10000:
            self.request_history = self.request_history[-5000:]

        # Persist stats periodically
        if stats.total_requests % 10 == 0:
            self._save_usage_stats()

    def _save_usage_stats(self) -> None:
        """Save usage statistics to disk."""
        try:
            stats_file = Path("data/usage_stats.json")
            stats_file.parent.mkdir(parents=True, exist_ok=True)

            stats_dict = {
                model_id: {
                    "model_id": stats.model_id,
                    "total_requests": stats.total_requests,
                    "successful_requests": stats.successful_requests,
                    "failed_requests": stats.failed_requests,
                    "total_input_tokens": stats.total_input_tokens,
                    "total_output_tokens": stats.total_output_tokens,
                    "total_cost": stats.total_cost,
                    "average_latency": stats.average_latency,
                    "last_used": stats.last_used.isoformat(),
                }
                for model_id, stats in self.usage_stats.items()
            }

            with open(stats_file, "w") as f:
                json.dump(stats_dict, f, indent=2)

            logger.debug(f"Saved usage stats to {stats_file}")
        except Exception as e:
            logger.error(f"Failed to save usage stats: {e}")

    def _load_usage_stats(self) -> None:
        """Load usage statistics from disk."""
        try:
            stats_file = Path("data/usage_stats.json")
            if stats_file.exists():
                with open(stats_file) as f:
                    stats_dict = json.load(f)

                for model_id, stats_data in stats_dict.items():
                    self.usage_stats[model_id] = UsageStats(
                        model_id=stats_data["model_id"],
                        total_requests=stats_data["total_requests"],
                        successful_requests=stats_data["successful_requests"],
                        failed_requests=stats_data["failed_requests"],
                        total_input_tokens=stats_data["total_input_tokens"],
                        total_output_tokens=stats_data["total_output_tokens"],
                        total_cost=stats_data["total_cost"],
                        average_latency=stats_data["average_latency"],
                        last_used=datetime.fromisoformat(stats_data["last_used"]),
                    )

                logger.info(
                    f"Loaded usage stats for {len(self.usage_stats)} models"
                )
        except Exception as e:
            logger.warning(f"Could not load usage stats: {e}")

    def route_with_fallback(
        self,
        user_input: str,
        conversation_context: dict[str, Any],
        prefer_free: bool = True,
        use_cache: bool = True,
    ) -> tuple[str, str, dict[str, Any], dict[str, Any]]:
        """
        Route with intelligent fallback and cost optimization.

        Args:
            user_input: The user's input text.
            conversation_context: Context about the current conversation.
            prefer_free: Whether to prefer free models when possible.
            use_cache: Whether to use caching for responses.

        Returns:
            A tuple containing (model_id, voice_style, model_params, routing_info).
        """
        # Check cache if enabled
        if use_cache:
            cache_key = self._get_cache_key(user_input, conversation_context)
            cached_response = self._check_cache(cache_key)
            if cached_response:
                return (
                    "cached",
                    "presence",
                    {},
                    {"cached": True, "response": cached_response},
                )

        # Analyze task type
        task_type = self.analyze_task_type(user_input, conversation_context)

        # Get fallback chain for task type
        task_key = self._task_type_to_key(task_type)
        fallback_chain = self.fallback_chains.get(task_key, ["deepseek/deepseek-r1-0528-qwen3-8b:free"])

        # Estimate context length
        context_length = len(user_input) + conversation_context.get("context_length", 0)

        # Try each model in the fallback chain
        for model_id in fallback_chain:
            # Check if model exists in metadata
            if model_id not in self.model_metadata:
                logger.warning(f"Model {model_id} not found in metadata, skipping")
                continue

            metadata = self.model_metadata[model_id]

            # Check context window
            if metadata.capabilities.context_window < context_length:
                logger.info(
                    f"Model {model_id} context window too small, trying next in chain"
                )
                continue

            # Estimate cost for this request
            estimated_tokens = len(user_input.split()) * 1.5  # Rough estimate
            estimated_cost = self.estimate_cost(model_id, int(estimated_tokens), int(estimated_tokens * 2))

            # Check budget if this is a paid model
            if metadata.capabilities.cost_per_1m_input > 0:
                if not self._is_within_budget(estimated_cost):
                    logger.warning(
                        f"Model {model_id} would exceed daily budget, trying next in chain"
                    )
                    continue

            # Model is suitable - determine voice style and params
            voice_style = self.determine_voice_style(task_type, user_input)
            model_params = self.voice_styles.get(
                voice_style, self.voice_styles["presence"]
            ).copy()

            # Add model-specific parameters
            model_config = self.models_config["models"].get(model_id, {})
            default_params = model_config.get("default_params", {})
            model_params.update(default_params)

            # Task-specific adjustments
            if task_type == TaskType.REASONING:
                model_params["temperature"] = min(
                    model_params.get("temperature", 0.7), 0.5
                )
            elif task_type == TaskType.CREATIVE_WRITING:
                model_params["temperature"] = max(
                    model_params.get("temperature", 0.7), 0.8
                )

            routing_info = {
                "task_type": task_type.value,
                "estimated_cost": estimated_cost,
                "fallback_position": fallback_chain.index(model_id),
                "total_fallbacks": len(fallback_chain),
                "is_free": metadata.capabilities.cost_per_1m_input == 0.0,
                "cached": False,
            }

            logger.info(
                f"Selected model: {model_id} (task: {task_type.value}, "
                f"fallback: {routing_info['fallback_position']}/{routing_info['total_fallbacks']}, "
                f"cost: ${estimated_cost:.6f})"
            )

            return model_id, voice_style, model_params, routing_info

        # Ultimate fallback
        fallback_model = "deepseek/deepseek-r1-0528-qwen3-8b:free"
        voice_style = "presence"
        model_params = self.voice_styles["presence"].copy()

        routing_info = {
            "task_type": task_type.value,
            "estimated_cost": 0.0,
            "fallback_position": -1,
            "total_fallbacks": len(fallback_chain),
            "is_free": True,
            "ultimate_fallback": True,
            "cached": False,
        }

        logger.warning(f"Using ultimate fallback: {fallback_model}")

        return fallback_model, voice_style, model_params, routing_info

    def _task_type_to_key(self, task_type: TaskType) -> str:
        """Convert TaskType enum to fallback chain key."""
        mapping = {
            TaskType.GENERAL_CHAT: "general_chat",
            TaskType.REASONING: "reasoning",
            TaskType.CODING: "coding",
            TaskType.ANALYSIS: "analysis",
            TaskType.CREATIVE_WRITING: "creative_writing",
            TaskType.VISION: "vision",
            TaskType.EMOTIONAL_SUPPORT: "general_chat",
            TaskType.FUNCTION_CALL: "coding",
            TaskType.LONGFORM: "general_chat",
        }
        return mapping.get(task_type, "general_chat")

    def record_request(
        self,
        model_id: str,
        task_type: str,
        input_tokens: int,
        output_tokens: int,
        latency: float,
        success: bool,
    ) -> None:
        """
        Record a completed request for tracking and optimization.

        Args:
            model_id: The model that was used.
            task_type: The type of task performed.
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.
            latency: Request latency in seconds.
            success: Whether the request succeeded.
        """
        cost = self.estimate_cost(model_id, input_tokens, output_tokens)

        metrics = RequestMetrics(
            model_id=model_id,
            task_type=task_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            latency=latency,
            success=success,
        )

        self._update_usage_stats(metrics)

    def get_usage_report(self, days: int = 7) -> dict[str, Any]:
        """
        Generate a usage report for the specified time period.

        Args:
            days: Number of days to include in the report.

        Returns:
            Dictionary containing usage statistics and insights.
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        # Filter recent requests
        recent_requests = [
            m for m in self.request_history if m.timestamp >= cutoff_date
        ]

        total_requests = len(recent_requests)
        total_cost = sum(m.cost for m in recent_requests)
        successful_requests = sum(1 for m in recent_requests if m.success)

        # Cost breakdown by model
        model_costs = {}
        for metrics in recent_requests:
            model_id = metrics.model_id
            if model_id not in model_costs:
                model_costs[model_id] = {
                    "requests": 0,
                    "cost": 0.0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                }
            model_costs[model_id]["requests"] += 1
            model_costs[model_id]["cost"] += metrics.cost
            model_costs[model_id]["input_tokens"] += metrics.input_tokens
            model_costs[model_id]["output_tokens"] += metrics.output_tokens

        # Task type breakdown
        task_breakdown = {}
        for metrics in recent_requests:
            task = metrics.task_type
            if task not in task_breakdown:
                task_breakdown[task] = {"requests": 0, "cost": 0.0}
            task_breakdown[task]["requests"] += 1
            task_breakdown[task]["cost"] += metrics.cost

        # Daily cost trend
        daily_costs = {}
        for metrics in recent_requests:
            date_str = metrics.timestamp.strftime("%Y-%m-%d")
            daily_costs[date_str] = daily_costs.get(date_str, 0.0) + metrics.cost

        return {
            "period_days": days,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": (
                successful_requests / total_requests if total_requests > 0 else 0
            ),
            "total_cost": total_cost,
            "average_cost_per_request": (
                total_cost / total_requests if total_requests > 0 else 0
            ),
            "daily_budget": self.cost_budget_daily,
            "budget_utilization": (
                total_cost / (self.cost_budget_daily * days)
                if self.cost_budget_daily > 0
                else 0
            ),
            "model_breakdown": model_costs,
            "task_breakdown": task_breakdown,
            "daily_costs": daily_costs,
        }

    def get_cost_optimization_suggestions(self) -> list[str]:
        """Generate suggestions for cost optimization based on usage patterns."""
        suggestions = []

        report = self.get_usage_report(days=7)

        # Check budget utilization
        if report["budget_utilization"] > 0.8:
            suggestions.append(
                "⚠️ Budget utilization is high (>80%). Consider increasing use of free models."
            )

        # Check model cost efficiency
        model_breakdown = report["model_breakdown"]
        for model_id, stats in model_breakdown.items():
            if model_id in self.model_metadata:
                metadata = self.model_metadata[model_id]
                if (
                    metadata.capabilities.cost_per_1m_input > 0
                    and stats["requests"] > 10
                ):
                    avg_cost = stats["cost"] / stats["requests"]
                    if avg_cost > 0.01:  # More than 1 cent per request
                        suggestions.append(
                            f"💡 Model '{model_id}' is averaging ${avg_cost:.4f} per request. "
                            f"Consider using free alternatives for simpler tasks."
                        )

        # Check for failed free models
        for model_id, stats_obj in self.usage_stats.items():
            if model_id in self.model_metadata:
                metadata = self.model_metadata[model_id]
                if metadata.capabilities.cost_per_1m_input == 0.0:
                    failure_rate = (
                        stats_obj.failed_requests / stats_obj.total_requests
                        if stats_obj.total_requests > 0
                        else 0
                    )
                    if failure_rate > 0.2:  # More than 20% failure rate
                        suggestions.append(
                            f"⚠️ Free model '{model_id}' has high failure rate ({failure_rate:.1%}). "
                            f"Consider using a different free model or premium fallback."
                        )

        if not suggestions:
            suggestions.append("✅ Usage patterns look optimal. Keep up the good work!")

        return suggestions
