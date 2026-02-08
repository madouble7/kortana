#!/usr/bin/env python
"""
Kor'tana Discord Bot - Setup Assistant

This script helps you complete the bot setup by prompting for just the bot token.
All other configuration is pre-filled with your Application ID.

Run this to complete setup in 2 minutes!
"""

import os
import sys
from pathlib import Path

# Your Discord App Details (from Developer Portal)
APP_ID = "1421497726201233418"
PUBLIC_KEY = "5bc1c281b27b59f238f6128aeb675a29da8e8dfc8cc3de095c595ae5a8d88f0e"


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"🤖 {text}")
    print("=" * 70)


def print_step(num, text):
    """Print numbered step."""
    print(f"\n{num}️⃣  {text}")
    print("-" * 70)


def get_bot_token():
    """Get bot token from user."""
    print_step(1, "Discord Bot Token")

    print("""
YOU'RE ALREADY ON THE RIGHT PAGE! You should see:
  ✅ Applications > kor'tana > Bot (selected)
  ✅ Token section visible
  ✅ "Reset Token" button

WHAT TO DO RIGHT NOW:
  1. In Discord Developer Portal (where you are):
     → Scroll down to the "TOKEN" section
     → Click the copy icon next to your token
     
  2. Come back here and paste the token below

INTENTS TO ENABLE (while you're there):
  ✅ Message Content Intent (needed for message reading)
  
CHECK THESE SETTINGS:
  ✅ Public Bot = ON (so bot can be added)
  ✅ Message Content Intent = ON (required!)

Note: Keep this token secret! Never commit to git.
    """)

    while True:
        token = input("🔑 Enter your bot token: ").strip()

        if not token:
            print("❌ Token cannot be empty")
            continue

        if len(token) < 50:
            print("❌ Token too short (should be ~70+ characters)")
            continue

        if "." not in token:
            print("❌ Invalid token format (should contain dots)")
            continue

        # Confirm token
        masked = f"{token[:20]}...{token[-10:]}"
        confirm = input(f"\n✓ Confirm token: {masked} (y/n): ").strip().lower()

        if confirm == "y":
            return token
        else:
            print("Let's try again...\n")


def create_env_file(token):
    """Create .env file with token."""
    print_step(2, "Creating .env File")

    env_content = f"""# Kor'tana Discord Bot Configuration
# Generated: {os.popen('date').read().strip() if os.name != 'nt' else 'Feb 8, 2026'}

# ===== REQUIRED =====
DISCORD_BOT_TOKEN={token}
DISCORD_APP_ID={APP_ID}
DISCORD_PUBLIC_KEY={PUBLIC_KEY}

# ===== OPTIONAL =====
# OpenAI API Key (for enhanced AI responses)
OPENAI_API_KEY=

# Bot Settings
KORTANA_MODE=default
LOG_LEVEL=INFO
MAX_MESSAGE_LENGTH=1900

# LLM Configuration
DEFAULT_LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.7
"""

    try:
        # Check if .env exists
        if Path(".env").exists():
            response = (
                input("\n⚠️  .env file already exists. Overwrite? (y/n): ")
                .strip()
                .lower()
            )
            if response != "y":
                print("Skipped .env creation (using existing file)")
                return True

        # Create .env
        with open(".env", "w") as f:
            f.write(env_content)

        print("✅ .env file created successfully")
        print(f"   Location: {Path('.env').absolute()}")

        # Show what was saved
        print("\n📝 Configuration saved:")
        print(f"   • DISCORD_BOT_TOKEN: {token[:20]}...{token[-5:]}")
        print(f"   • DISCORD_APP_ID: {APP_ID}")
        print(f"   • Mode: default")

        return True

    except Exception as e:
        print(f"❌ Error creating .env: {e}")
        return False


def run_validation():
    """Run validation checks."""
    print_step(3, "Validating Setup")

    print("Checking setup...\n")

    # Python version
    python_ok = sys.version_info >= (3, 10)
    print(f"  {'✅' if python_ok else '❌'} Python {sys.version_info.major}.{sys.version_info.minor}")

    # discord.py
    discord_ok = False
    try:
        import discord

        print(f"  ✅ discord.py installed")
        discord_ok = True
    except ImportError:
        print(f"  ❌ discord.py not installed (run: pip install discord.py)")

    # .env file
    env_ok = Path(".env").exists()
    print(f"  {'✅' if env_ok else '❌'} .env file")

    # Token validation
    from dotenv import load_dotenv

    load_dotenv()
    token = os.getenv("DISCORD_BOT_TOKEN")
    token_ok = token and len(token) > 50 and "." in token
    print(f"  {'✅' if token_ok else '❌'} Bot token configured")

    return discord_ok and env_ok and token_ok


def show_next_steps():
    """Show what to do next."""
    print_step(4, "Next Steps")

    print("""
✅ Your bot is configured and ready!

To start the bot:
  1. Install dependencies:
     pip install discord.py python-dotenv openai

  2. Start the bot:
     python start_discord_bot.py

  3. Test in Discord:
     • Bot should appear online
     • Try command: /ping
     • Try command: /kortana hello

For detailed setup:
  → See DISCORD_BOT_DEPLOYMENT.md

For help:
  → Run: python validate_discord_bot.py
    """)


def main():
    """Main setup flow."""
    print_header("KOR'TANA DISCORD BOT - QUICK SETUP")

    print("""
This assistant will help you set up Kor'tana in 2 minutes!

Your Discord App Settings (Pre-filled):
  • Application ID: 1421497726201233418
  • Status: Ready to connect
  
What you need to provide:
  • Bot Token (from https://discord.com/developers/applications)
    """)

    input("\nPress Enter to continue...")

    # Step 1: Get token
    token = get_bot_token()

    # Step 2: Create .env
    if not create_env_file(token):
        print("❌ Setup incomplete - please fix errors above")
        return False

    # Step 3: Validate
    if run_validation():
        print("\n" + "=" * 70)
        print("✅ SETUP COMPLETE")
        print("=" * 70)
    else:
        print("\n⚠️  Some components missing - see above")

    # Step 4: Next steps
    show_next_steps()

    print("=" * 70 + "\n")

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n🛑 Setup cancelled by user")
        sys.exit(1)
