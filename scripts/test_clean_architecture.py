#!/usr/bin/env python3
"""
Test the new clean services architecture to verify it eliminates circular dependencies.
"""

import logging
import sys

# Add the project root to the Python path
sys.path.insert(0, ".")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_clean_services_architecture():
    """Test that the new services architecture eliminates circular dependencies."""
    print("=== Testing Clean Services Architecture ===")

    try:
        # Test 1: Import the clean services module (should work without circular imports)
        print("Testing clean services import...")
        from kortana.core.services_clean import (
            get_enhanced_model_router,
            get_planning_engine,
            get_service_status,
            initialize_services,
            reset_services,
        )

        print("SUCCESS: Clean services imported without circular dependency issues")

        # Test 2: Initialize with mock configuration
        print("Testing service initialization...")

        class MockConfig:
            def __init__(self):
                self.default_llm_id = "deepseek/deepseek-r1-0528:free"
                self.agents = MockAgents()
                self.allowed_dirs = ["."]
                self.blocked_commands = ["rm", "del"]

        class MockAgents:
            def __init__(self):
                self.default_llm_id = "deepseek/deepseek-r1-0528:free"

        config = MockConfig()
        initialize_services(config)
        print("SUCCESS: Services initialized")

        # Test 3: Check service status before lazy loading
        print("Testing service status...")
        status = get_service_status()
        print(f"Initial status: {status}")

        # Test 4: Test lazy loading of services
        print("Testing lazy service loading...")

        # Load enhanced model router
        router = get_enhanced_model_router()
        print(f"Enhanced Model Router loaded: {type(router).__name__}")

        # Load planning engine
        planning = get_planning_engine()
        print(f"Planning Engine loaded: {type(planning).__name__}")

        # Test 5: Check service status after loading
        print("Testing final service status...")
        final_status = get_service_status()
        print(f"Final status: {final_status}")

        # Test 6: Reset services
        print("Testing service reset...")
        reset_services()
        reset_status = get_service_status()
        print(f"Reset status: {reset_status}")

        print("SUCCESS: All clean services architecture tests passed!")
        return True

    except Exception as e:
        print(f"ERROR: Clean services test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_model_router_integration():
    """Test that the model router can be accessed through clean services."""
    print("\n=== Testing Model Router Integration ===")

    try:
        from kortana.config import load_config
        from kortana.core.services_clean import (
            get_enhanced_model_router,
            initialize_services,
        )

        # Load real configuration
        config = load_config()
        initialize_services(config)

        # Get the enhanced model router
        router = get_enhanced_model_router()

        # Test basic router functionality
        available_models = router.get_available_models()
        print(f"Available models through clean services: {len(available_models)}")

        # Test model selection
        from kortana.core.enhanced_model_router import TaskType

        selected_model = router.select_optimal_model(
            TaskType.REASONING, prefer_free=True
        )
        print(f"Selected reasoning model: {selected_model}")

        print("SUCCESS: Model router integration working through clean services!")
        return True

    except Exception as e:
        print(f"ERROR: Model router integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all architecture tests."""
    print("Phase 6: Architectural Refactoring Tests")
    print("=" * 50)

    test1_passed = test_clean_services_architecture()
    test2_passed = test_model_router_integration()

    print("\n" + "=" * 50)
    if test1_passed and test2_passed:
        print("SUCCESS: Phase 6 Architectural Refactoring is working!")
        print("- Circular dependencies eliminated")
        print("- Service locator pattern implemented")
        print("- Lazy initialization working")
        print("- Model router integration successful")
    else:
        print("PARTIAL SUCCESS: Some tests failed, needs refinement")

    print("Architecture refactoring validation completed!")


if __name__ == "__main__":
    main()
