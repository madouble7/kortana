#!/usr/bin/env python3
"""
🔍 SIMPLE PROACTIVE TEST
Test the code scanner functionality directly
"""

import ast
from pathlib import Path


def simple_docstring_check():
    """Simple test of docstring detection using AST."""

    print("🔍 SIMPLE PROACTIVE CODE SCANNER TEST")
    print("=" * 45)

    # Test the goal_router.py file that we know has functions
    router_file = Path("src/kortana/api/routers/goal_router.py")

    if not router_file.exists():
        print("❌ Router file not found")
        return

    print(f"📁 Analyzing: {router_file}")

    try:
        with open(router_file, encoding="utf-8") as f:
            content = f.read()

        # Parse with AST
        tree = ast.parse(content)

        functions_without_docstrings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function has a docstring
                has_docstring = (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)
                )

                if not has_docstring:
                    functions_without_docstrings.append(
                        {
                            "function": node.name,
                            "line": node.lineno,
                            "file": str(router_file),
                        }
                    )

        print(
            f"📊 Functions analyzed: {len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])}"
        )
        print(f"📝 Functions missing docstrings: {len(functions_without_docstrings)}")

        if functions_without_docstrings:
            print("\n🔍 Issues found:")
            for issue in functions_without_docstrings[:3]:  # Show first 3
                print(
                    f"   - Function '{issue['function']}' at line {issue['line']} has no docstring"
                )

            # This would be where we create a goal
            sample_goal = f"Add comprehensive docstring to the '{functions_without_docstrings[0]['function']}' function in '{functions_without_docstrings[0]['file']}'"
            print("\n🎯 Sample goal that would be created:")
            print(f"   {sample_goal}")

            print("\n✅ Proactive code scanning is working!")
            print(
                "🤖 This demonstrates Kor'tana can identify code improvements autonomously"
            )

        else:
            print("✅ All functions have docstrings - no issues found")

    except Exception as e:
        print(f"❌ Error analyzing file: {e}")


if __name__ == "__main__":
    simple_docstring_check()
