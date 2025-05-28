"""
Kor'tana Model Optimizer
Intelligent model selection based on llm-stats.com data and usage patterns
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class ModelPerformance:
    """Model performance metrics from llm-stats.com"""
    gpqa_score: float
    cost_per_1m_input: float
    cost_per_1m_output: float
    context_window: int
    reasoning_capability: str
    specialized_features: List[str]

@dataclass
class ConversationContext:
    """Context for optimal model selection"""
    conversation_type: str  # "casual", "intimate", "autonomous", "memory"
    estimated_tokens: int
    priority_level: int  # 1-5, 5 being highest
    requires_reasoning: bool
    requires_empathy: bool
    budget_constraints: bool

class ModelOptimizer:
    """
    Intelligent model selector optimized with llm-stats.com data
    Balances performance, cost, and specialized capabilities
    """
    
    def __init__(self, config_path: str = "config/models_config.json"):
        self.config = self._load_config(config_path)
        self.usage_stats = {}
        self.cost_tracker = {"daily_spend": 0.0, "conversation_count": 0}
        
    def _load_config(self, config_path: str) -> Dict:
        """Load optimized models configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def select_optimal_model(self, context: ConversationContext) -> Tuple[str, str]:
        """
        Select the optimal model based on conversation context and cost efficiency
        Returns: (model_id, reason)
        """
        # Check budget constraints first
        if self._is_budget_exceeded():
            return self._get_budget_model(), "Budget optimization"
        
        # Route based on conversation type
        routing_rules = self.config.get("routing_rules", {})
        
        if context.conversation_type == "memory":
            if context.estimated_tokens > 100000:
                return "gemini-2.5-flash", "Massive context window needed"
            
        elif context.conversation_type == "autonomous":
            return "grok-3-mini", "Specialized autonomous development"
            
        elif context.conversation_type == "intimate":
            if context.priority_level >= 4:
                return "claude-3.7-sonnet", "Maximum empathy for intimate conversation"
            
        elif context.conversation_type == "casual":
            if context.estimated_tokens > 50000:
                return "gemini-2.5-flash", "Large context + cost efficiency"
            else:
                return "gemini-2.5-flash", "Primary cost-effective model"
        
        # Default to primary model
        return self.config.get("default_llm_id", "gemini-2.5-flash"), "Default primary model"
    
    def estimate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a conversation with specified model"""
        model_config = self.config["models"].get(model_id, {})
        
        input_cost = (input_tokens / 1_000_000) * model_config.get("cost_per_1m_input", 0)
        output_cost = (output_tokens / 1_000_000) * model_config.get("cost_per_1m_output", 0)
        
        return input_cost + output_cost
    
    def _is_budget_exceeded(self) -> bool:
        """Check if daily budget is exceeded"""
        daily_budget = self.config.get("cost_optimization", {}).get("daily_budget_usd", 35)
        return self.cost_tracker["daily_spend"] >= daily_budget * 0.9  # 90% threshold
    
    def _get_budget_model(self) -> str:
        """Get most cost-effective model for budget constraints"""
        return "gpt-4.1-nano"  # Fallback budget option
    
    def track_usage(self, model_id: str, input_tokens: int, output_tokens: int, cost: float):
        """Track model usage for optimization"""
        if model_id not in self.usage_stats:
            self.usage_stats[model_id] = {
                "total_calls": 0,
                "total_cost": 0.0,
                "total_tokens": 0,
                "average_cost_per_call": 0.0
            }
        
        stats = self.usage_stats[model_id]
        stats["total_calls"] += 1
        stats["total_cost"] += cost
        stats["total_tokens"] += input_tokens + output_tokens
        stats["average_cost_per_call"] = stats["total_cost"] / stats["total_calls"]
        
        # Update daily tracker
        self.cost_tracker["daily_spend"] += cost
        self.cost_tracker["conversation_count"] += 1
    
    def get_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on usage patterns"""
        recommendations = []
        
        # Analyze cost efficiency
        total_daily_spend = self.cost_tracker["daily_spend"]
        target_budget = self.config.get("cost_optimization", {}).get("daily_budget_usd", 35)
        
        if total_daily_spend > target_budget * 0.8:
            recommendations.append(
                f"💰 Consider routing more conversations to Gemini 2.5 Flash (cost: {total_daily_spend:.2f})"
            )
        
        # Analyze model distribution
        total_calls = sum(stats["total_calls"] for stats in self.usage_stats.values())
        if total_calls > 0:
            for model_id, stats in self.usage_stats.items():
                percentage = (stats["total_calls"] / total_calls) * 100
                if model_id == "claude-3.7-sonnet" and percentage > 20:
                    recommendations.append(
                        f"🎯 Claude 3.7 Sonnet usage at {percentage:.1f}% - consider reserving for intimate conversations only"
                    )
        
        return recommendations
    
    def generate_daily_report(self) -> Dict:
        """Generate daily optimization report"""
        return {
            "total_spend": self.cost_tracker["daily_spend"],
            "total_conversations": self.cost_tracker["conversation_count"],
            "average_cost_per_conversation": (
                self.cost_tracker["daily_spend"] / max(self.cost_tracker["conversation_count"], 1)
            ),
            "model_usage": self.usage_stats,
            "optimization_recommendations": self.get_optimization_recommendations(),
            "budget_utilization": (
                self.cost_tracker["daily_spend"] / 
                self.config.get("cost_optimization", {}).get("daily_budget_usd", 35)
            ) * 100
        }

# Example usage
if __name__ == "__main__":
    optimizer = ModelOptimizer()
    
    # Test different conversation contexts
    contexts = [
        ConversationContext("casual", 1000, 2, False, False, False),
        ConversationContext("intimate", 2000, 5, True, True, False),
        ConversationContext("autonomous", 5000, 4, True, False, False),
        ConversationContext("memory", 150000, 3, False, False, False)
    ]
    
    print("🧠 KOR'TANA MODEL OPTIMIZATION RECOMMENDATIONS")
    print("=" * 60)
    
    for context in contexts:
        model_id, reason = optimizer.select_optimal_model(context)
        estimated_cost = optimizer.estimate_cost(model_id, context.estimated_tokens, 500)
        
        print(f"📋 Context: {context.conversation_type}")
        print(f"   🎯 Selected Model: {model_id}")
        print(f"   💡 Reason: {reason}")
        print(f"   💰 Estimated Cost: ${estimated_cost:.4f}")
        print()
