#!/usr/bin/env python3
"""
Direct test of FastAPI app import and basic functionality
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_app_import():
    """Test importing and basic functionality of the FastAPI app."""
    print("=== FastAPI App Import Test ===")

    try:
        from kortana.main import app
        print("✅ FastAPI app imported successfully")

        # Check app attributes
        print(f"   App title: {app.title}")
        print(f"   App description: {app.description}")
        print(f"   App version: {app.version}")

        # Check routes
        routes = [route.path for route in app.routes]
        print(f"   Available routes: {routes}")

        if "/health" in routes and "/test-db" in routes:
            print("✅ All expected routes are available")
            return True
        else:
            print("❌ Missing expected routes")
            return False

    except Exception as e:
        print(f"❌ Error importing FastAPI app: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_app_import()
    print("\\n=== Test Complete ===")
    if success:
        print("🎉 FastAPI app structure is correct!")
    else:
        print("❌ FastAPI app has issues.")
