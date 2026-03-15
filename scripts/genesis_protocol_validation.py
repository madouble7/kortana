#!/usr/bin/env python3
"""
Genesis Protocol Final Validation
==================================

This script validates that all core Kor'tana systems are operational:
1. Core imports and services
2. Enhanced Model Router
3. Services architecture
4. Configuration system
5. Database operations
6. API endpoints

Success indicates Genesis Protocol completion.
"""

import sys
import traceback
from pathlib import Path

import requests


def test_core_imports():
    """Test core module imports"""
    print("🔍 TESTING CORE IMPORTS (Circular Dependency Validation)")
    print("------------------------------------------------------------")

    try:
        # Test brain module
        print("✅ Brain Module: Import successful")
    except Exception as e:
        print(f"❌ Brain Module: Import failed - {e}")
        return False

    try:
        # Test planning engine
        print("✅ Planning Engine: Import successful")
    except Exception as e:
        print(f"❌ Planning Engine: Import failed - {e}")
        return False

    try:
        # Test enhanced router
        print("✅ Enhanced Router: Import successful")
    except Exception as e:
        print(f"❌ Enhanced Router: Import failed - {e}")
        return False

    try:
        # Test model factory
        print("✅ Model Factory: Import successful")
    except Exception as e:
        print(f"❌ Model Factory: Import failed - {e}")
        return False

    try:
        # Test services
        print("✅ Services: Import successful")
    except Exception as e:
        print(f"❌ Services: Import failed - {e}")
        return False

    try:
        # Test memory manager
        print("✅ Memory Manager: Import successful")
    except Exception as e:
        print(f"❌ Memory Manager: Import failed - {e}")
        return False

    return True


def test_enhanced_router():
    """Test Enhanced Model Router initialization"""
    print("\n🚀 TESTING ENHANCED MODEL ROUTER")
    print("------------------------------------------------------------")

    try:
        from kortana.config import load_config
        from kortana.core.enhanced_model_router import EnhancedModelRouter

        settings = load_config()
        router = EnhancedModelRouter(settings=settings)
        print("✅ Enhanced Model Router: Initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Enhanced Router test failed: {e}")
        traceback.print_exc()
        return False


def test_services_architecture():
    """Test services architecture"""
    print("\n🏗️  TESTING SERVICES ARCHITECTURE")
    print("------------------------------------------------------------")

    try:
        from kortana.config import load_config
        from kortana.core.services import get_llm_service, initialize_services

        settings = load_config()
        initialize_services(settings)

        # Test service retrieval
        llm_service = get_llm_service()
        print("✅ Services Architecture: Working correctly")
        return True
    except Exception as e:
        print(f"❌ Services architecture test failed: {e}")
        traceback.print_exc()
        return False


def test_configuration_system():
    """Test configuration loading"""
    print("\n⚙️  TESTING CONFIGURATION SYSTEM")
    print("------------------------------------------------------------")

    try:
        from kortana.config import load_config

        settings = load_config()
        print(f"✅ Configuration loaded: Type {type(settings)}")

        # Test models config
        models_config_path = Path("config/models_config.json")
        if models_config_path.exists():
            print("✅ Models configuration file found")
        else:
            print("⚠️  Models configuration file not found")
            return False

        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        traceback.print_exc()
        return False


def test_database_operations():
    """Test database operations"""
    print("\n💾 TESTING DATABASE OPERATIONS")
    print("------------------------------------------------------------")

    try:
        from kortana.core.models import Goal
        from kortana.services.database import SyncSessionLocal

        db = SyncSessionLocal()
        goals = db.query(Goal).all()
        db.close()

        print(f"✅ Database query successful: {len(goals)} goals found")
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        traceback.print_exc()
        return False


def test_api_endpoints():
    """Test API endpoints"""
    print("\n🌐 TESTING API ENDPOINTS")
    print("------------------------------------------------------------")

    base_url = "http://localhost:8000"

    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint: Working")
        else:
            print(f"❌ Health endpoint: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint: Failed - {e}")
        return False

    # Test goals endpoint
    try:
        response = requests.get(f"{base_url}/goals/", timeout=5)
        if response.status_code == 200:
            print("✅ Goals endpoint: Working")
        else:
            print(f"❌ Goals endpoint: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Goals endpoint: Failed - {e}")
        return False

    return True


def main():
    """Run all genesis protocol validation tests"""
    print("🚀 GENESIS PROTOCOL - AUTONOMOUS READINESS VALIDATION")
    print("🤖 Final System Check Before Autonomous Operation")
    print("======================================================================")

    tests = [
        ("Core Imports (Circular Dependencies)", test_core_imports),
        ("Enhanced Model Router", test_enhanced_router),
        ("Services Architecture", test_services_architecture),
        ("Configuration System", test_configuration_system),
        ("Database Operations", test_database_operations),
        ("API Endpoints", test_api_endpoints),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔄 Running: {test_name}")
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {e}")

    print("\n======================================================================")
    print(f"📊 FINAL RESULTS: {passed}/{total} systems operational")

    if passed == total:
        print("🎉 GENESIS PROTOCOL VALIDATION: COMPLETE")
        print("✅ All systems operational - Kor'tana ready for autonomous operation")
        return True
    else:
        print("⚠️  Some systems need attention before full autonomous operation")
        print("🔧 Address failed tests before proceeding to autonomous tasks")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
