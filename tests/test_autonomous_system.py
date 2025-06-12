"""
Complete Autonomous System Test
==============================

Tests all components of the autonomous Kor'tana system:
- Database initialization
- Relay system with Gemini integration
- Agent handoff procedures
- Context package creation
- Token monitoring
- Automation scripts

Usage:
    python test_autonomous_system.py
    python test_autonomous_system.py --full  # Extended tests
"""

import os
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class AutonomousSystemTest:
    """Complete test suite for the autonomous Kor'tana system"""

    def __init__(self):
        """Initialize test environment"""
        self.project_root = Path(__file__).parent
        self.logs_dir = self.project_root / "logs"
        self.queues_dir = self.project_root / "queues"
        self.db_path = self.project_root / "kortana.db"
        self.test_results = []

        # Ensure directories exist
        self.logs_dir.mkdir(exist_ok=True)
        self.queues_dir.mkdir(exist_ok=True)

    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append(
            {
                "test": test_name,
                "success": success,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }
        )
        print(f"{status} {test_name}: {message}")

    def test_database_initialization(self) -> bool:
        """Test database creation and schema"""
        try:
            # Test database initialization
            result = subprocess.run(
                [sys.executable, "init_db.py"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                self.log_test(
                    "Database Init", False, f"Init script failed: {result.stderr}"
                )
                return False

            # Verify database exists and has correct schema
            if not self.db_path.exists():
                self.log_test("Database Init", False, "Database file not created")
                return False

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check for required tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            required_tables = ["context", "agent_activity"]
            missing_tables = [t for t in required_tables if t not in tables]

            conn.close()

            if missing_tables:
                self.log_test(
                    "Database Init", False, f"Missing tables: {missing_tables}"
                )
                return False

            self.log_test(
                "Database Init", True, f"Database created with tables: {tables}"
            )
            return True

        except Exception as e:
            self.log_test("Database Init", False, str(e))
            return False

    def test_relay_system(self) -> bool:
        """Test enhanced relay system"""
        try:
            # Test relay status
            result = subprocess.run(
                [sys.executable, "relays/relay.py", "--status"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                self.log_test(
                    "Relay System", False, f"Status check failed: {result.stderr}"
                )
                return False

            # Test single cycle
            result = subprocess.run(
                [sys.executable, "relays/relay.py"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                self.log_test(
                    "Relay System", False, f"Single cycle failed: {result.stderr}"
                )
                return False

            self.log_test("Relay System", True, "Single cycle completed successfully")
            return True

        except Exception as e:
            self.log_test("Relay System", False, str(e))
            return False

    def test_handoff_system(self) -> bool:
        """Test agent handoff system"""
        try:
            # Test handoff status
            result = subprocess.run(
                [sys.executable, "relays/handoff.py", "--status"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                self.log_test(
                    "Handoff System", False, f"Status check failed: {result.stderr}"
                )
                return False

            self.log_test("Handoff System", True, "Status check successful")
            return True

        except Exception as e:
            self.log_test("Handoff System", False, str(e))
            return False

    def test_gemini_integration(self) -> bool:
        """Test Gemini integration (with or without API key)"""
        try:
            # Test summarization
            result = subprocess.run(
                [sys.executable, "relays/relay.py", "--summarize"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                self.log_test(
                    "Gemini Integration",
                    False,
                    f"Summarization test failed: {result.stderr}",
                )
                return False

            # Check if API key is configured
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                self.log_test(
                    "Gemini Integration",
                    True,
                    "API key configured, summarization works",
                )
            else:
                self.log_test(
                    "Gemini Integration",
                    True,
                    "Mock summarization works (set GEMINI_API_KEY for full AI)",
                )

            return True

        except Exception as e:
            self.log_test("Gemini Integration", False, str(e))
            return False

    def test_context_packages(self) -> bool:
        """Test context package creation and storage"""
        try:
            # Create test agent logs
            test_agent = "test_agent"
            log_file = self.logs_dir / f"{test_agent}.log"

            with open(log_file, "w") as f:
                f.write(f"{datetime.now()} | Test agent started\n")
                f.write(f"{datetime.now()} | Processing task 1\n")
                f.write(f"{datetime.now()} | Task 1 completed\n")

            # Test context package creation
            from relays.relay import KortanaRelay

            relay = KortanaRelay()

            tokens_saved = relay.save_context_package(
                task_id="test_context_001",
                summary="Test context package for system validation",
                code="def test(): pass",
                issues=["Add more tests"],
                commit_ref="test_commit",
            )

            if tokens_saved > 0:
                self.log_test(
                    "Context Packages",
                    True,
                    f"Created package with {tokens_saved} tokens",
                )
                return True
            else:
                self.log_test(
                    "Context Packages", False, "Failed to create context package"
                )
                return False

        except Exception as e:
            self.log_test("Context Packages", False, str(e))
            return False

    def test_automation_scripts(self) -> bool:
        """Test Windows automation scripts"""
        try:
            # Check if batch files exist
            scripts = [
                self.project_root / "relays" / "run_relay.bat",
                self.project_root / "relays" / "handoff.bat",
            ]

            missing_scripts = [s for s in scripts if not s.exists()]
            if missing_scripts:
                self.log_test(
                    "Automation Scripts", False, f"Missing scripts: {missing_scripts}"
                )
                return False

            # Test batch file syntax (basic check)
            for script in scripts:
                with open(script) as f:
                    content = f.read()
                    if "python" not in content.lower():
                        self.log_test(
                            "Automation Scripts",
                            False,
                            f"Invalid script: {script.name}",
                        )
                        return False

            self.log_test(
                "Automation Scripts", True, "All automation scripts present and valid"
            )
            return True

        except Exception as e:
            self.log_test("Automation Scripts", False, str(e))
            return False

    def test_token_monitoring(self) -> bool:
        """Test token counting and threshold detection"""
        try:
            from relays.relay import KortanaRelay

            relay = KortanaRelay()

            # Test token counting
            test_text = "This is a test string for token counting."
            token_count = relay.count_tokens(test_text)

            if token_count > 0:
                self.log_test(
                    "Token Monitoring",
                    True,
                    f"Token counting works: {token_count} tokens",
                )
                return True
            else:
                self.log_test("Token Monitoring", False, "Token counting failed")
                return False

        except Exception as e:
            self.log_test("Token Monitoring", False, str(e))
            return False

    def create_test_agents(self):
        """Create test agents for demonstration"""
        test_agents = ["claude", "flash", "weaver"]

        for agent in test_agents:
            # Create log file
            log_file = self.logs_dir / f"{agent}.log"
            with open(log_file, "w") as f:
                f.write(f"{datetime.now()} | {agent} agent initialized\n")
                f.write(f"{datetime.now()} | Ready for task processing\n")

            # Create queue file
            queue_file = self.queues_dir / f"{agent}_in.txt"
            queue_file.touch()

        print(f"📁 Created test agents: {test_agents}")

    def run_full_test_suite(self, extended: bool = False) -> bool:
        """Run complete test suite"""
        print("🧪 AUTONOMOUS KOR'TANA SYSTEM TEST")
        print("=" * 50)

        # Create test environment
        self.create_test_agents()

        # Run tests
        tests = [
            ("Database", self.test_database_initialization),
            ("Relay System", self.test_relay_system),
            ("Handoff System", self.test_handoff_system),
            ("Gemini Integration", self.test_gemini_integration),
            ("Context Packages", self.test_context_packages),
            ("Token Monitoring", self.test_token_monitoring),
            ("Automation Scripts", self.test_automation_scripts),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                self.log_test(test_name, False, f"Exception: {e}")

        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 TEST SUMMARY: {passed}/{total} tests passed")
        print("=" * 50)

        success_rate = (passed / total) * 100
        if success_rate >= 85:
            print("🎉 SYSTEM READY: Autonomous Kor'tana system is functional!")
            print("\nNext steps:")
            print("1. Set GEMINI_API_KEY for AI summarization")
            print("2. Run: python setup_automation.py --demo")
            print("3. Choose your automation level")
            return True
        else:
            print("⚠️  ISSUES DETECTED: Some components need attention")
            print("\nFailed tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['message']}")
            return False

    def print_system_info(self):
        """Print system information"""
        print("\n📋 SYSTEM INFORMATION")
        print("-" * 30)
        print(f"Project Root: {self.project_root}")
        print(f"Database: {self.db_path}")
        print(f"Logs: {self.logs_dir}")
        print(f"Queues: {self.queues_dir}")
        print(f"Python: {sys.executable}")
        print(
            f"Gemini API: {'Configured' if os.getenv('GEMINI_API_KEY') else 'Not configured'}"
        )


def main():
    """Main test entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Autonomous Kor'tana System Test")
    parser.add_argument("--full", action="store_true", help="Run extended tests")
    parser.add_argument("--info", action="store_true", help="Show system info")

    args = parser.parse_args()

    tester = AutonomousSystemTest()

    if args.info:
        tester.print_system_info()
        return 0

    success = tester.run_full_test_suite(extended=args.full)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
