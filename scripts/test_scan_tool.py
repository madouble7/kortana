#!/usr/bin/env python3
"""
Test script for the new SCAN_CODEBASE_FOR_ISSUES tool
Part of Batch 10: The Proactive Engineer Initiative
"""

import asyncio
import logging

from src.kortana.core.execution_engine import ExecutionEngine

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_scan_tool():
    """Test the new code scanning functionality."""

    # Create execution engine
    execution_engine = ExecutionEngine(
        allowed_dirs=[
            r"c:\project-kortana",
            r"c:\project-kortana\src",
            r"c:\project-kortana\docs",
        ],
        blocked_commands=["rm", "del", "format"],
    )

    logger.info("🔍 Testing SCAN_CODEBASE_FOR_ISSUES tool...")

    # Test scanning a small directory for missing docstrings
    test_directory = r"c:\project-kortana\src\kortana\api"

    result = await execution_engine.scan_codebase_for_issues(
        directory=test_directory, rules=["missing_docstrings"], file_patterns=["*.py"]
    )

    if result.success:
        issues = result.data
        logger.info("✅ Scan completed successfully!")
        logger.info(f"📊 Found {len(issues)} issues:")

        for issue in issues[:5]:  # Show first 5 issues
            logger.info(
                f"  - {issue['file']}:{issue['line']} - {issue['function_name']} missing docstring"
            )

        if len(issues) > 5:
            logger.info(f"  ... and {len(issues) - 5} more issues")

    else:
        logger.error(f"❌ Scan failed: {result.error}")

    logger.info(f"⏱️  Scan took {result.duration:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(test_scan_tool())
