#!/usr/bin/env python3
"""
Secure Genesis Protocol Launch
Launch Kor'tana with proper environment variables loaded
"""

import os

from dotenv import load_dotenv


def launch_with_environment():
    """Launch the server with environment variables properly loaded"""
    print("🔐 SECURE GENESIS PROTOCOL LAUNCH")
    print("=" * 50)

    # Load environment variables
    load_dotenv()

    # Verify security key is set
    if os.getenv("KEY_VAULTS_SECRET"):
        print("✅ KEY_VAULTS_SECRET: Properly configured")
    else:
        print("❌ KEY_VAULTS_SECRET: Missing - server will not start")
        return False

    # Verify other essential variables
    essential_vars = ["OPENAI_API_KEY", "MEMORY_DB_URL", "APP_NAME"]

    print("\n🔍 Environment Check:")
    for var in essential_vars:
        value = os.getenv(var)
        if value:
            # Show partial value for security
            display_value = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"⚠️  {var}: Not set")

    print("\n🚀 Starting Kor'tana server with secure configuration...")

    try:
        import uvicorn

        from kortana.main import app

        print("✅ FastAPI app imported successfully")
        print("🌐 Server starting at http://127.0.0.1:8000")
        print("🔒 Security key properly configured")
        print("📊 Ready for Genesis Protocol autonomous tasks")
        print("\nPress Ctrl+C to stop the server...")
        print("-" * 50)

        # Start the server
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info", reload=False)

        return True

    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False


if __name__ == "__main__":
    success = launch_with_environment()
    if success:
        print("✅ Server shutdown cleanly")
    else:
        print("❌ Server failed to start - check configuration")
