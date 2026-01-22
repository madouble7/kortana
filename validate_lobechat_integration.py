#!/usr/bin/env python3
"""
Simple validation test for LobeChat integration files.
Tests file structure and basic syntax without requiring all dependencies.
"""

import ast
import sys
from pathlib import Path


def validate_python_syntax(file_path: Path) -> bool:
    """Validate Python file syntax."""
    try:
        with open(file_path, 'r') as f:
            code = f.read()
        ast.parse(code)
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in {file_path}: {e}")
        return False


def check_file_exists(file_path: Path) -> bool:
    """Check if file exists."""
    if file_path.exists():
        print(f"✅ {file_path} exists")
        return True
    else:
        print(f"❌ {file_path} not found")
        return False


def check_function_definitions(file_path: Path, expected_funcs: list) -> bool:
    """Check if expected functions are defined in file."""
    try:
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())
        
        defined_funcs = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                defined_funcs.append(node.name)
        
        all_found = True
        for func in expected_funcs:
            if func in defined_funcs:
                print(f"  ✅ Function '{func}' found")
            else:
                print(f"  ❌ Function '{func}' not found")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"  ❌ Error checking functions: {e}")
        return False


def check_class_definitions(file_path: Path, expected_classes: list) -> bool:
    """Check if expected classes are defined in file."""
    try:
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())
        
        defined_classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                defined_classes.append(node.name)
        
        all_found = True
        for cls in expected_classes:
            if cls in defined_classes:
                print(f"  ✅ Class '{cls}' found")
            else:
                print(f"  ❌ Class '{cls}' not found")
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"  ❌ Error checking classes: {e}")
        return False


def main():
    """Run validation tests."""
    print("=" * 70)
    print("LobeChat Integration - File Structure Validation")
    print("=" * 70)
    
    project_root = Path(__file__).parent
    all_passed = True
    
    # Test 1: Check main integration files exist
    print("\n📁 Test 1: Checking file existence...")
    files_to_check = [
        project_root / "src/kortana/adapters/lobechat_openai_adapter.py",
        project_root / "src/kortana/main.py",
        project_root / "docker-compose.yml",
        project_root / "Dockerfile.backend",
        project_root / "docs/LOBECHAT_INTEGRATION_GUIDE.md",
        project_root / "start-lobechat-integration.sh",
        project_root / "start-lobechat-integration.bat",
        project_root / ".env.template",
        project_root / "lobechat-frontend/README.md",
        project_root / "lobechat-frontend/kortana-config.json",
    ]
    
    for file_path in files_to_check:
        if not check_file_exists(file_path):
            all_passed = False
    
    # Test 2: Validate Python syntax
    print("\n🐍 Test 2: Validating Python syntax...")
    python_files = [
        project_root / "src/kortana/adapters/lobechat_openai_adapter.py",
        project_root / "src/kortana/main.py",
    ]
    
    for file_path in python_files:
        if file_path.exists():
            if validate_python_syntax(file_path):
                print(f"✅ {file_path} has valid syntax")
            else:
                all_passed = False
    
    # Test 3: Check lobechat_openai_adapter.py structure
    print("\n🔍 Test 3: Checking lobechat_openai_adapter.py structure...")
    adapter_file = project_root / "src/kortana/adapters/lobechat_openai_adapter.py"
    
    if adapter_file.exists():
        print("  Checking classes...")
        expected_classes = [
            "Message",
            "ChatCompletionRequest",
            "ChatCompletionResponse",
            "ModelListResponse",
        ]
        if not check_class_definitions(adapter_file, expected_classes):
            all_passed = False
        
        print("  Checking functions...")
        expected_functions = [
            "verify_api_key",
            "list_models",
            "create_chat_completion",
        ]
        if not check_function_definitions(adapter_file, expected_functions):
            all_passed = False
    
    # Test 4: Check main.py has routers registered
    print("\n🔍 Test 4: Checking main.py router registration...")
    main_file = project_root / "src/kortana/main.py"
    
    if main_file.exists():
        with open(main_file, 'r') as f:
            content = f.read()
        
        checks = [
            ("lobechat_router import", "from src.kortana.adapters.lobechat_openai_adapter import router as lobechat_router"),
            ("lobechat_router registered", "app.include_router(lobechat_router)"),
            ("CORS localhost:3210", "localhost:3210"),
        ]
        
        for check_name, check_str in checks:
            if check_str in content:
                print(f"  ✅ {check_name} found")
            else:
                print(f"  ❌ {check_name} not found")
                all_passed = False
    
    # Test 5: Check environment template
    print("\n🔍 Test 5: Checking .env.template...")
    env_template = project_root / ".env.template"
    
    if env_template.exists():
        with open(env_template, 'r') as f:
            content = f.read()
        
        required_vars = [
            "KORTANA_API_KEY",
            "OPENAI_API_KEY",
            "LOBECHAT_FRONTEND_URL",
            "LOBECHAT_BACKEND_URL",
        ]
        
        for var in required_vars:
            if var in content:
                print(f"  ✅ {var} defined")
            else:
                print(f"  ❌ {var} not defined")
                all_passed = False
    
    # Test 6: Check docker-compose.yml
    print("\n🔍 Test 6: Checking docker-compose.yml...")
    compose_file = project_root / "docker-compose.yml"
    
    if compose_file.exists():
        with open(compose_file, 'r') as f:
            content = f.read()
        
        required_services = [
            "kortana-backend",
            "lobechat-frontend",
        ]
        
        for service in required_services:
            if service in content:
                print(f"  ✅ Service '{service}' defined")
            else:
                print(f"  ❌ Service '{service}' not defined")
                all_passed = False
    
    # Final result
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ All validation tests passed!")
        print("=" * 70)
        return 0
    else:
        print("❌ Some validation tests failed!")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
