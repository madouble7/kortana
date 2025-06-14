#!/usr/bin/env python3
"""
Test the proactive scanning logic directly
"""

import ast
import os
from pathlib import Path


def scan_for_missing_docstrings():
    print("🔍 MANUAL PROACTIVE SCAN TEST")
    print("=" * 40)

    scan_paths = [
        "src/kortana/api/routers",
        "src/kortana/api/services",
        "src/kortana/core",
    ]

    findings = []

    for scan_path in scan_paths:
        print(f"📂 Scanning: {scan_path}")
        try:
            for root, dirs, files in os.walk(scan_path):
                for file in files:
                    if file.endswith(".py"):
                        file_path = Path(root) / file
                        try:
                            with open(file_path, encoding="utf-8") as f:
                                content = f.read()

                            tree = ast.parse(content)

                            # Find functions without docstrings
                            for node in ast.walk(tree):
                                if isinstance(
                                    node, (ast.FunctionDef, ast.AsyncFunctionDef)
                                ):
                                    if not ast.get_docstring(node):
                                        findings.append(
                                            {
                                                "file": str(file_path),
                                                "line": node.lineno,
                                                "function_name": node.name,
                                            }
                                        )
                                        print(
                                            f"   📍 Found: {node.name}() in {file_path.name}:{node.lineno}"
                                        )
                        except Exception as e:
                            print(f"   ⚠️ Could not scan {file_path}: {e}")
                            continue
        except Exception as e:
            print(f"   ❌ Could not scan directory {scan_path}: {e}")
            continue

    print("\n🎯 SCAN RESULTS:")
    print(f"   Functions without docstrings: {len(findings)}")

    if findings:
        print("\n📝 SAMPLE FINDINGS (first 5):")
        for i, finding in enumerate(findings[:5], 1):
            print(
                f"   {i}. {finding['function_name']}() in {Path(finding['file']).name}"
            )

    return findings


if __name__ == "__main__":
    scan_for_missing_docstrings()
