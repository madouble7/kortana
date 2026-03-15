"""
Validation script for Open WebUI integration
Tests the structure and logic without requiring full environment setup
"""

import json
import os
import ast
import sys


def validate_file_exists(filepath, description):
    """Validate that a file exists."""
    if os.path.exists(filepath):
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description} missing: {filepath}")
        return False


def validate_python_syntax(filepath):
    """Validate Python file syntax."""
    try:
        with open(filepath, 'r') as f:
            ast.parse(f.read())
        print(f"✓ Valid Python syntax: {filepath}")
        return True
    except SyntaxError as e:
        print(f"✗ Syntax error in {filepath}: {e}")
        return False


def validate_json_syntax(filepath):
    """Validate JSON file syntax."""
    try:
        with open(filepath, 'r') as f:
            json.load(f)
        print(f"✓ Valid JSON syntax: {filepath}")
        return True
    except json.JSONDecodeError as e:
        print(f"✗ JSON error in {filepath}: {e}")
        return False


def validate_docker_compose(filepath):
    """Basic validation of Docker Compose file."""
    if not os.path.exists(filepath):
        print(f"✗ Docker Compose file missing: {filepath}")
        return False
    
    with open(filepath, 'r') as f:
        content = f.read()
        required_items = [
            'open-webui',
            'mcp-server',
            'kortana-network',
            'KORTANA_API_KEY'
        ]
        for item in required_items:
            if item in content:
                print(f"  ✓ Contains: {item}")
            else:
                print(f"  ✗ Missing: {item}")
                return False
    
    print(f"✓ Docker Compose validated: {filepath}")
    return True


def main():
    print("=" * 60)
    print("Open WebUI Integration Validation")
    print("=" * 60)
    print()
    
    all_valid = True
    
    # Check core files
    print("1. Checking core integration files...")
    files_to_check = [
        ("docker-compose.openwebui.yml", "Docker Compose file"),
        ("src/kortana/adapters/openwebui_adapter.py", "OpenWebUI adapter"),
        ("src/kortana/api/routers/mcp_router.py", "MCP router"),
        ("config/mcp/mcp_config.json", "MCP configuration"),
        ("docs/OPENWEBUI_INTEGRATION.md", "Integration documentation"),
        ("docs/OPENWEBUI_QUICKREF.md", "Quick reference"),
        ("scripts/start_openwebui.sh", "Linux start script"),
        ("scripts/stop_openwebui.sh", "Linux stop script"),
        ("scripts/start_openwebui.bat", "Windows start script"),
        ("scripts/stop_openwebui.bat", "Windows stop script"),
    ]
    
    for filepath, description in files_to_check:
        if not validate_file_exists(filepath, description):
            all_valid = False
    
    print()
    
    # Validate Python syntax
    print("2. Validating Python syntax...")
    python_files = [
        "src/kortana/adapters/openwebui_adapter.py",
        "src/kortana/api/routers/mcp_router.py",
        "src/kortana/main.py",
    ]
    
    for filepath in python_files:
        if os.path.exists(filepath):
            if not validate_python_syntax(filepath):
                all_valid = False
    
    print()
    
    # Validate JSON syntax
    print("3. Validating JSON configuration...")
    json_files = [
        "config/mcp/mcp_config.json",
    ]
    
    for filepath in json_files:
        if os.path.exists(filepath):
            if not validate_json_syntax(filepath):
                all_valid = False
    
    print()
    
    # Validate Docker Compose
    print("4. Validating Docker Compose...")
    if not validate_docker_compose("docker-compose.openwebui.yml"):
        all_valid = False
    
    print()
    
    # Check for required sections in main.py
    print("5. Checking main.py integration...")
    with open("src/kortana/main.py", 'r') as f:
        main_content = f.read()
        checks = [
            ("openwebui_adapter import", "from src.kortana.adapters.openwebui_adapter import"),
            ("mcp_router import", "from src.kortana.api.routers.mcp_router import"),
            ("openwebui router included", "app.include_router(openwebui_router)"),
            ("mcp router included", "app.include_router(mcp_router)"),
        ]
        
        for check_name, check_str in checks:
            if check_str in main_content:
                print(f"  ✓ {check_name}")
            else:
                print(f"  ✗ Missing: {check_name}")
                all_valid = False
    
    print()
    
    # Check environment template
    print("6. Checking environment configuration...")
    with open(".env.template", 'r') as f:
        env_content = f.read()
        if "KORTANA_API_KEY" in env_content:
            print("  ✓ KORTANA_API_KEY in template")
        else:
            print("  ✗ KORTANA_API_KEY missing from template")
            all_valid = False
        
        if "WEBUI_SECRET_KEY" in env_content:
            print("  ✓ WEBUI_SECRET_KEY in template")
        else:
            print("  ✗ WEBUI_SECRET_KEY missing from template")
            all_valid = False
    
    print()
    
    # Summary
    print("=" * 60)
    if all_valid:
        print("✅ All validation checks passed!")
        print()
        print("Next steps:")
        print("1. Set up your .env file with API keys")
        print("2. Start the backend: python -m uvicorn src.kortana.main:app --port 8000")
        print("3. Start Open WebUI: docker compose -f docker-compose.openwebui.yml up -d")
        print("4. Access Open WebUI at http://localhost:3000")
        print()
        print("See docs/OPENWEBUI_INTEGRATION.md for detailed instructions.")
        return 0
    else:
        print("❌ Some validation checks failed!")
        print("Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
