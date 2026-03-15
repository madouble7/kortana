#!/usr/bin/env python
"""
Simple Discord Bot Startup Script

Usage:
  python start_discord_bot.py
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from dotenv import load_dotenv

# Load environment
load_dotenv(override=True)


def main():
    """Start the Discord bot."""
    print("\n" + "=" * 70)
    print("🤖 STARTING KOR'TANA DISCORD BOT")
    print("=" * 70 + "\n")

    # Check for token
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("❌ ERROR: DISCORD_BOT_TOKEN not found in .env file")
        print("\nTo set up the bot:")
        print("  1. Get a token from Discord Developer Portal:")
        print("     https://discord.com/developers/applications")
        print("  2. Add to .env file:")
        print("     DISCORD_BOT_TOKEN=your_token_here")
        print()
        input("Press Enter to exit...")
        return

    # Check for discord.py
    try:
        import discord

        print("✅ discord.py loaded")
    except ImportError:
        print("❌ discord.py not installed")
        print("Run: pip install discord.py")
        return

    # Import and start bot
    try:
        print("✅ Loading bot modules...")
        from src.discord_bot import main as bot_main

        print("🚀 Starting bot...\n")
        bot_main()

    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
