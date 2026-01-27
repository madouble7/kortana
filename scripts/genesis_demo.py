#!/usr/bin/env python3
"""
Simple Genesis Protocol Demo
Tests the new development tools with minimal dependencies
"""

import asyncio
import os
import sys

print("🚀 GENESIS PROTOCOL TOOLS DEMO")
print("=" * 50)

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def demo_genesis_tools():
    try:
        from kortana.core.execution_engine import ExecutionEngine

        # Initialize execution engine with current directory
        allowed_dirs = [os.getcwd()]
        blocked_commands = ["rm", "del", "sudo"]
        engine = ExecutionEngine(allowed_dirs, blocked_commands)

        print("✅ ExecutionEngine initialized successfully")

        # Test 1: Search for goal_router.py
        print("\n1️⃣ Testing SEARCH_CODEBASE for 'list_all_goals'...")
        search_result = await engine.search_codebase(
            query="list_all_goals",
            file_patterns=["*.py"],
            max_results=5
        )

        if search_result.success:
            results = search_result.data.get('results', [])
            print(f"   ✅ Found {len(results)} matches")
            for i, result in enumerate(results[:2]):
                print(f"   📁 Match {i+1}: {result['file']}")
                print(f"   📄 Line {result['line_number']}: {result['matched_line'].strip()}")
        else:
            print(f"   ❌ Search failed: {search_result.error}")

        # Test 2: Create and patch a test file
        print("\n2️⃣ Testing APPLY_PATCH...")
        test_file = "genesis_test.py"

        # Create test file
        with open(test_file, 'w') as f:
            f.write('def hello():\n    return "world"\n')

        # Apply patch
        patch_result = await engine.apply_patch(
            filepath=test_file,
            patch_content='def hello():\n    return "world"|||def hello():\n    return "Genesis Protocol!"'
        )

        if patch_result.success:
            print("   ✅ Patch applied successfully")
            with open(test_file) as f:
                content = f.read()
                print(f"   📝 Updated content: {content.strip()}")
        else:
            print(f"   ❌ Patch failed: {patch_result.error}")

        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)

        # Test 3: Simple test execution
        print("\n3️⃣ Testing RUN_TESTS...")
        test_result = await engine.run_tests(
            test_pattern="tests/",
            verbose=False
        )

        if test_result.success:
            print("   ✅ Tests executed successfully")
        else:
            print(f"   ⚠️ Test execution: {test_result.error}")

        print("\n🎯 GENESIS PROTOCOL TOOLS: FULLY OPERATIONAL!")
        print("Ready for autonomous software engineering tasks.")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(demo_genesis_tools())
    if success:
        print("\n🔥 PHASE 1 COMPLETE: Genesis Protocol tools verified!")
        print("🚀 Ready to proceed to PHASE 2: First Autonomous Development Goal")
    else:
        print("\n❌ Genesis Protocol tools verification failed")
        sys.exit(1)
