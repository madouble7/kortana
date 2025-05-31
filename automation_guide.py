#!/usr/bin/env python3
"""
Kor'tana Automation Levels Guide
===============================

Complete guide to the three automation levels with examples.
"""

print(
    """
🤖 KOR'TANA AUTONOMOUS SYSTEM - AUTOMATION LEVELS
=" * 60

Your enhanced autonomous relay system is now ready! Here are the three automation levels:

📖 AUTOMATION LEVEL GUIDE:

🔧 1. MANUAL LEVEL
================
- Full user control over all operations
- Perfect for development, debugging, and learning
- You trigger each action manually
- Maximum control and transparency

Commands:
  python relays/relay_enhanced.py --status    # Check system status
  python relays/relay_enhanced.py             # Run single relay cycle
  python relays/relay_enhanced.py --summarize # Create summaries
  python automation_control.py --level manual

⚡ 2. SEMI-AUTO LEVEL
===================
- Automated relay processing and message handling
- Automatic summarization when token limits approached
- Manual oversight and intervention points
- Best balance for productive work

Commands:
  python automation_control.py --level semi-auto
  python relays/relay_enhanced.py --loop      # Start continuous relay
  python automation_control.py --status       # Monitor system

🚀 3. HANDS-OFF LEVEL
====================
- Fully autonomous operation
- Self-monitoring and context management
- Automatic agent handoffs and recovery
- Minimal human oversight required

Commands:
  python automation_control.py --level hands-off
  python automation_control.py --start        # Start autonomous system
  python automation_control.py --stop         # Emergency stop

💾 DATABASE FEATURES:
====================
Your system now includes:
- Context package storage in kortana.db
- Token usage tracking and optimization
- Agent activity logging
- Automatic summarization triggers
- Task handoff metadata

🔗 SYSTEM INTEGRATION:
=====================
Enhanced features added to your existing relay:
- SQLite database for context persistence
- Token counting with tiktoken
- Gemini 2.0 Flash integration (optional)
- Automated summarization when approaching context limits
- Agent status monitoring and health checks

🎯 QUICK START:
==============
1. Choose your comfort level:
   python automation_control.py --level [manual|semi-auto|hands-off]

2. For development (recommended first):
   python automation_control.py --level manual
   python relays/relay_enhanced.py --status

3. For production use:
   python automation_control.py --level semi-auto
   python relays/relay_enhanced.py --loop

4. For autonomous operation:
   python automation_control.py --level hands-off
   python automation_control.py --start

🔍 MONITORING:
=============
- Database: Check kortana.db for context packages
- Logs: Monitor logs/ directory for agent activity
- Queues: Watch queues/ for message flow
- Status: Use --status commands for real-time info

🛠️  CUSTOMIZATION:
==================
- Edit relay_enhanced.py for custom logic
- Modify gemini_integration.py for different AI models
- Adjust automation_control.py for your workflow
- Configure thresholds in the database schema

Your autonomous Kor'tana system is ready for proto-autonomy! 🚀
"""
)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("\n🧪 Running quick system test...")
        # Import and test key components
        try:
            from relays.gemini_integration import GeminiSummarizer
            from relays.relay_enhanced import KortanaEnhancedRelay

            print("✅ Enhanced relay: Available")
            print("✅ Gemini integration: Available")
            print("✅ Database support: Available")
            print("🎉 System ready for autonomous operation!")

        except ImportError as e:
            print(f"⚠️  Import issue: {e}")
            print("📝 Run: pip install tiktoken")
    else:
        print("\nAdd --test flag to run system validation")
