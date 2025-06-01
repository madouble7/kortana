"""
Simple Autonomous System Test
============================

Basic test without Unicode symbols for Windows compatibility.
"""

import os
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class SimpleSystemTest:
    """Basic test suite for the autonomous Kor'tana system"""

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
        status = "[PASS]" if success else "[FAIL]"
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

    def test_python_environment(self) -> bool:
        """Test Python environment and packages"""
        try:
            # Check Python version
            version = sys.version_info
            if version.major < 3 or (version.major == 3 and version.minor < 8):
                self.log_test(
                    "Python Environment",
                    False,
                    f"Python {version.major}.{version.minor} too old",
                )
                return False

            # Check required modules
            required_modules = ["sqlite3", "json", "pathlib", "subprocess"]

            for module in required_modules:
                try:
                    __import__(module)
                except ImportError:
                    self.log_test(
                        "Python Environment", False, f"Missing module: {module}"
                    )
                    return False

            self.log_test(
                "Python Environment",
                True,
                f"Python {version.major}.{version.minor} with all modules",
            )
            return True

        except Exception as e:
            self.log_test("Python Environment", False, str(e))
            return False

    def test_file_structure(self) -> bool:
        """Test required files and directories exist"""
        try:
            required_files = ["init_db.py", "relays/relay.py", "relays/handoff.py"]

            required_dirs = ["logs", "queues", "relays"]

            # Check files
            missing_files = []
            for file_path in required_files:
                if not (self.project_root / file_path).exists():
                    missing_files.append(file_path)

            # Check directories
            missing_dirs = []
            for dir_path in required_dirs:
                if not (self.project_root / dir_path).exists():
                    missing_dirs.append(dir_path)

            if missing_files or missing_dirs:
                missing = missing_files + missing_dirs
                self.log_test("File Structure", False, f"Missing: {missing}")
                return False

            self.log_test(
                "File Structure", True, "All required files and directories exist"
            )
            return True

        except Exception as e:
            self.log_test("File Structure", False, str(e))
            return False

    def test_basic_relay_import(self) -> bool:
        """Test if relay module can be imported"""
        try:
            # Test importing the relay module
            sys.path.append(str(self.project_root / "relays"))

            # Try to import without running
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import sys; sys.path.append('relays'); import relay; print('Import successful')",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                self.log_test("Relay Import", False, f"Import failed: {result.stderr}")
                return False

            self.log_test("Relay Import", True, "Relay module imports successfully")
            return True

        except Exception as e:
            self.log_test("Relay Import", False, str(e))
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

        print(f"[INFO] Created test agents: {test_agents}")

    def run_basic_test_suite(self) -> bool:
        """Run basic test suite"""
        print("AUTONOMOUS KOR'TANA SYSTEM - BASIC TEST")
        print("=" * 50)

        # Create test environment
        self.create_test_agents()

        # Run tests
        tests = [
            ("Python Environment", self.test_python_environment),
            ("File Structure", self.test_file_structure),
            ("Database Init", self.test_database_initialization),
            ("Relay Import", self.test_basic_relay_import),
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
        print(f"TEST SUMMARY: {passed}/{total} tests passed")
        print("=" * 50)

        success_rate = (passed / total) * 100
        if success_rate >= 75:
            print("[SUCCESS] Basic system components are functional!")
            print("\nNext steps:")
            print("1. Set GEMINI_API_KEY for AI summarization")
            print("2. Run: python setup_automation.py --demo")
            print("3. Choose your automation level")
            return True
        else:
            print("[WARNING] Some components need attention")
            print("\nFailed tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['message']}")
            return False

    def print_system_info(self):
        """Print system information"""
        print("\nSYSTEM INFORMATION")
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

    parser = argparse.ArgumentParser(
        description="Simple Autonomous Kor'tana System Test"
    )
    parser.add_argument("--info", action="store_true", help="Show system info")

    args = parser.parse_args()

    tester = SimpleSystemTest()

    if args.info:
        tester.print_system_info()
        return 0

    success = tester.run_basic_test_suite()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
