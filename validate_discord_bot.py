#!/usr/bin/env python
"""
Discord Bot Deployment Validator

Validates that all components are ready for Discord bot deployment.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def validate_discord_bot_setup():
    """Comprehensive validation of Discord bot setup."""

    print("\n" + "=" * 70)
    print("🤖 DISCORD BOT DEPLOYMENT VALIDATOR")
    print("=" * 70 + "\n")

    validation_results = {}

    # 1. Check Python Version
    print("1️⃣  Python Version Check")
    print("-" * 70)
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    version_ok = sys.version_info >= (3, 10)
    print(f"  {'✅' if version_ok else '❌'} Python {python_version}")
    if not version_ok:
        print("  ⚠️  Recommended: Python 3.10+")
    validation_results["Python Version"] = version_ok

    # 2. Check Required Packages
    print("\n2️⃣  Required Packages")
    print("-" * 70)
    required_packages = {
        "discord": "discord.py",
        "dotenv": "python-dotenv",
        "openai": "openai",
    }

    packages_ok = True
    for import_name, pip_name in required_packages.items():
        try:
            __import__(import_name)
            version = ""
            if import_name == "discord":
                import discord

                version = f" (v{discord.__version__})"
            print(f"  ✅ {pip_name}{version}")
        except ImportError:
            print(f"  ❌ {pip_name} - Install with: pip install {pip_name}")
            packages_ok = False

    validation_results["Required Packages"] = packages_ok

    # 3. Check Discord Bot Module
    print("\n3️⃣  Discord Bot Modules")
    print("-" * 70)
    try:
        from src.discord_bot import bot, chat_engine

        print("  ✅ src/discord_bot.py found and importable")
        print(f"     - Bot instance: {bot.__class__.__name__}")
        print(f"     - Chat engine: {'Active' if chat_engine else 'Echo mode'}")
        bot_module_ok = True
    except ImportError as e:
        print(f"  ❌ Failed to import discord_bot: {e}")
        bot_module_ok = False
    except Exception as e:
        print(f"  ⚠️  Warning importing discord_bot: {e}")
        bot_module_ok = True  # Not critical

    validation_results["Discord Bot Module"] = bot_module_ok

    # 4. Check Kor'tana Brain Module
    print("\n4️⃣  Kor'tana Brain Module")
    print("-" * 70)
    try:
        from kortana.brain import ChatEngine

        print("  ✅ ChatEngine imported from kortana.brain")
        print(f"     - Class: {ChatEngine.__name__}")
        brain_ok = True
    except ImportError:
        print("  ⚠️  ChatEngine not available (echo mode will be used)")
        brain_ok = True  # Not critical
    except Exception as e:
        print(f"  ⚠️  Warning loading ChatEngine: {e}")
        brain_ok = True

    validation_results["Kor'tana Brain"] = brain_ok

    # 5. Check Environment Configuration
    print("\n5️⃣  Environment Configuration")
    print("-" * 70)
    from dotenv import load_dotenv

    load_dotenv(override=True)

    token = os.getenv("DISCORD_BOT_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")

    env_ok = True
    if token:
        masked = f"{token[:10]}...{token[-10:]}" if len(token) > 20 else "***"
        print(f"  ✅ DISCORD_BOT_TOKEN configured: {masked}")
    else:
        print("  ❌ DISCORD_BOT_TOKEN not found in .env")
        env_ok = False

    if openai_key:
        masked = (
            f"{openai_key[:8]}...{openai_key[-8:]}" if len(openai_key) > 20 else "***"
        )
        print(f"  ✅ OPENAI_API_KEY configured: {masked}")
    else:
        print("  ⚠️  OPENAI_API_KEY not found (echo mode for responses)")

    validation_results["Environment Config"] = env_ok

    # 6. Check Deployment Scripts
    print("\n6️⃣  Deployment Scripts")
    print("-" * 70)
    scripts = {
        "deploy_discord_bot.py": "Deployment script",
        "deploy_discord_bot.bat": "Windows batch file",
        "start_discord_bot.py": "Startup script",
    }

    scripts_ok = True
    for script_name, description in scripts.items():
        script_path = Path(script_name)
        if script_path.exists():
            print(f"  ✅ {script_name} - {description}")
        else:
            print(f"  ❌ {script_name} - MISSING ({description})")
            scripts_ok = False

    validation_results["Deployment Scripts"] = scripts_ok

    # 7. Check Documentation
    print("\n7️⃣  Documentation")
    print("-" * 70)
    docs = {
        "DISCORD_BOT_DEPLOYMENT.md": "Deployment guide",
        ".env.example": "Configuration template",
    }

    docs_ok = True
    for doc_name, description in docs.items():
        doc_path = Path(doc_name)
        if doc_path.exists():
            print(f"  ✅ {doc_name} - {description}")
        else:
            print(f"  ❌ {doc_name} - MISSING ({description})")
            docs_ok = False

    validation_results["Documentation"] = docs_ok

    # 8. Check .env File
    print("\n8️⃣  .env File Status")
    print("-" * 70)
    env_file = Path(".env")
    if env_file.exists():
        print("  ✅ .env file exists")
        with open(".env") as f:
            lines = f.readlines()
        print(f"     - Size: {len(lines)} lines")
    else:
        print("  ⚠️  .env file not found (will be created on first run)")

    # Summary
    print("\n" + "=" * 70)
    print("📊 VALIDATION SUMMARY")
    print("=" * 70 + "\n")

    for check_name, result in validation_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {check_name}")

    print()
    all_passed = all(validation_results.values())
    total_checks = len(validation_results)
    passed_checks = sum(1 for r in validation_results.values() if r)

    print(f"  Total: {passed_checks}/{total_checks} checks passed")
    print()

    if all_passed:
        print("✅ READY TO DEPLOY")
        print("\nTo start the bot, run:")
        print("  python deploy_discord_bot.py")
        print("  OR")
        print("  python start_discord_bot.py")
    elif env_ok:
        print("⚠️  SOME CHECKS FAILED but can proceed with caution")
        print("\nTo fix issues:")
        print("  - Install missing packages: pip install discord.py")
        print("  - Check .env file configuration")
        print("  - Review DISCORD_BOT_DEPLOYMENT.md for details")
    else:
        print("❌ CANNOT DEPLOY - Critical issues found")
        print("\nRequired to deploy:")
        print("  1. DISCORD_BOT_TOKEN in .env file")
        print("  2. discord.py package installed")
        print("  3. Python 3.10+")

    print("\n" + "=" * 70 + "\n")

    return all_passed


if __name__ == "__main__":
    success = validate_discord_bot_setup()
    sys.exit(0 if success else 1)
