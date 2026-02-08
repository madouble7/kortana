#!/usr/bin/env python
"""
Kor'tana Discord Bot Deployment Script

This script prepares and deploys the Discord bot:
- Validates dependencies
- Sets up environment variables
- Tests connectivity
- Starts the bot
"""

import os
import sys
import subprocess
from pathlib import Path

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"🤖 {text}")
    print("=" * 70)


def print_section(text):
    """Print formatted section."""
    print(f"\n📌 {text}")
    print("-" * 70)


def check_dependencies():
    """Check if required packages are installed."""
    print_section("Checking Dependencies")

    required_packages = {
        "discord": "discord.py",
        "dotenv": "python-dotenv",
        "openai": "openai",
        "pydantic": "pydantic",
        "yaml": "pyyaml",
    }

    missing_packages = []

    for import_name, pip_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"  ✅ {pip_name}")
        except ImportError:
            print(f"  ❌ {pip_name} (MISSING)")
            missing_packages.append(pip_name)

    if missing_packages:
        print(f"\n⚠️  Missing {len(missing_packages)} package(s)")
        print("\nTo install missing packages, run:")
        print(f"  pip install {' '.join(missing_packages)}")
        return False

    print("\n✅ All dependencies installed")
    return True


def check_environment():
    """Check environment variable setup."""
    print_section("Checking Environment Variables")

    from dotenv import load_dotenv

    load_dotenv(override=True)

    required_vars = {
        "DISCORD_BOT_TOKEN": "Discord bot token",
        "OPENAI_API_KEY": "OpenAI API key (optional for echo mode)",
    }

    missing_vars = []
    env_status = {}

    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if value:
            # Mask the token for display
            masked = f"{value[:10]}...{value[-10:]}" if len(value) > 20 else "***"
            print(f"  ✅ {var_name}: {masked}")
            env_status[var_name] = True
        else:
            print(f"  ❌ {var_name}: NOT FOUND ({description})")
            if var_name == "DISCORD_BOT_TOKEN":
                missing_vars.append(var_name)
            env_status[var_name] = False

    if missing_vars:
        print(f"\n❌ Configuration incomplete - bot requires: {', '.join(missing_vars)}")
        print("\nTo set up environment variables:")
        print("  1. Copy .env.example to .env (if it exists)")
        print("  2. Edit .env and add your tokens:")
        print('     DISCORD_BOT_TOKEN=your_token_here')
        print('     OPENAI_API_KEY=your_key_here (optional)')
        return False

    print("\n✅ Environment configured")
    return True


def validate_bot_modules():
    """Validate bot modules can be imported."""
    print_section("Validating Bot Modules")

    try:
        from src.discord_bot import bot, chat_engine
        print("  ✅ Discord bot imported")
        print(f"  ✅ Chat engine: {'Kor\'tana Brain' if chat_engine else 'Echo Mode'}")
        return True
    except ImportError as e:
        print(f"  ❌ Failed to import bot modules: {e}")
        return False


def test_discord_token():
    """Test Discord token validity."""
    print_section("Testing Discord Token")

    import discord

    token = os.getenv("DISCORD_BOT_TOKEN")

    if not token:
        print("  ⚠️  No token to test (will fail at startup)")
        return False

    try:
        # Just validate the token format (doesn't test connection yet)
        if len(token) > 50 and "." in token:
            print("  ✅ Token format valid")
            return True
        else:
            print("  ❌ Token format invalid")
            return False
    except Exception as e:
        print(f"  ❌ Error validating token: {e}")
        return False


def install_discord_py():
    """Install discord.py if missing."""
    print_section("Installing Discord.py")

    try:
        import discord

        print("  ✅ discord.py already installed")
        return True
    except ImportError:
        print("  Installing discord.py...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "discord.py"], text=True
            )
            print("  ✅ discord.py installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to install: {e}")
            return False


def setup_env_file():
    """Create .env file if it doesn't exist."""
    print_section("Setting Up .env File")

    env_file = ".env"
    env_example = """.env.example"""

    if os.path.exists(env_file):
        print(f"  ✅ {env_file} already exists")
        return True

    if os.path.exists(env_example):
        print(f"  Creating {env_file} from {env_example}...")
        try:
            with open(env_example, "r") as src:
                content = src.read()
            with open(env_file, "w") as dst:
                dst.write(content)
            print(f"  ✅ {env_file} created")
            print("\n  ⚠️  Please edit .env and add your tokens:")
            print("     DISCORD_BOT_TOKEN=your_token_here")
            print("     OPENAI_API_KEY=your_key_here")
            return False  # Need user to edit
        except Exception as e:
            print(f"  ❌ Failed to create {env_file}: {e}")
            return False
    else:
        print(f"  Creating new {env_file}...")
        env_content = """# Kor'tana Discord Bot Configuration

# Discord Bot Token
# Get this from Discord Developer Portal (https://discord.com/developers/applications)
DISCORD_BOT_TOKEN=

# OpenAI API Key (optional - for enhanced responses)
# Get this from OpenAI (https://platform.openai.com/api-keys)
OPENAI_API_KEY=

# Kor'tana Settings
KORTANA_MODE=default
LOG_LEVEL=INFO
"""
        try:
            with open(env_file, "w") as f:
                f.write(env_content)
            print(f"  ✅ {env_file} created")
            print("\n  ⚠️  Please edit .env and add your tokens:")
            print("     DISCORD_BOT_TOKEN=your_token_here")
            print("     OPENAI_API_KEY=your_key_here (optional)")
            return False
        except Exception as e:
            print(f"  ❌ Failed to create {env_file}: {e}")
            return False


def start_bot():
    """Start the Discord bot."""
    print_section("Starting Discord Bot")

    try:
        # Import and run the bot
        from src.discord_bot import main

        print("  🚀 Launching bot...")
        main()
    except KeyboardInterrupt:
        print("\n\n  🛑 Bot stopped by user")
    except Exception as e:
        print(f"  ❌ Error starting bot: {e}")
        import traceback

        traceback.print_exc()
        return False


def deployment_checklist():
    """Run full deployment checklist."""
    print_header("KOR'TANA DISCORD BOT DEPLOYMENT")

    print("\nRunning deployment checklist...\n")

    checks = []

    # 1. Check dependencies
    print("1️⃣  " + "=" * 60)
    discord_ok = check_dependencies()
    checks.append(("Dependencies", discord_ok))

    # 2. Install discord.py if needed
    if not check_python_package("discord"):
        print("\n2️⃣  " + "=" * 60)
        discord_py_ok = install_discord_py()
        checks.append(("discord.py Installation", discord_py_ok))
    else:
        checks.append(("discord.py Installation", True))

    # 3. Setup .env file
    print("\n3️⃣  " + "=" * 60)
    env_ok = setup_env_file()
    checks.append((".env Setup", env_ok))

    # 4. Check environment
    print("\n4️⃣  " + "=" * 60)
    env_check_ok = check_environment()
    checks.append(("Environment Variables", env_check_ok))

    # 5. Validate modules
    print("\n5️⃣  " + "=" * 60)
    modules_ok = validate_bot_modules()
    checks.append(("Bot Modules", modules_ok))

    # 6. Test token
    print("\n6️⃣  " + "=" * 60)
    token_ok = test_discord_token()
    checks.append(("Discord Token", token_ok))

    # Summary
    print_header("DEPLOYMENT CHECKLIST")
    print()
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")

    print()
    all_passed = all(result for _, result in checks)

    if all_passed:
        print("✅ All checks passed! Ready to start bot.\n")
        return True
    else:
        print("❌ Some checks failed. Please review above and fix issues.\n")
        return False


def check_python_package(package_name):
    """Check if a Python package is installed."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False


def main():
    """Main deployment flow."""
    try:
        # Run checklist
        if deployment_checklist():
            # Ask to start bot
            print("\nReady to start Kor'tana Discord Bot!")
            print("=" * 70)

            try:
                response = input("\nStart bot now? (y/n): ").lower().strip()
                if response in ("y", "yes"):
                    start_bot()
            except EOFError:
                print("(Running in non-interactive mode)")
        else:
            print("Please fix the issues above before starting the bot.")
            input("\nPress Enter to exit...")

    except KeyboardInterrupt:
        print("\n\nDeployment cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
