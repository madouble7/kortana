#!/usr/bin/env python3
"""
Kor'tana Chat Diagnostics - Check what's working and what's not
"""

import sys
from pathlib import Path


def check_python():
    """Check Python version"""
    version = sys.version
    print(f"✅ Python: {version}")
    return True


def check_modules():
    """Check required modules"""
    modules = {
        "requests": "REST API calls",
        "pyttsx3": "Text-to-speech",
        "speech_recognition": "Voice input",
    }

    results = {}
    for module, purpose in modules.items():
        try:
            __import__(module)
            print(f"✅ {module:20} - {purpose}")
            results[module] = True
        except ImportError:
            print(f"❌ {module:20} - {purpose} [MISSING]")
            results[module] = False

    return results


def check_files():
    """Check if all chat files exist"""
    files = {
        "kor_tana_simple_chat.py": "Simple chat interface",
        "kor_tana_chat.py": "Full chat interface",
        "kor_tana_voice_chat.py": "Voice chat interface",
        "talk_to_kortana.ps1": "Launcher script",
    }

    results = {}
    for filename, purpose in files.items():
        path = Path(filename)
        if path.exists():
            size = path.stat().st_size
            print(f"✅ {filename:30} - {purpose} ({size} bytes)")
            results[filename] = True
        else:
            print(f"❌ {filename:30} - {purpose} [NOT FOUND]")
            results[filename] = False

    return results


def check_server():
    """Check if server is running"""
    try:
        import requests

        response = requests.get("http://localhost:8000/api/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server running on port 8000")
            return True
        else:
            print(f"⚠️  Server responding but status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("⚠️  Server NOT running on port 8000 (needed for Full Chat & Voice Chat)")
        return False
    except Exception as e:
        print(f"⚠️  Server check error: {e}")
        return False


def run_simple_chat_test():
    """Test simple chat"""
    try:
        from kor_tana_simple_chat import SimpleKorTanaChat

        chat = SimpleKorTanaChat()
        response = chat.handle_status()
        if "Current Status:" in response:
            print("✅ Simple Chat works!")
            return True
        else:
            print("❌ Simple Chat test failed")
            return False
    except Exception as e:
        print(f"❌ Simple Chat error: {e}")
        return False


def main():
    """Run all diagnostics"""
    print("\n" + "=" * 70)
    print("🔍 KOR'TANA CHAT DIAGNOSTICS")
    print("=" * 70 + "\n")

    print("📋 CHECKING ENVIRONMENT:")
    print("-" * 70)
    check_python()
    print()

    print("📦 CHECKING MODULES:")
    print("-" * 70)
    modules = check_modules()
    print()

    print("📁 CHECKING FILES:")
    print("-" * 70)
    files = check_files()
    print()

    print("🌐 CHECKING SERVER:")
    print("-" * 70)
    server_ok = check_server()
    print()

    print("🧪 TESTING SIMPLE CHAT:")
    print("-" * 70)
    simple_ok = run_simple_chat_test()
    print()

    print("=" * 70)
    print("📊 SUMMARY:")
    print("=" * 70)

    # Summary
    all_files_ok = all(files.values())
    simple_modules_ok = modules.get("requests", False)
    voice_modules_ok = all(
        [
            modules.get("requests", False),
            modules.get("pyttsx3", False),
            modules.get("speech_recognition", False),
        ]
    )

    print(
        f"""
✅ Can use Simple Chat:     {simple_ok and all_files_ok}
   Requirements: Python, requests module, files

⚠️  Can use Full Chat:      {server_ok and simple_modules_ok and all_files_ok}
   Requirements: Server on port 8000, requests module, files

🎤 Can use Voice Chat:      {server_ok and voice_modules_ok and all_files_ok}
   Requirements: Server on port 8000, ALL modules (requests, pyttsx3, speech_recognition), microphone

📋 NEXT STEPS:
"""
    )

    if not simple_ok or not all_files_ok:
        print("   ❌ SIMPLE CHAT NOT WORKING - Debug needed")
    else:
        print("   ✅ Try: python kor_tana_simple_chat.py")

    if not server_ok:
        print(
            "   ⚠️  Server not running - Start: cd backend && python -m uvicorn src.kortana.main:app --port 8000"
        )
    else:
        print("   ✅ Server is running")

    missing_voice_modules = [
        m for m, ok in modules.items() if not ok and m in ["pyttsx3", "speech_recognition"]
    ]
    if missing_voice_modules:
        print(f"   ⚠️  Missing voice modules: {', '.join(missing_voice_modules)}")
        print(f"      Install: pip install {' '.join(missing_voice_modules)}")

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()

