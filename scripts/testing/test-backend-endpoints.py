#!/usr/bin/env python3
"""
Backend Endpoint Testing Script for Kor'tana
Tests all autonomous API endpoints to ensure they're working correctly
"""

import requests
import json
import sys
import time
from typing import Dict, List, Tuple

class BackendTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30

    def test_endpoint(self, method: str, endpoint: str, data: Dict = None, expected_status: int = 200) -> Tuple[bool, str]:
        """Test a single endpoint and return (success, message)"""
        url = f"{self.base_url}{endpoint}"

        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, headers={'Content-Type': 'application/json'})
            else:
                return False, f"Unsupported method: {method}"

            if response.status_code == expected_status:
                return True, f"✅ {method} {endpoint} - Status {response.status_code}"
            else:
                return False, f"❌ {method} {endpoint} - Expected {expected_status}, got {response.status_code}: {response.text[:200]}"

        except requests.exceptions.RequestException as e:
            return False, f"❌ {method} {endpoint} - Connection failed: {str(e)}"

    def run_all_tests(self) -> Tuple[int, int, List[str]]:
        """Run all backend endpoint tests and return (passed, total, messages)"""
        print("🧪 Starting Kor'tana Backend Endpoint Tests")
        print(f"Target URL: {self.base_url}")
        print("=" * 60)

        tests = [
            # Health check
            ("GET", "/api/health", None, 200),

            # Gemini endpoints
            ("POST", "/api/gemini/generate", {"prompt": "Hello, test message"}, 200),
            ("POST", "/api/gemini/analyze", {"text": "This is a test analysis"}, 200),
            ("GET", "/api/gemini/models", None, 200),

            # GitHub analysis endpoints
            ("POST", "/api/github/analyze", {
                "type": "issue",
                "title": "Test Issue for Analysis",
                "body": "This is a test issue to verify the GitHub analysis endpoint is working correctly.",
                "url": "https://github.com/test/repo/issues/1"
            }, 200),

            # Memory endpoints
            ("POST", "/api/memory/store", {
                "type": "test_memory",
                "content": "Test memory content",
                "metadata": {"source": "test"},
                "tags": ["test", "automation"]
            }, 200),
            ("GET", "/api/memory/retrieve", None, 200),

            # Agent endpoints
            ("GET", "/api/agents/list", None, 200),
            ("POST", "/api/agents/create", {
                "name": "test_agent",
                "type": "analysis",
                "config": {"enabled": True}
            }, 200),

            # Task Queue endpoints
            ("GET", "/api/task-queue", None, 200),
            ("POST", "/api/task-queue", {
                "type": "test_task",
                "title": "Test Autonomous Task",
                "description": "Testing the task queue system",
                "source": "test_script",
                "priority": "medium",
                "labels": ["test", "automation"]
            }, 200),

            # Autonomy endpoints
            ("GET", "/api/autonomy/actions", None, 200),
            ("POST", "/api/autonomy/log", {
                "type": "test_action",
                "description": "Testing autonomy logging",
                "context": {"test": True}
            }, 200),
        ]

        passed = 0
        total = len(tests)
        messages = []

        for method, endpoint, data, expected_status in tests:
            success, message = self.test_endpoint(method, endpoint, data, expected_status)
            messages.append(message)

            if success:
                passed += 1
                print(message)
            else:
                print(message)
                # Continue testing even if one fails

            # Small delay between requests to be respectful
            time.sleep(0.5)

        print("=" * 60)
        print(f"📊 Test Results: {passed}/{total} endpoints passed")

        if passed == total:
            print("🎉 All backend endpoints are working correctly!")
            return passed, total, messages
        else:
            print(f"⚠️  {total - passed} endpoints failed or returned unexpected status")
            return passed, total, messages

def main():
    """Main test runner"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    print(f"Testing Kor'tana backend at: {base_url}")
    print("Make sure the backend is running before running these tests.")
    print("Usage: python test-backend-endpoints.py [base_url]")
    print()

    tester = BackendTester(base_url)
    passed, total, messages = tester.run_all_tests()

    # Write detailed results to file
    with open("backend-test-results.json", "w") as f:
        json.dump({
            "timestamp": time.time(),
            "base_url": base_url,
            "passed": passed,
            "total": total,
            "success_rate": passed / total if total > 0 else 0,
            "results": messages
        }, f, indent=2)

    print(f"\n📄 Detailed results saved to: backend-test-results.json")

    # Exit with appropriate code
    if passed == total:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print(f"❌ {total - passed} tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
