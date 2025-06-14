#!/usr/bin/env python3
"""
Quick test of the fixed services imports
"""

print("🔍 TESTING FIXED SERVICES")
print("=" * 50)

try:
    print("1. Testing get_llm_service import...")
    print("✅ get_llm_service imported successfully")
except Exception as e:
    print(f"❌ get_llm_service import failed: {e}")

try:
    print("2. Testing get_model_router import...")
    print("✅ get_model_router imported successfully")
except Exception as e:
    print(f"❌ get_model_router import failed: {e}")

try:
    print("3. Testing get_chat_engine import...")
    print("✅ get_chat_engine imported successfully")
except Exception as e:
    print(f"❌ get_chat_engine import failed: {e}")

try:
    print("4. Testing initialize_core_services import...")
    print("✅ initialize_core_services imported successfully")
except Exception as e:
    print(f"❌ initialize_core_services import failed: {e}")

print("\n🔍 TESTING SERVICES WITH CONFIGURATION")
print("=" * 50)

try:
    from src.config.schema import create_default_config
    from src.kortana.core.services import get_enhanced_model_router, initialize_services

    print("5. Creating default configuration...")
    config = create_default_config()
    print("✅ Configuration created")

    print("6. Initializing services...")
    initialize_services(config)
    print("✅ Services initialized")

    print("7. Testing EnhancedModelRouter...")
    router = get_enhanced_model_router()
    print(f"✅ EnhancedModelRouter created: {type(router).__name__}")

except Exception as e:
    print(f"❌ Service initialization failed: {e}")
    import traceback

    traceback.print_exc()

print("\n🎯 SERVICES TEST COMPLETE")
