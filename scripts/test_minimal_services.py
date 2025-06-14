#!/usr/bin/env python3
"""
Test minimal centralized services
"""

import os
import sys

# Add project root to path
project_root = r"C:\project-kortana"
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))
os.chdir(project_root)


def test_minimal_services():
    """Test minimal services"""
    print("🔧 Testing Minimal Services")
    print("=" * 30)

    try:
        # Test config import
        from config.schema import create_default_config

        config = create_default_config()
        print("✅ Config created")

        # Test minimal services
        from kortana.core.services_minimal import (
            get_chat_engine,
            get_covenant_enforcer,
            initialize_core_services,
        )

        print("✅ Minimal services imported")

        # Initialize
        initialize_core_services(config)
        print("✅ Services initialized")

        # Get services
        brain = get_chat_engine()
        covenant = get_covenant_enforcer()
        print(f"✅ ChatEngine: {type(brain)}")
        print(f"✅ CovenantEnforcer: {type(covenant)}")

        print("\n🎉 Minimal services test passed!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_minimal_services()
