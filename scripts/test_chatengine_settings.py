#!/usr/bin/env python3
"""
Test ChatEngine initialization with proper settings
"""

import os
import sys

# Add project root to path
project_root = r"C:\project-kortana"
sys.path.insert(0, project_root)
os.chdir(project_root)

print("🔍 TESTING CHATENGINE WITH PROPER SETTINGS")
print("=" * 50)

try:
    print("1. Loading configuration...")
    from src.config.schema import create_default_config

    config = create_default_config()
    print("✅ Configuration loaded")

    print("2. Testing ChatEngine import...")
    from src.kortana.core.brain import ChatEngine

    print("✅ ChatEngine imported")

    print("3. Creating ChatEngine with settings...")
    engine = ChatEngine(settings=config)
    print("✅ ChatEngine created successfully!")
    print(f"   Type: {type(engine).__name__}")
    print(f"   Session ID: {engine.session_id}")
    print(f"   Mode: {engine.mode}")

    print("\n4. Testing EnhancedModelRouter with settings...")
    from src.kortana.core.enhanced_model_router import EnhancedModelRouter

    router = EnhancedModelRouter(settings=config)
    print("✅ EnhancedModelRouter created successfully!")
    print(f"   Type: {type(router).__name__}")

except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback

    traceback.print_exc()

print("\n🎯 CHATENGINE TEST COMPLETE")
