#!/usr/bin/env python3
"""
Launch script for Kor'tana Enhanced Discord Bot

This script checks prerequisites and launches the Discord bot with proper error handling.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

def check_dependencies():
    """Check if required dependencies are installed."""
    missing = []
    
    try:
        import discord
    except ImportError:
        missing.append("discord.py")
    
    try:
        import flask
    except ImportError:
        missing.append("Flask")
    
    try:
        from dotenv import load_dotenv
    except ImportError:
        missing.append("python-dotenv")
    
    if missing:
        print("❌ Missing required dependencies:")
        for dep in missing:
            print(f"   - {dep}")
        print("\nInstall them with:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    # Check optional dependencies
    optional_missing = []
    try:
        import huggingface_hub
    except ImportError:
        optional_missing.append("huggingface_hub")
    
    if optional_missing:
        print("⚠️  Optional dependencies not installed:")
        for dep in optional_missing:
            print(f"   - {dep} (enables Hugging Face fallback)")
        print("\nInstall with:")
        print(f"   pip install {' '.join(optional_missing)}")
        print()
    
    return True

def check_environment():
    """Check if required environment variables are set."""
    from dotenv import load_dotenv
    
    # Load .env file
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
        print(f"✅ Loaded environment from {env_file}")
    else:
        print(f"⚠️  No .env file found at {env_file}")
        print("   You can copy .env.example to .env and configure it")
    
    # Check required variables
    discord_token = os.getenv("DISCORD_BOT_TOKEN")
    if not discord_token:
        print("\n❌ ERROR: DISCORD_BOT_TOKEN not found in environment")
        print("   Please add it to your .env file:")
        print("   DISCORD_BOT_TOKEN=your_token_here")
        return False
    
    # Check optional variables
    hf_key = os.getenv("HUGGINGFACE_API_KEY")
    if not hf_key:
        print("⚠️  HUGGINGFACE_API_KEY not set (Hugging Face features disabled)")
    
    return True

def main():
    """Main launcher function."""
    print("=" * 60)
    print("🤖 Kor'tana Enhanced Discord Bot Launcher")
    print("=" * 60)
    print()
    
    # Check dependencies
    print("📦 Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    print("✅ All required dependencies installed")
    print()
    
    # Check environment
    print("🔑 Checking environment configuration...")
    if not check_environment():
        print("\n⚠️  Please configure your environment variables before running the bot.")
        print("   See docs/DISCORD_BOT_SETUP.md for detailed setup instructions.")
        sys.exit(1)
    print("✅ Environment configured")
    print()
    
    # Check for Kor'tana brain
    print("🧠 Checking Kor'tana brain availability...")
    try:
        from kortana.brain import ChatEngine
        print("✅ Kor'tana brain available")
    except Exception as e:
        print(f"⚠️  Kor'tana brain not available: {e}")
        print("   Bot will use Hugging Face fallback")
    print()
    
    # Launch bot
    print("=" * 60)
    print("🚀 Launching Discord bot...")
    print("=" * 60)
    print()
    
    try:
        # Import and run the bot
        from discord_bot_enhanced import main as bot_main
        bot_main()
    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n\n❌ Bot crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
