"""Simple validation of chat modules."""

import sys

sys.path.insert(0, r"c:\kortana\src")

print("=" * 70)
print("VALIDATING KOR'TANA CHAT MODULES")
print("=" * 70)
print()

modules_to_check = [
    ("dev_chat_simple", "Dev Chat Interface"),
    ("memory_manager", "Memory Manager"),
    ("kortana.core.brain", "Core Brain/ChatEngine"),
    ("kortana.config", "Configuration Module"),
]

print("Module Import Checks:")
print("-" * 70)

for module_name, display_name in modules_to_check:
    try:
        __import__(module_name)
        print(f"✅ {display_name:<30} ({module_name})")
    except ImportError as e:
        print(f"❌ {display_name:<30} - ImportError: {str(e)[:40]}")
    except Exception as e:
        print(f"❌ {display_name:<30} - {type(e).__name__}: {str(e)[:40]}")

print()
print("=" * 70)
print()

# Try to initialize components
print("Component Initialization Checks:")
print("-" * 70)

try:
    from dev_chat_simple import KortanaDevChat

    chat = KortanaDevChat()
    print(f"✅ KortanaDevChat initialized (Session: {chat.engine.session_id[:8]}...)")
except Exception as e:
    print(f"⚠️  KortanaDevChat - {e}")

try:
    from memory_manager import MemoryManager

    mm = MemoryManager("data/validation_test.jsonl")
    print("✅ MemoryManager initialized")
except Exception as e:
    print(f"⚠️  MemoryManager - {e}")

try:
    from kortana.config import load_config
    from kortana.core.brain import ChatEngine

    config = load_config()
    engine = ChatEngine(config)
    print(f"✅ ChatEngine initialized (Session: {engine.session_id[:8]}...)")
except Exception as e:
    print(f"⚠️  ChatEngine - {e}")

print()
print("=" * 70)
print("VALIDATION COMPLETE")
print("=" * 70)
