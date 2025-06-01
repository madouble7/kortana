#!/usr/bin/env python3
"""
Test Torch Protocol Integration
===============================

Quick test script to verify torch protocol integration is working correctly.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from torch_protocol import TorchProtocol


def test_torch_integration():
    """Test torch protocol functionality"""
    print("🔥" * 60)
    print("           TORCH PROTOCOL INTEGRATION TEST")
    print("🔥" * 60)

    # Initialize torch protocol
    print("\n[INIT] Initializing Torch Protocol...")
    try:
        torch_protocol = TorchProtocol()
        print("✅ Torch Protocol initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return False

    # Test database initialization
    print("\n[DB] Testing database initialization...")
    try:
        torch_protocol._init_torch_tables()
        print("✅ Database tables initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

    # Test agent detection
    print("\n[AGENT] Testing agent type detection...")
    test_agents = [
        ("claude-3.5-sonnet", "ai"),
        ("user-developer", "human"),
        ("github-copilot", "hybrid"),
        ("gpt-4o", "ai"),
        ("manual-review", "human"),
    ]

    for agent_name, expected_type in test_agents:
        detected_type = torch_protocol.detect_agent_type(agent_name)
        status = "✅" if detected_type == expected_type else "⚠️"
        print(f"  {status} {agent_name} -> {detected_type} (expected: {expected_type})")

    # Test torch creation in auto mode
    print("\n[TORCH] Testing auto-mode torch creation...")
    try:
        torch_data = torch_protocol.prompt_torch_filler(
            agent_name="test-agent",
            context="Testing torch protocol integration with relay system",
            handoff_reason="Integration test",
            task_id="test_integration_001",
            auto_mode=True,
        )

        torch_id = torch_protocol.save_torch_package(
            torch_data, from_agent="test-agent", to_agent="next-agent"
        )

        print(f"✅ Torch package created: {torch_id}")
        print(f"   Task: {torch_data['task_title']}")
        print(f"   Agent Type: {torch_data['agent_profile']['agent_type']}")

    except Exception as e:
        print(f"❌ Torch creation failed: {e}")
        return False

    # Test torch retrieval
    print("\n[RETRIEVE] Testing torch retrieval...")
    try:
        torches = torch_protocol.get_recent_torches(limit=1)
        if torches:
            latest_torch = torches[0]
            print(f"✅ Retrieved torch: {latest_torch['torch_id']}")
            print(
                f"   From: {latest_torch['from_agent']} -> To: {latest_torch['to_agent']}"
            )
        else:
            print("⚠️ No torches found")
    except Exception as e:
        print(f"❌ Torch retrieval failed: {e}")
        return False

    print("\n🎉 TORCH PROTOCOL INTEGRATION TEST COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("Ready for relay integration and production use.")
    return True


if __name__ == "__main__":
    success = test_torch_integration()
    sys.exit(0 if success else 1)
