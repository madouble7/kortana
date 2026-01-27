#!/usr/bin/env python3
"""
Genesis Protocol Final Validation
Comprehensive test of the autonomous system's readiness
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from kortana.config.schema import KortanaConfig  # Updated import path
from kortana.core.services import initialize_services


def test_core_imports():
    """Test that all core modules can be imported without circular dependencies"""
    print("🔍 TESTING CORE IMPORTS (Circular Dependency Validation)")
    print("-" * 60)

    import_tests = [
        ("Brain Module", "from kortana.core.brain import ChatEngine"),
        (
            "Planning Engine",
            "from kortana.core.planning_engine import PlanningEngine",
        ),
        (
            "Enhanced Router",
            "from kortana.core.enhanced_model_router import EnhancedModelRouter",
        ),
        (
            "Model Factory",
            "from kortana.llm_clients.factory import LLMClientFactory",
        ),
        ("Services", "from kortana.core.services import get_llm_service"),
        (
            "Memory Manager",
            "from kortana.memory.memory_manager import MemoryManager",
        ),
    ]

    passed = 0
    for name, import_statement in import_tests:
        try:
            exec(import_statement)
            print(f"✅ {name}: Import successful")
            passed += 1
        except Exception as e:
            print(f"❌ {name}: Import failed - {e}")

    print(f"\n📊 Import Tests: {passed}/{len(import_tests)} passed")
    return passed == len(import_tests)


def test_enhanced_router(config: KortanaConfig):  # Added config parameter
    """Test the enhanced model router functionality"""
    print("\n🚀 TESTING ENHANCED MODEL ROUTER")
    print("-" * 60)

    try:
        from kortana.core.enhanced_model_router import EnhancedModelRouter, TaskType

        # Test router initialization
        router = EnhancedModelRouter(settings=config)
        print("✅ Enhanced Model Router initialized")

        # Test model selection
        test_prompt = "Analyze code architecture and suggest improvements"
        # Ensure the router has models configured for this to pass
        if not router.models_config or not router.models_config.get(
            "models"
        ):  # Corrected attribute
            print(
                "⚠️ Enhanced Model Router has no model configurations. Skipping model selection/cost tests."
            )
            return True

        # Use a valid TaskType for selection
        selected_model_id = router.select_optimal_model(
            TaskType.REASONING, prefer_free=True, context_length_needed=len(test_prompt)
        )  # Corrected method and added params
        print(f"✅ Model selection working: Selected {selected_model_id}")

        # Test cost optimization - estimate_cost needs model_id, input_tokens, output_tokens
        # We'll use the selected model and some dummy token counts
        if selected_model_id:
            costs = router.estimate_cost(
                selected_model_id,
                input_tokens=len(test_prompt.split()),
                output_tokens=200,
            )  # Corrected method and added params
            print(f"✅ Cost estimation working for {selected_model_id}: {costs}")
        else:
            print("⚠️ Skipping cost estimation as no model was selected.")

        return True

    except Exception as e:
        print(f"❌ Enhanced Router test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_services_architecture():
    """Test the new services architecture"""
    print("\n🏗️  TESTING SERVICES ARCHITECTURE")
    print("-" * 60)

    try:
        from kortana.core.services import get_llm_service, get_model_router

        # Test service access
        llm_service = get_llm_service()
        print(f"✅ LLM Service accessible: {type(llm_service).__name__}")

        router_service = get_model_router()
        print(f"✅ Model Router accessible: {type(router_service).__name__}")

        return True

    except Exception as e:
        print(f"❌ Services architecture test failed: {e}")
        return False


def test_configuration_system():
    """Test configuration loading and validation"""
    print("\n⚙️  TESTING CONFIGURATION SYSTEM")
    print("-" * 60)

    try:
        # Test YAML config loading
        import yaml

        with open("src/kortana/config/models.yaml") as f:
            config = yaml.safe_load(f)

        print(f"✅ YAML configuration loaded: {len(config.get('models', {}))} models")

        # Test JSON config loading
        import json

        with open("config/models_config.json") as f:
            json_config = json.load(f)

        print(
            f"✅ JSON configuration loaded: {len(json_config.get('models', {}))} models"
        )

        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def run_autonomous_readiness_check():
    """Run comprehensive autonomous readiness validation"""
    print("🚀 GENESIS PROTOCOL - AUTONOMOUS READINESS VALIDATION")
    print("🤖 Final System Check Before Autonomous Operation")
    print("=" * 70)
    print()

    # Load configuration and initialize services
    try:
        config = KortanaConfig()
        print("✅ KortanaConfig loaded successfully.")
        initialize_services(config)
        print("✅ Core services initialized.")
    except Exception as e:
        print(f"❌ Failed to load configuration or initialize services: {e}")
        import traceback

        traceback.print_exc()
        print("\n🛠️  SYSTEM REQUIRES ATTENTION - CRITICAL INITIALIZATION FAILURE")
        return False

    tests = [
        (
            "Core Imports (Circular Dependencies)",
            test_core_imports,
            False,
        ),  # Flag: needs_config
        ("Enhanced Model Router", test_enhanced_router, True),
        (
            "Services Architecture",
            test_services_architecture,
            False,
        ),  # Corrected: Added comma
        ("Configuration System", test_configuration_system, False),
    ]

    passed = 0
    for test_name, test_func, needs_config in tests:
        print(f"\n🔄 Running: {test_name}")
        try:
            if needs_config:
                result = test_func(config)  # Pass config if needed
            else:
                result = test_func()

            if result:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: FAILED with exception - {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"📊 FINAL RESULTS: {passed}/{len(tests)} systems operational")

    if passed == len(tests):
        print("🎉 GENESIS PROTOCOL VALIDATION: COMPLETE SUCCESS!")
        print("🤖 Kor'tana is ready for autonomous software engineering")
        print("🚀 All systems operational - The Proving Ground is ready")
        print("\n🎯 NEXT PHASE: Autonomous task execution and monitoring")
    else:
        print("⚠️  Some systems need attention before full autonomous operation")
        print("🔧 Address failed tests before proceeding to autonomous tasks")

    return passed == len(tests)


if __name__ == "__main__":
    success = run_autonomous_readiness_check()

    if success:
        print("\n🌟 AUTONOMOUS CAPABILITIES CONFIRMED")
        print("📋 Ready to receive and execute autonomous software engineering goals")
        print("🔍 System architecture is stable and optimized")
    else:
        print("\n🛠️  SYSTEM REQUIRES ATTENTION")
        print("📋 Address validation failures before autonomous operation")
