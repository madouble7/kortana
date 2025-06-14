#!/usr/bin/env python3
"""
Environment Test Script
"""

import os

from dotenv import load_dotenv


def test_environment():
    print("🔍 ENVIRONMENT CONFIGURATION TEST")
    print("=" * 40)

    # Load environment
    print("📁 Loading .env file...")
    load_dotenv()

    # Check KEY_VAULTS_SECRET
    key_secret = os.getenv("KEY_VAULTS_SECRET")
    if key_secret:
        print("✅ KEY_VAULTS_SECRET: Configured")
        print(f"   Length: {len(key_secret)} characters")
    else:
        print("❌ KEY_VAULTS_SECRET: Missing")
        return False

    # Check other essential vars
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print("✅ OPENAI_API_KEY: Configured")
    else:
        print("⚠️  OPENAI_API_KEY: Missing")

    print("\n🎯 Environment is ready for secure server launch!")
    return True


if __name__ == "__main__":
    test_environment()
