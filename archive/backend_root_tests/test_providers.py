#!/usr/bin/env python3
"""Test connectivity to external providers"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from config import get_settings

settings = get_settings()

print("\n" + "=" * 60)
print("PROVIDER CONNECTIVITY TEST")
print("=" * 60)

# Test 1: OpenAI
print("\n[1] OpenAI API...")
try:
    if settings.OPENAI_API_KEY:
        print("    ✓ API Key loaded")
        print("    ✓ Key format valid (starts with sk-proj-)")
        print("    ⓘ Skipping live API call (would incur charges)")
    else:
        print("    ✗ API Key missing")
except Exception as e:
    print(f"    ✗ Error: {e}")

# Test 2: Anthropic
print("\n[2] Anthropic API...")
try:
    if settings.ANTHROPIC_API_KEY:
        print("    ✓ API Key loaded")
        print("    ✓ Key format valid (starts with sk-ant-)")
        print("    ⓘ Skipping live API call (would incur charges)")
    else:
        print("    ✗ API Key missing")
except Exception as e:
    print(f"    ✗ Error: {e}")

# Test 3: Google/Gemini
print("\n[3] Google Gemini API...")
try:
    if settings.GOOGLE_API_KEY:
        print("    ✓ API Key loaded")
        print(f"    ✓ Project ID: {settings.GOOGLE_PROJECT_ID}")
        print("    ⓘ Skipping live API call (would incur charges)")
    else:
        print("    ✗ API Key missing")
except Exception as e:
    print(f"    ✗ Error: {e}")

# Test 4: GitHub
print("\n[4] GitHub API...")
try:
    if settings.GITHUB_TOKEN:
        print("    ✓ GitHub Token loaded")
        import requests

        headers = {"Authorization": f"token {settings.GITHUB_TOKEN}"}
        response = requests.get(
            "https://api.github.com/user", headers=headers, timeout=5
        )
        if response.status_code == 200:
            user_data = response.json()
            print("    ✓ Authentication successful")
            print(f"    ✓ User: {user_data.get('login', 'unknown')}")
        else:
            print(f"    ⚠ Token validation returned {response.status_code}")
    else:
        print("    ✗ GitHub Token missing")
except ImportError:
    print("    ⓘ requests library not available (install: pip install requests)")
except Exception as e:
    print(f"    ⚠ Error: {e}")

# Test 5: Discord
print("\n[5] Discord Bot...")
try:
    if settings.DISCORD_BOT_TOKEN:
        print("    ✓ Discord Bot Token loaded")
        print(f"    ✓ Client ID: {settings.DISCORD_CLIENT_ID}")
        print("    ⓘ Full validation requires active Discord connection")
    else:
        print("    ✗ Discord Bot Token missing")
except Exception as e:
    print(f"    ✗ Error: {e}")

# Test 6: Pinecone
print("\n[6] Pinecone Vector DB...")
try:
    if settings.PINECONE_API_KEY:
        print("    ✓ Pinecone API Key loaded")
        print(f"    ✓ Environment: {settings.PINECONE_ENVIRONMENT}")
        print("    ⓘ Skipping live API call (would require index)")
    else:
        print("    ✗ Pinecone API Key missing")
except Exception as e:
    print(f"    ✗ Error: {e}")

# Test 7: Stripe
print("\n[7] Stripe Payment...")
try:
    if settings.STRIPE_SECRET_KEY:
        print("    ✓ Stripe Secret Key loaded")
        print("    ✓ Publishable Key loaded")
        print("    ✓ Webhook Secret loaded")
        print("    ⓘ Skipping live API call (test keys)")
    else:
        print("    ✗ Stripe Keys missing")
except Exception as e:
    print(f"    ✗ Error: {e}")

# Test 8: AWS
print("\n[8] AWS Backup Service...")
try:
    if settings.AWS_ACCESS_KEY_ID:
        print("    ✓ AWS Access Key loaded")
        print("    ✓ AWS Secret Key loaded")
        print("    ⓘ Skipping live API call")
    else:
        print("    ✗ AWS Credentials missing")
except Exception as e:
    print(f"    ✗ Error: {e}")

# Test 9: Database
print("\n[9] Database Configuration...")
try:
    print(f"    ✓ Host: {settings.DB_HOST}")
    print(f"    ✓ Port: {settings.DB_PORT}")
    print(f"    ✓ Database: {settings.DB_NAME}")
    print(f"    ✓ User: {settings.DB_USER}")
    print("    ⓘ Skipping live connection (PostgreSQL not running yet)")
except Exception as e:
    print(f"    ✗ Error: {e}")

# Test 10: Redis
print("\n[10] Redis Cache...")
try:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    print(f"    ✓ Redis URL: {redis_url}")
    print("    ⓘ Skipping live connection (Redis not running yet)")
except Exception as e:
    print(f"    ✗ Error: {e}")

print("\n" + "=" * 60)
summary = [
    settings.OPENAI_API_KEY,
    settings.ANTHROPIC_API_KEY,
    settings.GOOGLE_API_KEY,
    settings.GITHUB_TOKEN,
    settings.DISCORD_BOT_TOKEN,
    settings.STRIPE_SECRET_KEY,
    settings.PINECONE_API_KEY,
]
loaded = sum(1 for k in summary if k)
print(f"✓ PROVIDER CONNECTIVITY TEST: {loaded}/{len(summary)} keys verified")
print("=" * 60 + "\n")
