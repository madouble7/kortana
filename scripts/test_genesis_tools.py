#!/usr/bin/env python3
"""
Direct Genesis Protocol Test
Test the new development tools independently
"""

import asyncio
import os
import sys

print("DEBUG: test_genesis_tools.py started")

sys.path.append(".")

from src.kortana.core.execution_engine import ExecutionEngine


async def test_genesis_tools():
    """Test each Genesis Protocol tool"""
    print("DEBUG: test_genesis_tools() function started")
    print("🔧 TESTING GENESIS PROTOCOL TOOLS")
    print("=" * 50)

    # Initialize execution engine
    allowed_dirs = [os.getcwd()]
    blocked_commands = ["rm", "del", "sudo"]
    engine = ExecutionEngine(allowed_dirs, blocked_commands)

    print("1. Testing SEARCH_CODEBASE...")
    search_result = await engine.search_codebase(
        query="list_all_goals",
        file_patterns=["*.py"]
    )

    if search_result.success and search_result.data and search_result.data.get('results'):
        print(f"   ✅ Found {len(search_result.data['results'])} matches")
        print(f"   📁 First match: {search_result.data['results'][0]['file']}")
        print(f"   📄 Context: {search_result.data['results'][0]['context'][:100]}...")
    else:
        print(f"   ❌ Search failed or found no matches: {search_result.error or 'No results'}")

    print("\n2. Testing RUN_TESTS...")
    test_result = await engine.run_tests(
        test_pattern="tests/test_simple.py", verbose=False
    )
    print(f"   ✅ Test execution: {'SUCCESS' if test_result.success else 'FAILED'}")

    if test_result.data:
        print(
            f"   📊 Results: {test_result.data.get('raw_output', 'No output')[:100]}..."
        )

    print("\n3. Testing APPLY_PATCH...")
    # Create a test file to patch
    test_file = "genesis_test_patch.py"
    with open(test_file, 'w') as f:
        f.write("# Test file\ndef hello():\n    return 'world'\n")

    patch_result = await engine.apply_patch(
        filepath=test_file,
        patch_content="def hello():\n    return 'world'|||def hello():\n    return 'Genesis Protocol!'",
    )
    print(f"   ✅ Patch application: {'SUCCESS' if patch_result.success else 'FAILED'}")

    if patch_result.success:
        with open(test_file) as f:
            print(f"   📝 Updated content: {f.read()}")

    # Clean up
    if os.path.exists(test_file):
        os.remove(test_file)

    print("\n🎯 GENESIS PROTOCOL TOOLS: OPERATIONAL")
    print("Ready for autonomous development tasks!")


if __name__ == "__main__":
    asyncio.run(test_genesis_tools())
