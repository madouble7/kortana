#!/usr/bin/env python3
"""
Simple test for centralized services without package imports
"""

import os
import sys

# Add project root to path
project_root = r"C:\project-kortana"
sys.path.insert(0, project_root)
os.chdir(project_root)


def test_services_direct_import():
    """Test importing services directly"""
    print("🔧 Testing Direct Services Import")
    print("=" * 40)

    try:
        # Test importing config directly
        sys.path.insert(0, os.path.join(project_root, "src"))
        from config.schema import create_default_config

        config = create_default_config()
        print("✅ Config import successful")

        # Test importing services module directly
        from kortana.core.services import (
            get_chat_engine,
            get_covenant_enforcer,
            initialize_core_services,
        )

        print("✅ Services import successful")

        # Test initialization
        initialize_core_services(config)
        print("✅ Services initialization successful")

        # Test getting services
        brain = get_chat_engine()
        covenant = get_covenant_enforcer()
        print(f"✅ Retrieved ChatEngine: {type(brain)}")
        print(f"✅ Retrieved CovenantEnforcer: {type(covenant)}")

        print("\n🎉 Direct services test passed!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_services_direct_import()
