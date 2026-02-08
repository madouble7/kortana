#!/usr/bin/env python
"""
Simple Discord Bot Setup and Dependency Installer
Fixes Python environment and installs discord.py
"""

import os
import subprocess
import sys

print("\n" + "=" * 80)
print("🤖 KOR'TANA DISCORD BOT - DEPENDENCY INSTALLER")
print("=" * 80 + "\n")

# Step 1: Check Python
print("1️⃣  Checking Python installation...")
print(f"   Python: {sys.version}")
print(f"   Executable: {sys.executable}\n")

# Step 2: Install discord.py
print("2️⃣  Installing discord.py...")
try:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "discord.py"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("   ✅ discord.py installed successfully")
    else:
        print("   ⚠️  Installation had warnings (continuing anyway)")
        if result.stderr:
            print(f"   Error: {result.stderr[:200]}")
except Exception as e:
    print(f"   ⚠️  Error during installation: {e}")

# Step 3: Install other dependencies
print("\n3️⃣  Installing other dependencies...")
packages = ["python-dotenv", "openai", "pydantic", "pyyaml"]
for package in packages:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", package],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"   ✅ {package}")
        else:
            print(f"   ⚠️  {package} (skipping)")
    except Exception as e:
        print(f"   ⚠️  {package}: {e}")

# Step 4: Verify discord.py is importable
print("\n4️⃣  Verifying installation...")
try:
    import discord

    print("   ✅ discord.py is importable")
except ImportError as e:
    print(f"   ❌ discord.py still not importable: {e}")
    print("   This may require a Python restart.")
    input("\n   Press Enter to exit...")
    sys.exit(1)

# Step 5: Start bot
print("\n" + "=" * 80)
print("✅ Dependencies installed!")
print("=" * 80)
print("\nStarting Kor'tana Discord Bot...\n")

try:
    os.system("python start_discord_bot.py")
except KeyboardInterrupt:
    print("\n\nBot stopped by user")
except Exception as e:
    print(f"\nError starting bot: {e}")
    input("Press Enter to exit...")
