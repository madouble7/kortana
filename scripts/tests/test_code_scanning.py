#!/usr/bin/env python3
"""
Test Proactive Code Scanning - Batch 10 Phase 1 Validation

This script tests Kor'tana's code scanning capabilities directly.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from kortana.core.execution_engine import ExecutionEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_code_scanning():
    """Test the code scanning functionality directly."""
    print("🔍 TESTING CODE SCANNING (Batch 10 Phase 1)")
    print("=" * 50)

    try:
        # Create execution engine instance
        allowed_dirs = [str(Path.cwd())]
        blocked_commands = ['rm', 'del', 'format', 'sudo']
        execution_engine = ExecutionEngine(allowed_dirs=allowed_dirs, blocked_commands=blocked_commands)

        print(f"✅ ExecutionEngine initialized with allowed dirs: {allowed_dirs}")

        # Test scanning a specific directory for missing docstrings
        scan_directory = "src/kortana/core"
        rules = ["missing_docstring"]
        file_patterns = ["*.py"]

        print(f"\n🚀 Scanning {scan_directory} for missing docstrings...")

        result = await execution_engine.scan_codebase_for_issues(
            directory_to_scan=scan_directory,
            rules=rules,
            file_patterns=file_patterns
        )

        if result.success:
            issues = result.data
            print(f"✅ Scan completed successfully!")
            print(f"📊 Found {len(issues)} functions missing docstrings")

            # Show first few issues
            if issues:
                print("\n🔍 Sample Issues Found:")
                for issue in issues[:5]:  # Show first 5
                    print(f"  📝 {issue['function_name']} in {issue['relative_path']}:{issue['line_number']}")

                if len(issues) > 5:
                    print(f"  ... and {len(issues) - 5} more")
            else:
                print("✨ No missing docstrings found - code quality is excellent!")

        else:
            print(f"❌ Scan failed: {result.error}")
            return False

        print("\n✅ CODE SCANNING TEST COMPLETED!")
        return True

    except Exception as e:
        print(f"❌ Error in code scanning test: {e}")
        logger.exception("Test failed")
        return False

def main():
    """Main test function."""
    print("🤖 Kor'tana Code Scanning Test")
    print("Testing proactive code quality analysis...")

    try:
        success = asyncio.run(test_code_scanning())

        if success:
            print("\n🎉 SUCCESS: Code scanning is working!")
            print("🔥 Kor'tana can now autonomously analyze code quality!")
        else:
            print("\n💥 FAILED: Code scanning encountered issues")

    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        logger.exception("Main test failed")

if __name__ == "__main__":
    main()
