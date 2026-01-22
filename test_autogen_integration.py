"""
Test script for AutoGen adapter integration.

This script tests the basic functionality of the AutoGen adapter
to ensure it's properly integrated with Kor'tana.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import httpx


async def test_autogen_health():
    """Test AutoGen health endpoint."""
    print("Testing AutoGen health endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8000/adapters/autogen/health", timeout=10.0
            )
            if response.status_code == 200:
                print("✓ Health check passed")
                print(f"  Response: {response.json()}")
                return True
            else:
                print(f"✗ Health check failed with status {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Health check failed with error: {e}")
        return False


async def test_autogen_status():
    """Test AutoGen status endpoint."""
    print("\nTesting AutoGen status endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8000/adapters/autogen/status", timeout=10.0
            )
            if response.status_code == 200:
                print("✓ Status check passed")
                data = response.json()
                print(f"  Available agents: {data.get('available_agents')}")
                print(f"  Framework: {data.get('framework')}")
                print(f"  Status: {data.get('status')}")
                return True
            else:
                print(f"✗ Status check failed with status {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Status check failed with error: {e}")
        return False


async def test_autogen_chat():
    """Test AutoGen chat endpoint."""
    print("\nTesting AutoGen chat endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            test_message = {
                "messages": [{"role": "user", "content": "Hello, AutoGen!"}],
                "conversation_id": "test-conversation-1",
            }
            response = await client.post(
                "http://localhost:8000/adapters/autogen/chat",
                json=test_message,
                timeout=30.0,
            )
            if response.status_code == 200:
                print("✓ Chat endpoint passed")
                data = response.json()
                print(f"  Status: {data.get('status')}")
                print(f"  Conversation ID: {data.get('conversation_id')}")
                if data.get("agent_responses"):
                    agent_response = data["agent_responses"][0]
                    print(f"  Agent: {agent_response.get('agent')}")
                    print(f"  Response preview: {agent_response.get('content', '')[:100]}...")
                return True
            else:
                print(f"✗ Chat endpoint failed with status {response.status_code}")
                print(f"  Response: {response.text}")
                return False
    except Exception as e:
        print(f"✗ Chat endpoint failed with error: {e}")
        return False


async def test_autogen_collaboration():
    """Test AutoGen multi-agent collaboration endpoint."""
    print("\nTesting AutoGen collaboration endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            test_task = {
                "task": "Analyze the benefits of using AutoGen for multi-agent systems",
                "max_rounds": 3,
            }
            response = await client.post(
                "http://localhost:8000/adapters/autogen/collaborate",
                json=test_task,
                timeout=30.0,
            )
            if response.status_code == 200:
                print("✓ Collaboration endpoint passed")
                data = response.json()
                print(f"  Status: {data.get('status')}")
                print(f"  Agents involved: {data.get('agents_involved')}")
                if data.get("agent_contributions"):
                    print("  Agent contributions:")
                    for contrib in data["agent_contributions"]:
                        print(f"    - {contrib.get('agent')}: {contrib.get('contribution')}")
                return True
            else:
                print(
                    f"✗ Collaboration endpoint failed with status {response.status_code}"
                )
                print(f"  Response: {response.text}")
                return False
    except Exception as e:
        print(f"✗ Collaboration endpoint failed with error: {e}")
        return False


async def test_invalid_request():
    """Test error handling with invalid request."""
    print("\nTesting error handling with invalid request...")
    try:
        async with httpx.AsyncClient() as client:
            # Send empty messages array (invalid)
            invalid_request = {"messages": []}
            response = await client.post(
                "http://localhost:8000/adapters/autogen/chat",
                json=invalid_request,
                timeout=10.0,
            )
            if response.status_code in [400, 422]:
                print("✓ Error handling works correctly")
                print(f"  Received expected error status: {response.status_code}")
                return True
            else:
                print(
                    f"✗ Expected error status, got {response.status_code} instead"
                )
                return False
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


async def run_all_tests():
    """Run all AutoGen integration tests."""
    print("=" * 60)
    print("AutoGen Integration Test Suite")
    print("=" * 60)
    print("\nNOTE: Make sure the Kor'tana server is running at http://localhost:8000")
    print("Start server with: python -m uvicorn src.kortana.main:app --reload")
    print("=" * 60)

    await asyncio.sleep(1)

    results = []

    # Run all tests
    results.append(await test_autogen_health())
    results.append(await test_autogen_status())
    results.append(await test_autogen_chat())
    results.append(await test_autogen_collaboration())
    results.append(await test_invalid_request())

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    if passed == total:
        print("\n✓ All tests passed! AutoGen integration is working correctly.")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
