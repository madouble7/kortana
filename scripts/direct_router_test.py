#!/usr/bin/env python3
"""
Direct test for Enhanced Model Router
"""

import logging
import sys

# Add the project root to the Python path
sys.path.insert(0, ".")

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Import only what we need
    from src.kortana.core.enhanced_model_router import EnhancedModelRouter, TaskType

    # Create a minimal settings object
    class MockSettings:
        def __init__(self):
            self.paths = {}

    def main():
        """Run direct tests."""
        print("Enhanced Model Router Direct Test")
        print("=" * 40)

        try:
            # Create mock settings
            settings = MockSettings()
            print("✓ Mock settings created")

            # Initialize router
            router = EnhancedModelRouter(settings)
            print("✓ Router initialized")

            # Test model selection
            model_id = router.select_optimal_model(TaskType.REASONING, prefer_free=True)
            print(f"✓ Selected model for reasoning: {model_id}")

            # Test available models
            available = router.get_available_models()
            print(f"✓ Available models: {len(available)}")
            for model in available[:3]:  # Show first 3
                print(f"  - {model}")

            # Test routing
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

except ImportError as e:
    print(f"Import error: {e}")
    print("Could not import enhanced model router")
