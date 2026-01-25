#!/usr/bin/env python3
"""Test that all API keys load from .env"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.kortana.config import get_settings

settings = get_settings()

print("✓ Backend configuration loaded successfully!\n")

credentials = {
    "OpenAI": settings.OPENAI_API_KEY,
    "Anthropic": settings.ANTHROPIC_API_KEY,
    "Google Gemini": settings.GEMINI_API_KEY,
    "Google API": settings.GOOGLE_API_KEY,
    "GitHub": settings.GITHUB_TOKEN,
    "Discord Bot": settings.DISCORD_BOT_TOKEN,
    "Stripe": settings.STRIPE_SECRET_KEY,
    "Pinecone": settings.PINECONE_API_KEY,
    "AWS": settings.AWS_ACCESS_KEY_ID,
    "Twilio": settings.TWILIO_ACCOUNT_SID,
}

loaded = sum(1 for v in credentials.values() if v)
print(f"Credentials loaded: {loaded}/{len(credentials)}")
print("\nAPI Keys Status:")

for name, value in credentials.items():
    status = "✓ Configured" if value else "✗ Missing"
    print(f"  {status:20} {name}")

print(f"\nDatabase: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
print(f"Environment: {settings.ENVIRONMENT}")
print(f"Debug Mode: {settings.DEBUG}")
