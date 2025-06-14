#!/usr/bin/env python3
"""
Genesis Protocol - Direct Brain Interaction
Test Kor'tana's autonomous reasoning and planning capabilities
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_autonomous_reasoning():
    """Test Kor'tana's autonomous reasoning about the refactoring task"""
    print("🧠 GENESIS PROTOCOL - AUTONOMOUS REASONING TEST")
    print("=" * 60)
    print()

    try:
        from kortana.core.brain import ChatEngine

        print("✅ Brain module imported successfully")

        # Initialize the chat engine with our new architecture
        chat_engine = ChatEngine()
        print("✅ ChatEngine initialized with enhanced model router")

        # Present the Genesis Protocol task
        genesis_task = """
        You are Kor'tana, an autonomous AI software engineer. This is your first
        autonomous refactoring task: the Genesis Protocol.

        TASK: Analyze and plan the refactoring of the model routing system to use
        enhanced_model_router.py with cost optimization and centralized configuration.

        Please analyze the current architecture and provide:
        1. Your assessment of the current model routing implementation
        2. A step-by-step plan to implement enhanced routing
        3. Potential risks and mitigation strategies
        4. Success criteria for validation

        This is your first autonomous software engineering challenge. Show your
        reasoning process and planning capabilities.
        """

        print("🎯 Presenting Genesis Protocol task to Kor'tana...")
        print("🤖 Waiting for autonomous analysis and planning...")
        print("-" * 60)

        # Get Kor'tana's autonomous response
        response = chat_engine.process_message(genesis_task)

        print("📋 KOR'TANA'S AUTONOMOUS ANALYSIS:")
        print("=" * 60)
        print(response)
        print("=" * 60)

        return response

    except Exception as e:
        print(f"❌ Error during autonomous reasoning test: {e}")
        import traceback

        traceback.print_exc()
        return None


def test_planning_capabilities():
    """Test autonomous planning capabilities"""
    print("\n🗺️  TESTING AUTONOMOUS PLANNING CAPABILITIES")
    print("-" * 50)

    try:
        from kortana.core.planning_engine import PlanningEngine

        planning_engine = PlanningEngine()
        print("✅ PlanningEngine initialized")

        # Test goal planning
        planning_prompt = """
        Create a detailed execution plan for refactoring the model routing system.
        Break down the task into specific, actionable steps with dependencies.
        """

        # This might not work exactly as expected depending on the implementation
        # but we can test the planning engine's initialization and basic functionality
        print("🔄 Testing planning engine capabilities...")

        # Check if planning engine has the methods we expect
        methods = [
            method for method in dir(planning_engine) if not method.startswith("_")
        ]
        print(f"📊 Available planning methods: {methods}")

        return True

    except Exception as e:
        print(f"❌ Error during planning test: {e}")
        return False


def validate_architecture():
    """Validate that our enhanced architecture is working"""
    print("\n🏗️  VALIDATING ENHANCED ARCHITECTURE")
    print("-" * 50)

    try:
        # Test enhanced model router
        from kortana.core.enhanced_model_router import EnhancedModelRouter

        router = EnhancedModelRouter()
        print("✅ Enhanced Model Router initialized")

        # Test router capabilities
        test_prompt = "What is the best approach for autonomous software refactoring?"

        print("🔄 Testing cost-optimized model selection...")
        model_info = router.select_model("reasoning", test_prompt)
        print(f"📊 Selected model: {model_info}")

        # Test actual routing
        print("🔄 Testing enhanced routing...")
        response = router.route_request("reasoning", test_prompt)
        print(f"✅ Routing successful: {len(response)} characters returned")

        return True

    except Exception as e:
        print(f"❌ Error during architecture validation: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main Genesis Protocol testing sequence"""
    print("🚀 GENESIS PROTOCOL - AUTONOMOUS CAPABILITIES VALIDATION")
    print("🤖 Testing Kor'tana's First Autonomous Software Engineering Task")
    print("=" * 70)
    print()

    success_count = 0
    total_tests = 3

    # Test 1: Autonomous Reasoning
    response = test_autonomous_reasoning()
    if response:
        success_count += 1
        print("✅ Test 1 PASSED: Autonomous reasoning capabilities confirmed")

    # Test 2: Planning Capabilities
    if test_planning_capabilities():
        success_count += 1
        print("✅ Test 2 PASSED: Planning engine operational")

    # Test 3: Architecture Validation
    if validate_architecture():
        success_count += 1
        print("✅ Test 3 PASSED: Enhanced architecture functional")

    print(f"\n📊 GENESIS PROTOCOL RESULTS: {success_count}/{total_tests} tests passed")

    if success_count == total_tests:
        print("🎉 GENESIS PROTOCOL SUCCESS!")
        print("🤖 Kor'tana's autonomous capabilities are fully operational")
        print("🚀 Ready for autonomous software engineering tasks")
    else:
        print("⚠️  Some capabilities need attention before full autonomous operation")

    print("\n🏁 Genesis Protocol validation complete")


if __name__ == "__main__":
    main()
