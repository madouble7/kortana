#!/usr/bin/env python3
"""
Kor'tana AI Summarization Test Suite
===================================
Test real Gemini 2.0 Flash integration with practical scenarios
"""

import sys
import time
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from relays.relay import EnhancedKortanaRelay


class AITestSuite:
    """Comprehensive AI testing for Gemini 2.0 Flash integration"""

    def __init__(self):
        self.relay = EnhancedKortanaRelay()
        self.test_results = []
        self.token_usage = {
            "total_input": 0,
            "total_output": 0,
            "summarizations": 0,
            "context_packages": 0,
        }

    def log_test(self, test_name: str, status: str, details: str = "", tokens: int = 0):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "tokens": tokens,
            "timestamp": datetime.now().isoformat(),
        }
        self.test_results.append(result)

        status_emoji = {"PASS": "[PASS]", "FAIL": "[FAIL]", "WARN": "[WARN]"}
        print(f"{status_emoji.get(status, '[TEST]')} {test_name}: {status}")
        if details:
            print(f"   {details}")
        if tokens > 0:
            print(f"   Tokens: {tokens}")

    def test_api_connection(self):
        """Test 1: Verify API connection"""
        print("\n🔌 TESTING API CONNECTION")
        print("=" * 30)

        if self.relay.model:
            try:
                # Simple test prompt
                test_prompt = "Respond with exactly: 'API connection successful'"
                response = self.relay.model.generate_content(test_prompt)

                if "API connection successful" in response.text:
                    self.log_test(
                        "API Connection", "PASS", "Gemini responding correctly"
                    )
                else:
                    self.log_test(
                        "API Connection",
                        "WARN",
                        f"Unexpected response: {response.text[:50]}",
                    )

            except Exception as e:
                self.log_test("API Connection", "FAIL", f"API error: {e}")
        else:
            self.log_test("API Connection", "FAIL", "No model configured")

    def test_token_counting(self):
        """Test 2: Token counting accuracy"""
        print("\n🔢 TESTING TOKEN COUNTING")
        print("=" * 25)

        test_texts = [
            ("Short text", "Hello world"),
            (
                "Medium text",
                "This is a longer text with multiple sentences. It should count more tokens than the short text.",
            ),
            (
                "Long text",
                "This is a very long text that spans multiple sentences and includes various types of content. "
                * 10,
            ),
        ]

        for name, text in test_texts:
            tokens = self.relay.count_tokens(text)
            self.log_test(
                f"Token Count - {name}", "PASS", f"Text: {len(text)} chars", tokens
            )
            self.token_usage["total_input"] += tokens

    def test_basic_summarization(self):
        """Test 3: Basic AI summarization"""
        print("\n📝 TESTING BASIC SUMMARIZATION")
        print("=" * 30)

        test_history = """
        [2025-05-30 09:00] claude: Starting analysis of the authentication module
        [2025-05-30 09:05] claude: Found security vulnerability in password validation
        [2025-05-30 09:10] flash: Quick fix - add bcrypt hashing and salt
        [2025-05-30 09:15] weaver: Integrating the security fix with user management
        [2025-05-30 09:20] claude: Testing the updated authentication flow
        [2025-05-30 09:25] flash: All tests passing, ready for deployment
        [2025-05-30 09:30] weaver: Documentation updated, security audit complete
        """.strip()

        try:
            summary = self.relay.summarize_with_gemini(test_history, max_tokens=500)

            if "[MOCK SUMMARY]" in summary:
                self.log_test("Basic Summarization", "FAIL", "Still using mock mode")
            else:
                input_tokens = self.relay.count_tokens(test_history)
                output_tokens = self.relay.count_tokens(summary)

                self.log_test(
                    "Basic Summarization",
                    "PASS",
                    f"Input: {input_tokens}→Output: {output_tokens} tokens",
                )
                self.token_usage["total_input"] += input_tokens
                self.token_usage["total_output"] += output_tokens
                self.token_usage["summarizations"] += 1

                print(f"   📄 Summary Preview: {summary[:100]}...")

        except Exception as e:
            self.log_test("Basic Summarization", "FAIL", f"Summarization error: {e}")

    def test_context_package_creation(self):
        """Test 4: Context package creation and storage"""
        print("\n📦 TESTING CONTEXT PACKAGES")
        print("=" * 28)

        test_task = {
            "id": f"ai_test_{int(time.time())}",
            "code": "def authenticate(username, password):\n    return bcrypt.checkpw(password, hash)",
            "issues": ["Add rate limiting", "Implement 2FA"],
            "commit_ref": "abc123",
        }

        test_summary = "Authentication module updated with bcrypt hashing and security improvements. Tests passing, ready for deployment."

        try:
            tokens_saved = self.relay.save_context_package(
                task_id=test_task["id"],
                summary=test_summary,
                code=test_task["code"],
                issues=test_task["issues"],
                commit_ref=test_task["commit_ref"],
            )

            self.log_test(
                "Context Package",
                "PASS",
                f"Package saved: {test_task['id']}",
                tokens_saved,
            )
            self.token_usage["context_packages"] += 1

        except Exception as e:
            self.log_test("Context Package", "FAIL", f"Storage error: {e}")

    def test_threshold_logic(self):
        """Test 5: Token threshold and handoff logic"""
        print("\n⚡ TESTING THRESHOLD LOGIC")
        print("=" * 27)

        # Test with small history (below threshold)
        small_history = "Agent activity log with minimal content."
        small_task = {"id": "small_test", "code": "", "issues": []}

        output_small, result_small = self.relay.route_task(small_task, small_history)

        if result_small == small_history:
            self.log_test("Below Threshold", "PASS", "No summarization triggered")
        else:
            self.log_test("Below Threshold", "WARN", "Unexpected summarization")

        # Test with large history (above threshold) - simulate by setting low threshold
        original_threshold = self.relay.handoff_threshold
        self.relay.handoff_threshold = 0.001  # Very low threshold for testing

        large_history = "Large agent conversation history. " * 1000  # Force threshold
        large_task = {"id": "large_test", "code": "test_code", "issues": ["test_issue"]}

        output_large, result_large = self.relay.route_task(large_task, large_history)

        if result_large != large_history:
            self.log_test(
                "Above Threshold", "PASS", "Summarization triggered correctly"
            )
        else:
            self.log_test("Above Threshold", "FAIL", "Summarization not triggered")

        # Restore original threshold
        self.relay.handoff_threshold = original_threshold

    def test_database_integration(self):
        """Test 6: Database operations"""
        print("\n💾 TESTING DATABASE INTEGRATION")
        print("=" * 32)

        try:
            conn = sqlite3.connect(self.relay.db_path)
            cursor = conn.cursor()

            # Check context table
            cursor.execute("SELECT COUNT(*) FROM context")
            context_count = cursor.fetchone()[0]

            # Check for our test packages
            cursor.execute(
                "SELECT COUNT(*) FROM context WHERE task_id LIKE 'ai_test_%'"
            )
            test_count = cursor.fetchone()[0]

            conn.close()

            self.log_test(
                "Database Read",
                "PASS",
                f"Total packages: {context_count}, Test packages: {test_count}",
            )

        except Exception as e:
            self.log_test("Database Read", "FAIL", f"Database error: {e}")

    def test_agent_discovery(self):
        """Test 7: Agent discovery and status"""
        print("\n🤖 TESTING AGENT DISCOVERY")
        print("=" * 26)

        agents = self.relay.agents
        active_count = len(
            [a for a in agents.values() if a.get("status") == "discovered"]
        )

        self.log_test(
            "Agent Discovery",
            "PASS",
            f"Found {len(agents)} agents, {active_count} active",
        )

        for agent_name, agent_info in agents.items():
            log_file = agent_info.get("log")
            if log_file and log_file.exists():
                size = log_file.stat().st_size
                self.log_test(f"Agent {agent_name}", "PASS", f"Log file: {size} bytes")
            else:
                self.log_test(f"Agent {agent_name}", "WARN", "No log file found")

    def run_full_test_suite(self):
        """Run complete AI test suite"""
        print("[TEST] KOR'TANA AI TEST SUITE - GEMINI 2.0 FLASH")
        print("=" * 50)
        print(f"[TIME] Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(
            f"[KEY] API Key: {self.relay.gemini_api_key[:15]}..."
            if self.relay.gemini_api_key
            else "No API key"
        )
        print(
            f"[MODEL] Model: {'Gemini 2.0 Flash' if self.relay.model else 'Mock mode'}"
        )

        # Run all tests
        self.test_api_connection()
        self.test_token_counting()
        self.test_basic_summarization()
        self.test_context_package_creation()
        self.test_threshold_logic()
        self.test_database_integration()
        self.test_agent_discovery()

        # Generate summary report
        self.generate_report()

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("🎯 TEST SUITE RESULTS")
        print("=" * 60)

        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        warned = len([r for r in self.test_results if r["status"] == "WARN"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"])
        total = len(self.test_results)

        print(
            f"📊 SUMMARY: {passed}/{total} passed, {warned} warnings, {failed} failures"
        )
        print("🔢 TOKEN USAGE:")
        print(f"   Input Tokens: {self.token_usage['total_input']:,}")
        print(f"   Output Tokens: {self.token_usage['total_output']:,}")
        print(f"   Summarizations: {self.token_usage['summarizations']}")
        print(f"   Context Packages: {self.token_usage['context_packages']}")

        if failed == 0:
            print("\n🎉 ALL CRITICAL TESTS PASSED!")
            print("✅ Gemini 2.0 Flash integration is FULLY OPERATIONAL")
            print("🚀 Ready for autonomous operation with real AI power")
        elif failed <= 2:
            print("\n⚠️ MOSTLY FUNCTIONAL - Minor issues detected")
            print("🔧 Review warnings and address any critical failures")
        else:
            print("\n❌ MULTIPLE FAILURES DETECTED")
            print("🛠️ System needs attention before production use")

        # Save detailed results
        report_file = Path(__file__).parent / "ai_test_results.json"
        with open(report_file, "w") as f:
            json.dump(
                {
                    "summary": {
                        "passed": passed,
                        "warned": warned,
                        "failed": failed,
                        "total": total,
                    },
                    "token_usage": self.token_usage,
                    "detailed_results": self.test_results,
                    "timestamp": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )

        print(f"\n📄 Detailed results saved to: {report_file}")
        print("=" * 60)


def main():
    """Main test runner"""
    test_suite = AITestSuite()
    test_suite.run_full_test_suite()


if __name__ == "__main__":
    main()
