#!/usr/bin/env python3
"""
Test script to validate Discord bot enhanced can be imported properly.
This doesn't start the bot, just validates the syntax and imports.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_imports():
    """Test that all imports work correctly."""
    print("=" * 60)
    print("Testing Discord Bot Enhanced Imports")
    print("=" * 60)
    print()
    
    # Test discord.py
    print("1. Testing discord.py import...")
    try:
        import discord
        from discord import app_commands
        from discord.ext import commands
        print(f"   ✅ discord.py version: {discord.__version__}")
    except ImportError as e:
        print(f"   ❌ Failed to import discord.py: {e}")
        print("   Install with: pip install discord.py>=2.3.0")
        return False
    
    # Test Flask
    print("2. Testing Flask import...")
    try:
        import flask
        print(f"   ✅ Flask version: {flask.__version__}")
    except ImportError:
        print("   ❌ Failed to import Flask")
        print("   Install with: pip install Flask>=3.0.0")
        return False
    
    # Test optional dependencies
    print("3. Testing optional dependencies...")
    try:
        import huggingface_hub
        print(f"   ✅ huggingface_hub version: {huggingface_hub.__version__}")
    except ImportError:
        print("   ⚠️  huggingface_hub not installed (optional)")
    
    # Test dotenv
    print("4. Testing dotenv import...")
    try:
        import dotenv
        print(f"   ✅ python-dotenv installed")
    except ImportError:
        print("   ❌ Failed to import dotenv")
        print("   Install with: pip install python-dotenv")
        return False
    
    # Test Kor'tana brain (optional)
    print("5. Testing Kor'tana brain import...")
    try:
        from kortana.brain import ChatEngine
        print("   ✅ Kor'tana brain available")
    except ImportError as e:
        print(f"   ⚠️  Kor'tana brain not available: {e}")
        print("   This is OK - bot will use fallback modes")
    
    print()
    print("=" * 60)
    print("✅ All required imports successful!")
    print("=" * 60)
    return True

def test_bot_module():
    """Test that the bot module can be imported."""
    print()
    print("=" * 60)
    print("Testing Discord Bot Module Import")
    print("=" * 60)
    print()
    
    try:
        # This will import the module but not run it
        import discord_bot_enhanced
        print("✅ discord_bot_enhanced module imported successfully")
        print(f"   - MAX_RESPONSE_LENGTH: {discord_bot_enhanced.MAX_RESPONSE_LENGTH}")
        print(f"   - HF_TIMEOUT_SECONDS: {discord_bot_enhanced.HF_TIMEOUT_SECONDS}")
        print(f"   - DEFAULT_FLASK_PORT: {discord_bot_enhanced.DEFAULT_FLASK_PORT}")
        return True
    except Exception as e:
        print(f"❌ Failed to import discord_bot_enhanced: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test bot module
    if not test_bot_module():
        success = False
    
    print()
    if success:
        print("🎉 All tests passed! Bot is ready to run.")
        print()
        print("To start the bot:")
        print("  1. Configure DISCORD_BOT_TOKEN in .env")
        print("  2. Run: python scripts/launchers/launch_discord_bot.py")
        print()
        print("For more info, see docs/DISCORD_BOT_SETUP.md")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
