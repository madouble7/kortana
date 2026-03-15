#!/usr/bin/env python3
"""
Simple test for Enhanced Model Router
"""

import logging
import sys

# Add the project root to the Python path
sys.path.insert(0, ".")

from src.kortana.config import load_config
from src.kortana.core.enhanced_model_router import EnhancedModelRouter, TaskType

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Run simple tests."""
    print("Enhanced Model Router Simple Test")
    print("=" * 40)

    try:
        # Try to load config
        print("Loading configuration...")
        settings = load_config()
        print(f"✓ Configuration loaded: {type(settings)}")

        # Initialize router
        print("Initializing router...")
        router = EnhancedModelRouter(settings)
        print("✓ Router initialized")

        # Test basic functionality
        print("Testing model selection...")
        model_id = router.select_optimal_model(TaskType.REASONING, prefer_free=True)
        print(f"✓ Selected model for reasoning: {model_id}")

        # Test routing
        print("Testing routing...")
        test_input = "Help me solve this math problem"
        model_id, voice_style, model_params = router.route(
            test_input, {}, prefer_free=True
        )
        print(f"✓ Routing result: {model_id}, {voice_style}")

        print("\n" + "=" * 40)
        print("All tests passed!")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
