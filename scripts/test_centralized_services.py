#!/usr/bin/env python3
"""
Test script to validate centralized services refactoring
"""

import os
import sys

# Add project root to path
project_root = r"C:\project-kortana"
sys.path.insert(0, project_root)
os.chdir(project_root)


def test_centralized_services():
    """Test that centralized services work correctly"""
    print("🔧 Testing Centralized Services Refactoring")
    print("=" * 50)

    try:
        # Test importing the services module
        from kortana.core.services import (
            get_chat_engine,
            get_covenant_enforcer,
            initialize_core_services,
        )

        print("✅ Successfully imported centralized services")

        # Test creating config
        from kortana.config.schema import create_default_config

        config = create_default_config()
        print("✅ Successfully created default config")

        # Test initializing services
        initialize_core_services(config)
        print("✅ Successfully initialized centralized services")

        # Test getting services
        brain = get_chat_engine()
        covenant = get_covenant_enforcer()
        print(f"✅ Successfully retrieved ChatEngine: {type(brain)}")
        print(f"✅ Successfully retrieved CovenantEnforcer: {type(covenant)}")

        # Test Phase 5 system initialization
        from phase5_advanced_autonomous import AdvancedAutonomousKortana

        kortana = AdvancedAutonomousKortana()
        print("✅ Successfully initialized Phase 5 Kor'tana with centralized services")
        print(f"   Brain type: {type(kortana.brain)}")
        print(f"   Covenant type: {type(kortana.covenant)}")

        print(
            "\n🎉 All tests passed! Centralized services refactoring is working correctly."
        )
        return True

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_centralized_services()
