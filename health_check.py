#!/usr/bin/env python3
"""
Kortana Project Health Check
"""


def test_import(module_name, display_name):
    """Test importing a module and report results."""
    try:
        __import__(module_name)
        print(f"✅ {display_name}: SUCCESS")
        return True
    except Exception as e:
        print(f"❌ {display_name}: FAILED - {e}")
        return False


def main():
    print("=== KORTANA PROJECT HEALTH CHECK ===")
    print("Testing core module imports...\n")

    results = []

    # Test core modules
    results.append(test_import("src.kortana.config", "Config module"))
    results.append(test_import("src.kortana.core.brain", "Brain module"))
    results.append(
        test_import("src.kortana.agents.autonomous_agents", "Autonomous agents")
    )
    results.append(test_import("src.kortana.llm_clients.factory", "LLM clients"))
    results.append(test_import("src.kortana.core.covenant", "Covenant enforcer"))

    print("\n=== HEALTH CHECK SUMMARY ===")
    total_tests = len(results)
    passed_tests = sum(results)
    failed_tests = total_tests - passed_tests

    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")

    health_percentage = (passed_tests / total_tests) * 100
    print(f"Health Score: {health_percentage:.1f}%")

    if health_percentage >= 90:
        print("🎉 EXCELLENT health status!")
    elif health_percentage >= 75:
        print("✅ GOOD health status")
    elif health_percentage >= 50:
        print("⚠️ MODERATE health - improvements needed")
    else:
        print("❌ POOR health - critical issues need attention")


if __name__ == "__main__":
    main()
