#!/usr/bin/env python
"""
Find which Python has discord.py and use it to run the bot
"""

import subprocess
import sys
import os

print("\n" + "=" * 80)
print("🔍 DIAGNOSING PYTHON ENVIRONMENT FOR DISCORD BOT")
print("=" * 80 + "\n")

# Step 1: Check current Python
print(f"Current Python: {sys.executable}")
print(f"Version: {sys.version}\n")

# Step 2: Try to import discord in current Python
print("Step 1: Checking current Python...")
try:
    import discord
    from discord import ext
    from discord.ext import commands
    print("✅ discord.py WITH discord.ext found in current Python!")
    print("   Using this Python to run bot...\n")
    
    # Run the bot with this Python
    print("=" * 80)
    print("STARTING BOT")
    print("=" * 80 + "\n")
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
        from dotenv import load_dotenv
        load_dotenv()
        
        from src.discord_bot import main as bot_main
        bot_main()
    except Exception as e:
        print(f"Error running bot: {e}")
        import traceback
        traceback.print_exc()
    
except ImportError as e:
    print(f"❌ discord.ext NOT found in current Python: {e}\n")
    
    # Try to find Python with discord.py
    print("Step 2: Searching for Python with discord.py...\n")
    
    # Common Python locations
    possible_pythons = [
        r"C:\Python311\python.exe",
        r"C:\Python312\python.exe", 
        r"C:\Python313\python.exe",
        sys.executable,
    ]
    
    found_python = None
    
    for python_path in possible_pythons:
        if not os.path.exists(python_path):
            continue
            
        try:
            result = subprocess.run(
                [python_path, "-c", "import discord.ext.commands; print('OK')"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✅ Found discord.py in: {python_path}")
                found_python = python_path
                break
            else:
                print(f"❌ {python_path}: discord.ext not available")
        except Exception as e:
            print(f"❌ {python_path}: {type(e).__name__}")
    
    if found_python:
        print(f"\nUsing: {found_python}\n")
        print("=" * 80)
        print("STARTING BOT")
        print("=" * 80 + "\n")
        
        # Run bot with found Python
        os.system(f'"{found_python}" start_discord_bot.py')
    else:
        print("\n❌ Could not find Python with discord.py")
        print("Trying to reinstall discord.py...\n")
        
        # Try pip install again
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--force-reinstall", "discord.py"],
            text=True
        )
        
        print("\nTrying bot again...")
        os.system(f'"{sys.executable}" start_discord_bot.py')
