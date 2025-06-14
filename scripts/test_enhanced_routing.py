#!/usr/bin/env python3
"""
Test script for Enhanced Model Router

This script tests the enhanced model routing system with various scenarios
to ensure optimal model selection and cost optimization.
"""

import logging
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, '.')

from src.kortana.config import load_config
from src.kortana.core.enhanced_model_router import EnhancedModelRouter, TaskType

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_task_analysis():
    """Test the task analysis functionality."""
    print("\n=== Testing Task Analysis ===")

    try:
        settings = load_config()
        router = EnhancedModelRouter(settings)

        test_cases = [
            ("Explain how photosynthesis works step by step", TaskType.REASONING),
            (
                "I'm feeling really sad today and need someone to talk to",
                TaskType.EMOTIONAL_SUPPORT,
            ),
            (
                "Write a creative story about a time-traveling cat",
                TaskType.CREATIVE_WRITING,
            ),
            ("Can you help me debug this Python code?", TaskType.CODING),
            ("What's the weather like?", TaskType.GENERAL_CHAT),
            ("Analyze this image and tell me what you see", TaskType.VISION),
            (
                "Please explain the quarterly sales data in detail and provide comprehensive insights into market trends, customer behavior patterns, seasonal variations, and recommendations for the next quarter based on historical performance and current market conditions.",
                TaskType.LONGFORM,
            ),
        ]

        for user_input, expected_task in test_cases:
            detected_task = router.analyze_task_type(user_input, {})
            status = "✓" if detected_task == expected_task else "✗"
            print(f"{status} Input: {user_input[:50]}...")
            print(
                f"   Expected: {expected_task.value}, Detected: {detected_task.value}"
            )

    except Exception as e:
        logger.error(f"Task analysis test failed: {e}")


def test_model_selection():
    """Test model selection for different task types."""
    print("\n=== Testing Model Selection ===")

    try:
        settings = load_config()
        router = EnhancedModelRouter(settings)

        for task_type in TaskType:
            model_id = router.select_optimal_model(task_type, prefer_free=True)
            model_info = router.get_model_info(model_id)

            cost_indicator = (
                "FREE"
                if model_info and model_info.capabilities.cost_per_1m_input == 0.0
                else "PAID"
            )
            print(
                f"Task: {task_type.value:15} → Model: {model_id:25} ({cost_indicator})"
            )

    except Exception as e:
        logger.error(f"Model selection test failed: {e}")


def test_cost_optimization():
    """Test cost optimization features."""
    print("\n=== Testing Cost Optimization ===")

    try:
        settings = load_config()
        router = EnhancedModelRouter(settings)

        # Test with free preference
        reasoning_model_free = router.select_optimal_model(
            TaskType.REASONING, prefer_free=True
        )

        # Test without free preference
        reasoning_model_performance = router.select_optimal_model(
            TaskType.REASONING, prefer_free=False
        )

        print(f"Reasoning task (prefer free): {reasoning_model_free}")
        print(f"Reasoning task (prefer performance): {reasoning_model_performance}")

        # Test cost estimation
        test_input_tokens = 1000
        test_output_tokens = 500

        for model_id in router.get_available_models():
            cost = router.estimate_cost(model_id, test_input_tokens, test_output_tokens)
            print(f"Cost for {model_id}: ${cost:.4f}")

    except Exception as e:
        logger.error(f"Cost optimization test failed: {e}")


def test_full_routing():
    """Test full routing pipeline."""
    print("\n=== Testing Full Routing Pipeline ===")

    try:
        settings = load_config()
        router = EnhancedModelRouter(settings)

        test_scenarios = [
            {
                "input": "Help me solve this complex math problem: find the derivative of x^3 + 2x^2 - 5x + 1",
                "context": {"context_length": 100},
            },
            {
                "input": "I'm feeling overwhelmed with work and need some emotional support",
                "context": {"context_length": 50},
            },
            {
                "input": "Write a function in Python that sorts a list using bubble sort",
                "context": {"context_length": 80},
            },
            {"input": "What's your favorite color?", "context": {"context_length": 25}},
        ]

        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\nScenario {i}: {scenario['input'][:50]}...")

            model_id, voice_style, model_params = router.route(
                scenario["input"], scenario["context"], prefer_free=True
            )

            model_info = router.get_model_info(model_id)
            cost_info = (
                "FREE"
                if model_info and model_info.capabilities.cost_per_1m_input == 0.0
                else "PAID"
            )

            print(f"  Model: {model_id} ({cost_info})")
            print(f"  Voice Style: {voice_style}")
            print(f"  Temperature: {model_params.get('temperature', 'N/A')}")

    except Exception as e:
        logger.error(f"Full routing test failed: {e}")


def test_deepseek_integration():
    """Test DeepSeek R1 integration specifically."""
    print("\n=== Testing DeepSeek R1 Integration ===")

    try:
        settings = load_config()
        router = EnhancedModelRouter(settings)

        # Check if DeepSeek is available
        available_models = router.get_available_models()
        deepseek_models = [m for m in available_models if "deepseek" in m.lower()]

        print(f"Available DeepSeek models: {deepseek_models}")

        if "deepseek-r1-0528-free" in available_models:
            model_info = router.get_model_info("deepseek-r1-0528-free")
            print("DeepSeek R1 model info:")
            print(f"  Provider: {model_info.provider}")
            print(f"  Cost per 1M input: ${model_info.capabilities.cost_per_1m_input}")
            print(
                f"  Cost per 1M output: ${model_info.capabilities.cost_per_1m_output}"
            )
            print(
                f"  Context window: {model_info.capabilities.context_window:,} tokens"
            )
            print(f"  Supports reasoning: {model_info.capabilities.supports_reasoning}")
            print(f"  Preferred tasks: {[t.value for t in model_info.preferred_tasks]}")

            # Test routing to DeepSeek for reasoning tasks
            reasoning_input = "Solve this step by step: If a train travels at 60 mph for 2 hours, then 80 mph for 1.5 hours, what's the average speed?"
            model_id, voice_style, model_params = router.route(
                reasoning_input, {}, prefer_free=True
            )

            print("\nReasoning task routing:")
            print(f"  Selected model: {model_id}")
            print(f"  Voice style: {voice_style}")

        else:
            print("DeepSeek R1 0528 free model not found in configuration!")

    except Exception as e:
        logger.error(f"DeepSeek integration test failed: {e}")


def main():
    """Run all tests."""
    print("Enhanced Model Router Test Suite")
    print("=" * 50)

    # Check for required environment variables
    required_env_vars = ["OPENROUTER_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        print(f"\nWarning: Missing environment variables: {missing_vars}")
        print("Some tests may fail or use fallback configurations.")

    test_task_analysis()
    test_model_selection()
    test_cost_optimization()
    test_full_routing()
    test_deepseek_integration()

    print("\n" + "=" * 50)
    print("Test suite completed!")


if __name__ == "__main__":
    main()
