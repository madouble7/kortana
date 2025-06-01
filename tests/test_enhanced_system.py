#!/usr/bin/env python3
"""
Enhanced System Test
===================

Tests the enhanced autonomous relay system with context management.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "relays"))


def test_database():
    """Test database initialization"""
    print("🧪 Testing database initialization...")

    import init_db

    init_db.init_kortana_db()

    db_path = project_root / "kortana.db"
    if db_path.exists():
        print("✅ Database created successfully")
        return True
    else:
        print("❌ Database creation failed")
        return False


def test_gemini_integration():
    """Test Gemini integration"""
    print("\n🧪 Testing Gemini integration...")

    try:
        from relays.gemini_integration import GeminiSummarizer

        summarizer = GeminiSummarizer()

        test_text = "This is a test message for summarization. " * 20
        summary = summarizer.summarize(test_text, max_tokens=100)

        print(f"✅ Summarization works: {len(summary)} chars")
        return True
    except Exception as e:
        print(f"❌ Gemini integration error: {e}")
        return False


def test_enhanced_relay():
    """Test enhanced relay system"""
    print("\n🧪 Testing enhanced relay system...")

    try:
        from relays.relay_enhanced import KortanaEnhancedRelay

        relay = KortanaEnhancedRelay()

        print("✅ Enhanced relay initialized")

        # Test single cycle
        stats = relay.relay_cycle()
        print(f"✅ Relay cycle completed: {stats}")

        return True
    except Exception as e:
        print(f"❌ Enhanced relay error: {e}")
        return False


def main():
    """Run all tests"""
    print("🎯 ENHANCED KOR'TANA SYSTEM TEST")
    print("=" * 40)

    tests = [test_database, test_gemini_integration, test_enhanced_relay]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")

    print("\n" + "=" * 40)
    print(f"📊 TEST RESULTS: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed! System ready for autonomous operation.")
        print("\nNext Steps:")
        print("1. Set your automation level:")
        print("   python automation_control.py --level manual|semi-auto|hands-off")
        print("2. Start the system:")
        print("   python relays/relay_enhanced.py --loop")
    else:
        print("⚠️  Some tests failed. Check the errors above.")


if __name__ == "__main__":
    main()
