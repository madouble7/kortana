#!/usr/bin/env python
"""
Kor'tana Discord Bot - One-Line Setup Guide

Copy and paste these commands in order. That's it!
"""

import os
import sys
from pathlib import Path

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    🤖 KOR'TANA DISCORD BOT - QUICK START                     ║
║                                                                              ║
║                        Get Your Bot Running in 7 Minutes                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝


📋 STEP-BY-STEP INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ STEP 1: Get Your Bot Token (2 minutes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Open: https://discord.com/developers/applications
2. Click: kor'tana application
3. Click: Bot (left sidebar)
4. Click: Copy (under TOKEN)
5. Keep it copied to clipboard

✓ You now have your bot token


✅ STEP 2: Run Setup Script (1 minute)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Windows:
  setup_discord_bot_quick.bat

Any OS:
  python setup_discord_bot_quick.py

✓ Script will ask you to paste token
✓ Then creates .env file
✓ That's it!


✅ STEP 3: Install Discord Package (1 minute)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  pip install discord.py

✓ Done


✅ STEP 4: Start the Bot (30 seconds)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  python start_discord_bot.py

✓ Bot should now be online in Discord


✅ STEP 5: Test in Discord (2 minutes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Type these in Discord:
  /ping              (should respond with latency)
  /kortana hello     (should respond with a message)

✓ If both work, YOU'RE DONE! 🎉


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 YOUR DISCORD APP (Pre-configured)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Application ID:    1421497726201233418
  Public Key:        5bc1c281b27b59f238f6128aeb675a29da8e8dfc8cc3de095c595ae5a8d88f0e
  Status:            ✅ Ready (pre-configured)
  Installation:      ✅ 1 Server
  Your Next Step:    ⏭️  Get bot token (see Step 1 above)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 WHAT'S ALREADY DONE FOR YOU
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ✅ Discord application created
  ✅ Bot invited to server
  ✅ All deployment scripts ready
  ✅ Configuration templates prepared
  ✅ Validation tools built
  ✅ Documentation complete
  ✅ Your App ID integrated


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ TOTAL TIME REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Get Token:     2 minutes  👉 START HERE
  Setup:         1 minute
  Install:       1 minute
  Start:         30 seconds
  Test:          2 minutes
  ────────────────────────
  TOTAL:         ~7 minutes ✅


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 RIGHT NOW - NEXT 60 SECONDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Open your browser
2. Go to: https://discord.com/developers/applications
3. Click kor'tana app
4. Go to Bot section
5. Copy your token

Then run:
  python setup_discord_bot_quick.py

And paste your token when asked.

That's it! 🎉


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❓ QUICK HELP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ❓ Where's my bot token?
     → Discord portal: Applications → kor'tana → Bot → TOKEN → Copy

  ❓ Token not working?
     → Regenerate it in Bot section

  ❓ Bot doesn't respond?
     → Check Message Content Intent is enabled in Discord portal

  ❓ Import errors?
     → pip install -r requirements.txt

  ❓ Need more help?
     → See: DISCORD_BOT_DEPLOYMENT.md


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 FILES YOU'LL USE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  setup_discord_bot_quick.py    ← Run this with your token
  setup_discord_bot_quick.bat   ← Or this (Windows)
  start_discord_bot.py          ← Then this to start bot
  validate_discord_bot.py       ← If something's wrong


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 STATUS: 🟡 AWAITING YOUR BOT TOKEN

Everything is prepared and waiting for you.
Get your token and run the setup script.

You've got this! 💪

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

# Show file locations
print("\n📍 You are in: {}\n".format(os.getcwd()))

# Check key files exist
key_files = [
    "setup_discord_bot_quick.py",
    "start_discord_bot.py",
    "validate_discord_bot.py",
]

print("✅ Key files ready:")
for f in key_files:
    exists = "✓" if Path(f).exists() else "✗"
    print(f"   {exists} {f}")

print("\n" + "=" * 80)
print("READY TO BEGIN? Open Discord Developer Portal and get your bot token!")
print("→ https://discord.com/developers/applications")
print("=" * 80 + "\n")
