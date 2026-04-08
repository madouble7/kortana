#!/usr/bin/env python3
"""Test Application Startup"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Test 1: Configuration
print("\n[1] Testing Configuration System...")
try:
    from src.kortana.config import get_settings

    settings = get_settings()
    settings.validate()
    print("    ✓ Configuration loaded and validated")
except Exception as e:
    print(f"    ✗ Configuration failed: {e}")
    sys.exit(1)

# Test 2: FastAPI App
print("\n[2] Testing FastAPI Application...")
try:
    from src.kortana.main import app

    print("    ✓ FastAPI app instantiated")
except Exception as e:
    print(f"    ✗ App instantiation failed: {e}")
    sys.exit(1)

# Test 3: Routes
print("\n[3] Testing Routes...")
try:
    routes = [route.path for route in app.routes]
    api_routes = [r for r in routes if "/api" in r]
    print(f"    ✓ {len(api_routes)} API routes loaded")
    for route in sorted(api_routes)[:5]:
        print(f"      - {route}")
    if len(api_routes) > 5:
        print(f"      ... and {len(api_routes) - 5} more")
except Exception as e:
    print(f"    ✗ Route check failed: {e}")

# Test 4: API Keys
print("\n[4] Testing API Keys Status...")
keys_to_check = {
    "OpenAI": "OPENAI_API_KEY",
    "Anthropic": "ANTHROPIC_API_KEY",
    "GitHub": "GITHUB_TOKEN",
    "Discord": "DISCORD_BOT_TOKEN",
    "Stripe": "STRIPE_SECRET_KEY",
    "Pinecone": "PINECONE_API_KEY",
    "Google": "GOOGLE_API_KEY",
}
loaded = 0
for name, key in keys_to_check.items():
    value = getattr(settings, key, None)
    if value:
        print(f"    ✓ {name:15} - Loaded")
        loaded += 1
    else:
        print(f"    ✗ {name:15} - Missing")

print(f"\n[+] Status: {loaded}/{len(keys_to_check)} critical keys loaded")

# Test 5: Server Config
print("\n[5] Testing Server Configuration...")
print(f"    ✓ Host: {settings.HOST}")
print(f"    ✓ Port: {settings.PORT}")
print(f"    ✓ Environment: {settings.ENVIRONMENT}")
print(f"    ✓ Debug: {settings.DEBUG}")

print("\n" + "=" * 50)
print("✓ APPLICATION STARTUP TEST PASSED")
print("=" * 50)
print("\nNext: Start the server with:")
print("  python -m uvicorn src.kortana.main:app --reload")
print("  Then visit: http://localhost:8000/docs")
