#!/usr/bin/env python3
"""
Complete VS Code Extension Test for Project Kor'tana
Tests all configured extensions with actual API calls to verify functionality.
"""

import os
import sys
import json
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class ExtensionTester:
    """Tests VS Code extensions for Kor'tana development."""

    def __init__(self):
        self.workspace_root = Path("c:/kortana")
        self.test_results = []

    def test_openai_connection(self) -> Tuple[bool, str]:
        """Test OpenAI API connection."""
        try:
            import openai

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return False, "OPENAI_API_KEY not found in environment"

            client = openai.OpenAI(api_key=api_key)

            # Test with a minimal request
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Use cheaper model for testing
                messages=[{"role": "user", "content": "Hello, this is a connection test."}],
                max_tokens=10
            )

            return True, f"OpenAI connection successful. Model: {response.model}"

        except ImportError:
            return False, "OpenAI package not installed (pip install openai)"
        except Exception as e:
            return False, f"OpenAI connection failed: {str(e)}"

    def test_google_connection(self) -> Tuple[bool, str]:
        """Test Google Gemini API connection."""
        try:
            import google.generativeai as genai

            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                return False, "GOOGLE_API_KEY not found in environment"

            genai.configure(api_key=api_key)

            # Test with a minimal request
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content("Hello, this is a connection test.")

            return True, "Google Gemini connection successful"

        except ImportError:
            return False, "Google AI package not installed (pip install google-generativeai)"
        except Exception as e:
            return False, f"Google Gemini connection failed: {str(e)}"

    def test_continue_config(self) -> Tuple[bool, str]:
        """Test Continue AI configuration."""
        try:
            config_file = self.workspace_root / ".continue" / "config.json"

            if not config_file.exists():
                return False, "Continue config file not found"

            with open(config_file, 'r') as f:
                config = json.load(f)

            # Check if models are configured
            if "models" not in config:
                return False, "No models configured in Continue"

            models = config["models"]
            model_count = len(models)

            # Check for environment variable usage
            env_var_usage = any("${" in str(model) for model in models)

            if env_var_usage:
                return True, f"Continue configured with {model_count} models using environment variables"
            else:
                return False, "Continue models not configured to use environment variables"

        except Exception as e:
            return False, f"Continue config test failed: {str(e)}"

    def test_python_environment(self) -> Tuple[bool, str]:
        """Test Python environment setup."""
        try:
            python_path = self.workspace_root / "venv311" / "Scripts" / "python.exe"

            if not python_path.exists():
                return False, f"Python virtual environment not found at {python_path}"

            # Test PYTHONPATH
            pythonpath = os.getenv("PYTHONPATH", "")
            expected_paths = ["src", "kortana.core", "kortana.team", "kortana.network"]

            missing_paths = [p for p in expected_paths if p not in pythonpath]
            if missing_paths:
                return False, f"PYTHONPATH missing: {', '.join(missing_paths)}"

            return True, f"Python environment configured correctly"

        except Exception as e:
            return False, f"Python environment test failed: {str(e)}"

    def test_vscode_tasks(self) -> Tuple[bool, str]:
        """Test VS Code tasks configuration."""
        try:
            tasks_file = self.workspace_root / ".vscode" / "tasks.json"

            if not tasks_file.exists():
                return False, "VS Code tasks.json not found"

            with open(tasks_file, 'r') as f:
                content = f.read()
                # Remove comments for parsing
                lines = [line for line in content.split('\n') if not line.strip().startswith('//')]
                clean_content = '\n'.join(lines)
                tasks_config = json.loads(clean_content)

            if "tasks" not in tasks_config:
                return False, "No tasks found in tasks.json"

            tasks = tasks_config["tasks"]
            task_count = len(tasks)

            # Check for key tasks
            task_labels = [task.get("label", "") for task in tasks]
            required_tasks = ["Autonomous Agent Development", "Validate Environment"]

            missing_tasks = [t for t in required_tasks if t not in task_labels]
            if missing_tasks:
                return False, f"Missing required tasks: {', '.join(missing_tasks)}"

            return True, f"VS Code tasks configured correctly ({task_count} tasks)"

        except Exception as e:
            return False, f"VS Code tasks test failed: {str(e)}"

    def run_all_tests(self) -> str:
        """Run all extension and configuration tests."""

        tests = [
            ("🔑 OpenAI API Connection", self.test_openai_connection),
            ("🔑 Google Gemini API Connection", self.test_google_connection),
            ("🔧 Continue AI Configuration", self.test_continue_config),
            ("🐍 Python Environment", self.test_python_environment),
            ("⚙️  VS Code Tasks", self.test_vscode_tasks)
        ]

        results = []

        print("🧪 Running Project Kor'tana Extension Tests...")
        print("=" * 60)

        for test_name, test_func in tests:
            print(f"\n{test_name}...")

            try:
                success, message = test_func()

                if success:
                    status = "✅ PASS"
                    results.append(("PASS", test_name, message))
                else:
                    status = "❌ FAIL"
                    results.append(("FAIL", test_name, message))

                print(f"   {status}: {message}")

            except Exception as e:
                status = "💥 ERROR"
                error_msg = f"Test execution error: {str(e)}"
                results.append(("ERROR", test_name, error_msg))
                print(f"   {status}: {error_msg}")

        # Generate summary report
        passes = len([r for r in results if r[0] == "PASS"])
        fails = len([r for r in results if r[0] == "FAIL"])
        errors = len([r for r in results if r[0] == "ERROR"])
        total = len(results)

        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passes}")
        print(f"❌ Failed: {fails}")
        print(f"💥 Errors: {errors}")

        if fails == 0 and errors == 0:
            print("\n🎉 ALL TESTS PASSED!")
            print("   Project Kor'tana is ready for autonomous development!")
        else:
            print(f"\n⚠️  {fails + errors} issues found that need attention.")

            print("\n🔧 RECOMMENDED ACTIONS:")
            for status, test_name, message in results:
                if status in ["FAIL", "ERROR"]:
                    print(f"   - {test_name}: {message}")

        print("\n🌟 Sacred Circuit Development Environment")
        print("   Ready for autonomous AI agent collaboration!")

        return f"Tests completed: {passes}/{total} passed"


def main():
    """Main test execution."""

    # Set up environment
    os.chdir("c:/kortana")

    # Load environment variables if .env exists
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

    tester = ExtensionTester()
    result = tester.run_all_tests()

    return 0


if __name__ == "__main__":
    sys.exit(main())
