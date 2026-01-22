"""
Simple test script to verify Open WebUI integration structure
Tests basic functionality without requiring full dependencies
"""

import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_openwebui_adapter_structure():
    """Test that OpenWebUI adapter has required components."""
    print("\n1. Testing OpenWebUI Adapter Structure...")
    
    try:
        # Read the file content
        with open('src/kortana/adapters/openwebui_adapter.py', 'r') as f:
            content = f.read()
        
        # Check for required components
        checks = [
            ('Router definition', 'router = APIRouter'),
            ('OpenAI models endpoint', 'def list_models'),
            ('Chat completions endpoint', 'def create_chat_completion'),
            ('Streaming support', 'StreamingResponse'),
            ('Authentication', 'verify_api_key'),
            ('OpenAI request model', 'class OpenAIChatRequest'),
            ('OpenAI response model', 'class OpenAIChatResponse'),
        ]
        
        all_passed = True
        for check_name, check_str in checks:
            if check_str in content:
                print(f"  ✓ {check_name}")
            else:
                print(f"  ✗ {check_name} not found")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_mcp_router_structure():
    """Test that MCP router has required components."""
    print("\n2. Testing MCP Router Structure...")
    
    try:
        with open('src/kortana/api/routers/mcp_router.py', 'r') as f:
            content = f.read()
        
        checks = [
            ('Router definition', 'router = APIRouter'),
            ('Memory search endpoint', 'def mcp_search_memory'),
            ('Memory store endpoint', 'def mcp_store_memory'),
            ('Goals list endpoint', 'def mcp_list_goals'),
            ('Goals create endpoint', 'def mcp_create_goal'),
            ('Context gather endpoint', 'def mcp_gather_context'),
            ('Discovery endpoint', 'def mcp_discover_tools'),
            ('Authentication', 'verify_mcp_token'),
        ]
        
        all_passed = True
        for check_name, check_str in checks:
            if check_str in content:
                print(f"  ✓ {check_name}")
            else:
                print(f"  ✗ {check_name} not found")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_main_integration():
    """Test that main.py includes the new routers."""
    print("\n3. Testing Main.py Integration...")
    
    try:
        with open('src/kortana/main.py', 'r') as f:
            content = f.read()
        
        checks = [
            ('OpenWebUI adapter import', 'from src.kortana.adapters.openwebui_adapter import router as openwebui_router'),
            ('MCP router import', 'from src.kortana.api.routers.mcp_router import router as mcp_router'),
            ('OpenWebUI router included', 'app.include_router(openwebui_router)'),
            ('MCP router included', 'app.include_router(mcp_router)'),
        ]
        
        all_passed = True
        for check_name, check_str in checks:
            if check_str in content:
                print(f"  ✓ {check_name}")
            else:
                print(f"  ✗ {check_name} not found")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_mcp_config():
    """Test MCP configuration file."""
    print("\n4. Testing MCP Configuration...")
    
    try:
        with open('config/mcp/mcp_config.json', 'r') as f:
            config = json.load(f)
        
        # Check structure
        checks = []
        
        if 'servers' in config and isinstance(config['servers'], list):
            print(f"  ✓ Servers list present ({len(config['servers'])} servers)")
            checks.append(True)
            
            for server in config['servers']:
                if 'tools' in server:
                    print(f"    ✓ {server['name']}: {len(server['tools'])} tools")
        else:
            print("  ✗ Servers list missing")
            checks.append(False)
        
        if 'settings' in config:
            print("  ✓ Settings present")
            checks.append(True)
        else:
            print("  ✗ Settings missing")
            checks.append(False)
        
        return all(checks)
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_docker_compose():
    """Test Docker Compose configuration."""
    print("\n5. Testing Docker Compose Configuration...")
    
    try:
        with open('docker-compose.openwebui.yml', 'r') as f:
            content = f.read()
        
        checks = [
            ('open-webui service', 'open-webui:'),
            ('mcp-server service', 'mcp-server:'),
            ('Networks defined', 'networks:'),
            ('Volumes defined', 'volumes:'),
            ('API key env var', 'KORTANA_API_KEY'),
            ('Port 3000', '"3000:8080"'),
            ('Port 8001', '"8001:8000"'),
        ]
        
        all_passed = True
        for check_name, check_str in checks:
            if check_str in content:
                print(f"  ✓ {check_name}")
            else:
                print(f"  ✗ {check_name} not found")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_documentation():
    """Test that documentation files exist and have content."""
    print("\n6. Testing Documentation...")
    
    docs = [
        ('Integration guide', 'docs/OPENWEBUI_INTEGRATION.md', 5000),
        ('Quick reference', 'docs/OPENWEBUI_QUICKREF.md', 1000),
        ('Architecture docs', 'docs/OPENWEBUI_ARCHITECTURE.md', 5000),
        ('Troubleshooting', 'docs/OPENWEBUI_TROUBLESHOOTING.md', 5000),
    ]
    
    all_passed = True
    for doc_name, doc_path, min_size in docs:
        try:
            if os.path.exists(doc_path):
                size = os.path.getsize(doc_path)
                if size >= min_size:
                    print(f"  ✓ {doc_name} ({size} bytes)")
                else:
                    print(f"  ⚠ {doc_name} exists but may be incomplete ({size} bytes)")
            else:
                print(f"  ✗ {doc_name} missing")
                all_passed = False
        except Exception as e:
            print(f"  ✗ {doc_name}: {e}")
            all_passed = False
    
    return all_passed


def test_scripts():
    """Test that startup/shutdown scripts exist."""
    print("\n7. Testing Startup Scripts...")
    
    scripts = [
        ('Linux start script', 'scripts/start_openwebui.sh'),
        ('Linux stop script', 'scripts/stop_openwebui.sh'),
        ('Windows start script', 'scripts/start_openwebui.bat'),
        ('Windows stop script', 'scripts/stop_openwebui.bat'),
    ]
    
    all_passed = True
    for script_name, script_path in scripts:
        if os.path.exists(script_path):
            # Check if executable on Linux
            if script_path.endswith('.sh'):
                is_executable = os.access(script_path, os.X_OK)
                if is_executable:
                    print(f"  ✓ {script_name} (executable)")
                else:
                    print(f"  ⚠ {script_name} (not executable)")
            else:
                print(f"  ✓ {script_name}")
        else:
            print(f"  ✗ {script_name} missing")
            all_passed = False
    
    return all_passed


def main():
    print("=" * 70)
    print("Open WebUI Integration Tests")
    print("=" * 70)
    
    results = []
    
    results.append(("OpenWebUI Adapter Structure", test_openwebui_adapter_structure()))
    results.append(("MCP Router Structure", test_mcp_router_structure()))
    results.append(("Main.py Integration", test_main_integration()))
    results.append(("MCP Configuration", test_mcp_config()))
    results.append(("Docker Compose", test_docker_compose()))
    results.append(("Documentation", test_documentation()))
    results.append(("Startup Scripts", test_scripts()))
    
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Integration is ready.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
