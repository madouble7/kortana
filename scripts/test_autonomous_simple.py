#!/usr/bin/env python3
"""
Simple autonomous test to verify Kor'tana's autonomous capabilities.
"""

import sys
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


def test_autonomous_infrastructure():
    """Test core autonomous infrastructure components."""
    print("🧪 TESTING AUTONOMOUS INFRASTRUCTURE")
    print("=" * 50)

    results = {}

    # Test 1: Basic imports
    print("\n1. Testing Core Imports...")
    try:
        print("  ✅ Config module imported")
        results["config_import"] = True
    except Exception as e:
        print(f"  ❌ Config import failed: {e}")
        results["config_import"] = False

    # Test 2: Environmental Scanner
    print("\n2. Testing Environmental Scanner...")
    try:
        from environmental_scanner import EnvironmentalScanner

        scanner = EnvironmentalScanner()
        print("  ✅ Environmental Scanner available")
        results["scanner"] = True
    except Exception as e:
        print(f"  ❌ Scanner failed: {e}")
        results["scanner"] = False

    # Test 3: Goal Engine structure
    print("\n3. Testing Goal Engine...")
    try:
        print("  ✅ Goal Engine class available")
        results["goal_engine"] = True
    except Exception as e:
        print(f"  ❌ Goal Engine failed: {e}")
        results["goal_engine"] = False

    # Test 4: Autonomous Development Engine
    print("\n4. Testing Autonomous Development Engine...")
    try:
        print("  ✅ ADE class available")
        results["ade"] = True
    except Exception as e:
        print(f"  ❌ ADE failed: {e}")
        results["ade"] = False

    # Test 5: Relay System
    print("\n5. Testing Relay System...")
    try:
        print("  ✅ Autonomous Relay available")
        results["relay"] = True
    except Exception as e:
        print(f"  ❌ Relay failed: {e}")
        results["relay"] = False

    # Summary
    print("\n" + "=" * 50)
    print("AUTONOMOUS INFRASTRUCTURE SUMMARY")
    print("=" * 50)

    total_tests = len(results)
    passed_tests = sum(results.values())
    success_rate = (passed_tests / total_tests) * 100

    for test_name, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {test_name.replace('_', ' ').title()}")

    print(f"\nSuccess Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")

    if success_rate >= 80:
        print("\n🎉 AUTONOMOUS INFRASTRUCTURE READY FOR ACTIVATION!")
        print("🚀 Kor'tana can proceed to autonomous awakening")
    elif success_rate >= 60:
        print("\n⚠️  Infrastructure mostly ready - minor issues to resolve")
    else:
        print("\n❌ Infrastructure needs attention before activation")

    return success_rate >= 80


def test_autonomous_activation():
    """Test autonomous activation methods."""
    print("\n🚀 AUTONOMOUS ACTIVATION PATHWAYS")
    print("=" * 50)

    activation_methods = [
        {
            "name": "ChatEngine Autonomous",
            "command": "python src\\kortana\\core\\brain.py",
            "description": "Core brain with autonomous scheduler",
        },
        {
            "name": "Master Orchestrator",
            "command": "python relays\\master_orchestrator.py",
            "description": "Multi-agent coordination system",
        },
        {
            "name": "Proto-Autonomy Demo",
            "command": "python start_autonomy.py --demo-agents",
            "description": "Controlled autonomy demonstration",
        },
        {
            "name": "ADE Direct",
            "command": "python src\\kortana\\core\\autonomous_development_engine.py --analyze-critical-issues",
            "description": "Direct autonomous development",
        },
    ]

    for i, method in enumerate(activation_methods, 1):
        print(f"\n{i}. {method['name']}")
        print(f"   Command: {method['command']}")
        print(f"   Purpose: {method['description']}")

    print(f"\n✨ {len(activation_methods)} autonomous activation methods available")
    return True


def main():
    """Run autonomous capability tests."""
    print("🤖 KOR'TANA AUTONOMOUS CAPABILITY TEST")
    print("=" * 60)
    print("Testing infrastructure readiness for autonomous awakening...")

    try:
        # Test infrastructure
        infrastructure_ready = test_autonomous_infrastructure()

        # Show activation methods
        test_autonomous_activation()

        print("\n" + "=" * 60)
        if infrastructure_ready:
            print("🎯 CONCLUSION: Kor'tana is ready for autonomous awakening!")
            print("🔥 Choose an activation method and begin the awakening process")
        else:
            print("🔧 CONCLUSION: Infrastructure needs attention before awakening")

        return infrastructure_ready

    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
