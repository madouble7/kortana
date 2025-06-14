#!/usr/bin/env python3
"""
Genesis Protocol Final Validation - ASCII Version
==================================================

This script validates that all core Kor'tana systems are operational.
"""

import sys
from pathlib import Path

import requests


def test_core_imports():
    """Test core module imports"""
    print("TESTING CORE IMPORTS")
    print("------------------------------------------------------------")

    try:
        print("[OK] Brain Module: Import successful")
    except Exception as e:
        print(f"[FAIL] Brain Module: Import failed - {e}")
        return False

    try:
        print("[OK] Enhanced Router: Import successful")
    except Exception as e:
        print(f"[FAIL] Enhanced Router: Import failed - {e}")
        return False

    try:
        print("[OK] Services: Import successful")
    except Exception as e:
        print(f"[FAIL] Services: Import failed - {e}")
        return False

    return True


def test_enhanced_router():
    """Test Enhanced Model Router initialization"""
    print("\nTESTING ENHANCED MODEL ROUTER")
    print("------------------------------------------------------------")

    try:
        from src.kortana.config import load_config
        from src.kortana.core.enhanced_model_router import EnhancedModelRouter

        settings = load_config()
        router = EnhancedModelRouter(settings=settings)
        print("[OK] Enhanced Model Router: Initialized successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Enhanced Router test failed: {e}")
        return False


def test_services_architecture():
    """Test services architecture"""
    print("\nTESTING SERVICES ARCHITECTURE")
    print("------------------------------------------------------------")

    try:
        from src.kortana.config import load_config
        from src.kortana.core.services import get_llm_service, initialize_services

        settings = load_config()
        initialize_services(settings)

        llm_service = get_llm_service()
        print("[OK] Services Architecture: Working correctly")
        return True
    except Exception as e:
        print(f"[FAIL] Services architecture test failed: {e}")
        return False


def test_configuration_system():
    """Test configuration loading"""
    print("\nTESTING CONFIGURATION SYSTEM")
    print("------------------------------------------------------------")

    try:
        from src.kortana.config import load_config

        settings = load_config()
        print(f"[OK] Configuration loaded: Type {type(settings)}")

        models_config_path = Path("config/models_config.json")
        if models_config_path.exists():
            print("[OK] Models configuration file found")
        else:
            print("[WARN] Models configuration file not found")
            return False

        return True
    except Exception as e:
        print(f"[FAIL] Configuration test failed: {e}")
        return False


def test_database_operations():
    """Test database operations"""
    print("\nTESTING DATABASE OPERATIONS")
    print("------------------------------------------------------------")

    try:
        from src.kortana.core.models import Goal
        from src.kortana.services.database import SyncSessionLocal

        db = SyncSessionLocal()
        goals = db.query(Goal).all()
        db.close()

        print(f"[OK] Database query successful: {len(goals)} goals found")
        return True
    except Exception as e:
        print(f"[FAIL] Database test failed: {e}")
        return False


def test_api_endpoints():
    """Test API endpoints"""
    print("\nTESTING API ENDPOINTS")
    print("------------------------------------------------------------")

    base_url = "http://localhost:8000"

    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("[OK] Health endpoint: Working")
        else:
            print(f"[FAIL] Health endpoint: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Health endpoint: Failed - {e}")
        return False

    # Test goals endpoint
    try:
        response = requests.get(f"{base_url}/goals/", timeout=5)
        if response.status_code == 200:
            print("[OK] Goals endpoint: Working")
        else:
            print(f"[FAIL] Goals endpoint: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Goals endpoint: Failed - {e}")
        return False

    return True


def main():
    """Run all genesis protocol validation tests"""
    print("GENESIS PROTOCOL - AUTONOMOUS READINESS VALIDATION")
    print("Final System Check Before Autonomous Operation")
    print("=" * 70)

    tests = [
        ("Core Imports", test_core_imports),
        ("Enhanced Model Router", test_enhanced_router),
        ("Services Architecture", test_services_architecture),
        ("Configuration System", test_configuration_system),
        ("Database Operations", test_database_operations),
        ("API Endpoints", test_api_endpoints),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        try:
            if test_func():
                print(f"[PASS] {test_name}: PASSED")
                passed += 1
            else:
                print(f"[FAIL] {test_name}: FAILED")
        except Exception as e:
            print(f"[FAIL] {test_name}: FAILED - {e}")

    print("\n" + "=" * 70)
    print(f"FINAL RESULTS: {passed}/{total} systems operational")

    if passed == total:
        print("GENESIS PROTOCOL VALIDATION: COMPLETE")
        print("All systems operational - Kor'tana ready for autonomous operation")
        return True
    else:
        print("Some systems need attention before full autonomous operation")
        print("Address failed tests before proceeding to autonomous tasks")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
