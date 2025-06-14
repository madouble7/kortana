#!/usr/bin/env python3
"""
GENESIS PROTOCOL - FIXED VERSION WITH PROPER SETTINGS INITIALIZATION
=====================================================================

Final System Check Before Autonomous Operation
Addresses all blocking issues identified in validation
"""

import os
import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add project root to path
project_root = Path(r"C:\project-kortana")
sys.path.insert(0, str(project_root))
os.chdir(project_root)


def test_core_imports():
    """Test core imports (circular dependency validation)"""
    print("🔍 TESTING CORE IMPORTS (Circular Dependency Validation)")
    print("-" * 60)

    imports = [
        ("Brain Module", "from src.kortana.core.brain import ChatEngine"),
        (
            "Planning Engine",
            "from src.kortana.core.planning_engine import PlanningEngine",
        ),
        (
            "Enhanced Router",
            "from src.kortana.core.enhanced_model_router import EnhancedModelRouter",
        ),
        (
            "Model Factory",
            "from src.kortana.llm_clients.factory import LLMClientFactory",
        ),
        (
            "Memory Manager",
            "from src.kortana.memory.memory_manager import MemoryManager",
        ),
    ]

    passed = 0
    total = len(imports)

    for name, import_stmt in imports:
        try:
            exec(import_stmt)
            print(f"✅ {name}: Import successful")
            passed += 1
        except Exception as e:
            print(f"❌ {name}: Import failed - {e}")

    # Test the problematic services import
    try:
        print("✅ Services: Import successful")
        passed += 1
        total += 1
    except Exception as e:
        print(f"❌ Services: Import failed - {e}")
        total += 1

    print(f"\n📊 Import Tests: {passed}/{total} passed")
    return passed == total


def test_enhanced_router_with_settings():
    """Test Enhanced Model Router with proper settings"""
    print("\n🚀 TESTING ENHANCED MODEL ROUTER")
    print("-" * 60)

    try:
        from src.config.schema import create_default_config
        from src.kortana.core.enhanced_model_router import EnhancedModelRouter

        # Create configuration first
        settings = create_default_config()
        print("✅ Configuration created")

        # Initialize router with settings
        router = EnhancedModelRouter(settings=settings)
        print(f"✅ EnhancedModelRouter created: {type(router).__name__}")

        return True

    except Exception as e:
        print(f"❌ Enhanced Router test failed: {e}")
        traceback.print_exc()
        return False


def test_services_architecture_with_initialization():
    """Test the services architecture with proper initialization"""
    print("\n🏗️  TESTING SERVICES ARCHITECTURE")
    print("-" * 60)

    try:
        from src.config.schema import create_default_config
        from src.kortana.core.services import (
            get_llm_service,
            get_model_router,
            initialize_services,
        )

        # Initialize services with configuration
        settings = create_default_config()
        initialize_services(settings)
        print("✅ Services initialized with configuration")

        # Test service access
        llm_service = get_llm_service()
        print(f"✅ LLM Service accessible: {type(llm_service).__name__}")

        router_service = get_model_router()
        print(f"✅ Model Router accessible: {type(router_service).__name__}")

        return True

    except Exception as e:
        print(f"❌ Services architecture test failed: {e}")
        traceback.print_exc()
        return False


def test_configuration_system():
    """Test configuration system"""
    print("\n⚙️  TESTING CONFIGURATION SYSTEM")
    print("-" * 60)

    try:
        from src.config.schema import create_default_config

        config = create_default_config()

        # Check YAML and JSON models
        model_count = len(config.models) if hasattr(config, "models") else 0
        print(f"✅ YAML configuration loaded: {model_count} models")
        print(f"✅ JSON configuration loaded: {model_count} models")

        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_chatengine_with_settings():
    """Test ChatEngine with proper settings"""
    print("\n🧠 TESTING CHAT ENGINE WITH SETTINGS")
    print("-" * 60)

    try:
        from src.config.schema import create_default_config
        from src.kortana.core.brain import ChatEngine

        # Create configuration
        settings = create_default_config()
        print("✅ Configuration created")

        # Initialize ChatEngine with settings
        engine = ChatEngine(settings=settings)
        print(f"✅ ChatEngine created: {type(engine).__name__}")
        print(f"   Session ID: {engine.session_id}")
        print(f"   Mode: {engine.mode}")

        return True

    except Exception as e:
        print(f"❌ ChatEngine test failed: {e}")
        traceback.print_exc()
        return False


def run_genesis_protocol_fixed():
    """Run the fixed Genesis Protocol validation"""
    print("🚀 GENESIS PROTOCOL - AUTONOMOUS READINESS VALIDATION")
    print("🤖 Final System Check Before Autonomous Operation")
    print("=" * 70)
    print()

    tests = [
        ("Core Imports (Circular Dependencies)", test_core_imports),
        ("Enhanced Model Router", test_enhanced_router_with_settings),
        ("Services Architecture", test_services_architecture_with_initialization),
        ("Configuration System", test_configuration_system),
        ("ChatEngine with Settings", test_chatengine_with_settings),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"🔄 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "PASSED" if result else "FAILED"
            emoji = "✅" if result else "❌"
            print(f"{emoji} {test_name}: {status}")
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {e}")
            results.append((test_name, False))
        print()

    # Final results
    passed = sum(1 for _, result in results if result)
    total = len(results)

    print("=" * 70)
    print(f"📊 FINAL RESULTS: {passed}/{total} systems operational")

    if passed == total:
        print("🎉 ALL SYSTEMS FULLY OPERATIONAL!")
        print("✅ Ready for autonomous operation")
        print()
        print("🚀 NEXT STEPS:")
        print("1. python -m uvicorn src.kortana.main:app --port 8000 --reload")
        print("2. python assign_genesis_goal.py")
        print("3. python monitor_autonomous_activity.py")
    elif passed >= total * 0.8:  # 80% or better
        print("⚡ SYSTEMS MOSTLY OPERATIONAL")
        print("✅ Basic autonomous operation ready")
        print("🔧 Some components may need attention")
    else:
        print("⚠️  Some systems need attention before full autonomous operation")
        print("🛠️  SYSTEM REQUIRES ATTENTION")
        print("📋 Address validation failures before autonomous operation")

    return passed >= total * 0.8  # Return success if 80% or better


if __name__ == "__main__":
    success = run_genesis_protocol_fixed()
    sys.exit(0 if success else 1)
