"""
KOR'TANA Quickstart Example
Basic usage of the Kor'tana API
"""

from fastapi.testclient import TestClient
from src.kortana.main import app


def main():
    """Quick demonstration of Kor'tana API"""
    print("🚀 KOR'TANA Quickstart")
    print("=" * 50)

    # Create test client
    client = TestClient(app)

    # 1. Test root endpoint
    print("\n1. Root Endpoint")
    response = client.get("/")
    print(f"   Status: {response.status_code}")
    print(f"   Data: {response.json()}")

    # 2. Health check
    print("\n2. Health Check")
    response = client.get("/api/health")
    print(f"   Status: {response.status_code}")
    print(f"   Status: {response.json()['status']}")

    # 3. API structure
    print("\n3. Available Routes")
    for route in app.routes:
        if hasattr(route, "path"):
            methods = getattr(route, "methods", [])
            if methods:
                print(f"   {list(methods)[0]:7} {route.path}")

    print("\n" + "=" * 50)
    print("✅ Quickstart complete!")
    print("\n📚 Next steps:")
    print("   - Check /docs for API documentation")
    print("   - See examples/02_authentication.py for auth")
    print("   - See examples/03_agents.py for agents")


if __name__ == "__main__":
    main()
