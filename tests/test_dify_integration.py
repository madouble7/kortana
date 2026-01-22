#!/usr/bin/env python3
"""
Minimal test for Dify integration without full backend dependencies.
Tests the adapter interface and router structure.
"""

import sys
import ast
import os
from pathlib import Path

# Get the repository root dynamically
REPO_ROOT = Path(__file__).parent.parent.absolute()

def test_file_syntax(filepath):
    """Test if a Python file has valid syntax."""
    try:
        with open(filepath, 'r') as f:
            code = f.read()
        ast.parse(code)
        return True, "✓ Syntax valid"
    except SyntaxError as e:
        return False, f"✗ Syntax error: {e}"

def test_file_structure(filepath, expected_classes=None, expected_functions=None):
    """Test if a Python file contains expected classes and functions."""
    try:
        with open(filepath, 'r') as f:
            code = f.read()
        tree = ast.parse(code)
        
        # Find classes
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        
        # Find functions
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        
        results = []
        
        if expected_classes:
            for cls in expected_classes:
                if cls in classes:
                    results.append(f"✓ Class '{cls}' found")
                else:
                    results.append(f"✗ Class '{cls}' not found")
        
        if expected_functions:
            for func in expected_functions:
                if func in functions:
                    results.append(f"✓ Function '{func}' found")
                else:
                    results.append(f"✗ Function '{func}' not found")
        
        return True, "\n".join(results)
    except Exception as e:
        return False, f"✗ Error: {e}"

def main():
    print("=" * 60)
    print("Dify Integration - Minimal Test Suite")
    print("=" * 60)
    
    base_path = REPO_ROOT
    
    tests = [
        {
            "name": "Dify Adapter Syntax",
            "file": f"{base_path}/src/kortana/adapters/dify_adapter.py",
            "test": "syntax"
        },
        {
            "name": "Dify Router Syntax",
            "file": f"{base_path}/src/kortana/adapters/dify_router.py",
            "test": "syntax"
        },
        {
            "name": "Main App Syntax",
            "file": f"{base_path}/src/kortana/main.py",
            "test": "syntax"
        },
        {
            "name": "Dify Adapter Structure",
            "file": f"{base_path}/src/kortana/adapters/dify_adapter.py",
            "test": "structure",
            "expected_classes": ["DifyAdapter"],
            "expected_functions": [
                "handle_chat_request",
                "handle_workflow_request", 
                "handle_completion_request",
                "get_adapter_info"
            ]
        },
        {
            "name": "Dify Router Structure",
            "file": f"{base_path}/src/kortana/adapters/dify_router.py",
            "test": "structure",
            "expected_classes": [
                "DifyChatRequest",
                "DifyWorkflowRequest",
                "DifyCompletionRequest",
                "DifyChatResponse"
            ],
            "expected_functions": [
                "handle_dify_chat",
                "handle_dify_workflow",
                "handle_dify_completion",
                "get_dify_adapter_info",
                "dify_adapter_health"
            ]
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        print(f"\n{test['name']}:")
        print("-" * 60)
        
        if not os.path.exists(test['file']):
            print(f"✗ File not found: {test['file']}")
            failed += 1
            continue
        
        if test['test'] == 'syntax':
            success, message = test_file_syntax(test['file'])
        elif test['test'] == 'structure':
            success, message = test_file_structure(
                test['file'],
                test.get('expected_classes'),
                test.get('expected_functions')
            )
        
        print(message)
        if success:
            passed += 1
        else:
            failed += 1
    
    # Check documentation
    print("\n\nDocumentation:")
    print("-" * 60)
    docs_to_check = [
        f"{base_path}/docs/DIFY_INTEGRATION.md",
        f"{base_path}/config/dify_config_example.md"
    ]
    
    for doc in docs_to_check:
        if os.path.exists(doc):
            size = os.path.getsize(doc)
            print(f"✓ {os.path.basename(doc)} exists ({size} bytes)")
            passed += 1
        else:
            print(f"✗ {os.path.basename(doc)} not found")
            failed += 1
    
    # Check environment config
    print("\n\nConfiguration:")
    print("-" * 60)
    env_file = f"{base_path}/.env.example"
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            content = f.read()
        if 'DIFY_API_KEY' in content:
            print("✓ .env.example contains DIFY configuration")
            passed += 1
        else:
            print("✗ .env.example missing DIFY configuration")
            failed += 1
    
    # Check README
    readme_file = f"{base_path}/README.md"
    if os.path.exists(readme_file):
        with open(readme_file, 'r') as f:
            content = f.read()
        if 'Dify' in content or 'dify' in content:
            print("✓ README.md mentions Dify integration")
            passed += 1
        else:
            print("✗ README.md doesn't mention Dify")
            failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {passed + failed}")
    
    if failed == 0:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
