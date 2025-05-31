#!/usr/bin/env python3
"""
Kor'tana System Verification & Production Readiness Check
=========================================================
Comprehensive validation before deploying autonomous system
"""

import sqlite3
import subprocess
import sys
from pathlib import Path


class SystemVerifier:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.issues = []
        self.warnings = []
        self.passed = []

    def check_python_environment(self):
        """Verify Python environment and packages"""
        print("\n[CHECK] Python Environment")
        print("-" * 30)

        # Check Python version
        if sys.version_info >= (3, 11):
            self.passed.append("Python 3.11+ detected")
            print(f"[OK] Python {sys.version.split()[0]}")
        else:
            self.issues.append("Python 3.11+ required")
            print(f"[ERROR] Python {sys.version.split()[0]} - upgrade needed")

        # Check virtual environment
        if hasattr(sys, "real_prefix") or (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        ):
            self.passed.append("Virtual environment active")
            print("[OK] Virtual environment active")
        else:
            self.warnings.append("Virtual environment not detected")
            print(
                "[WARNING] No virtual environment detected"
            )  # Check required packages
        required_packages = [
            ("google.generativeai", "google-generativeai"),
            ("tiktoken", "tiktoken"),
            ("sqlite3", "sqlite3"),
            ("pathlib", "pathlib"),
            ("json", "json"),
            ("datetime", "datetime"),
        ]

        for import_name, display_name in required_packages:
            try:
                __import__(import_name)
                self.passed.append(f"Package {display_name} available")
                print(f"[OK] {display_name}")
            except ImportError:
                self.issues.append(f"Missing package: {display_name}")
                print(f"[ERROR] Missing: {display_name}")

    def check_database(self):
        """Verify database configuration"""
        print("\n[CHECK] Database System")
        print("-" * 25)

        db_path = self.base_dir / "kortana.db"
        if db_path.exists():
            self.passed.append("Database file exists")
            print("[OK] Database file found")

            try:
                conn = sqlite3.connect(str(db_path))

                # Check tables
                tables = ["context", "agent_activity", "token_usage", "system_state"]
                cursor = conn.cursor()

                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    self.passed.append(f"Table {table} has {count} records")
                    print(f"[OK] Table '{table}': {count} records")

                conn.close()

            except Exception as e:
                self.issues.append(f"Database error: {e}")
                print(f"[ERROR] Database issue: {e}")
        else:
            self.issues.append("Database not initialized")
            print("[ERROR] Database not found - run init_db.py")

    def check_file_structure(self):
        """Verify required files and directories"""
        print("\n[CHECK] File Structure")
        print("-" * 22)

        required_files = [
            "relays/relay.py",
            "relays/handoff.py",
            "relays/run_relay.bat",
            "relays/handoff.bat",
            "init_db.py",
            "requirements.txt",
        ]

        required_dirs = ["logs", "relays", "venv311"]

        # Check files
        for file_path in required_files:
            full_path = self.base_dir / file_path
            if full_path.exists():
                self.passed.append(f"File {file_path} exists")
                print(f"[OK] {file_path}")
            else:
                self.issues.append(f"Missing file: {file_path}")
                print(f"[ERROR] Missing: {file_path}")

        # Check directories
        for dir_path in required_dirs:
            full_path = self.base_dir / dir_path
            if full_path.exists() and full_path.is_dir():
                self.passed.append(f"Directory {dir_path} exists")
                print(f"[OK] {dir_path}/")
            else:
                self.issues.append(f"Missing directory: {dir_path}")
                print(f"[ERROR] Missing: {dir_path}/")

    def check_relay_system(self):
        """Test relay system functionality"""
        print("\n[CHECK] Relay System")
        print("-" * 20)

        try:
            # Import relay module
            sys.path.append(str(self.base_dir / "relays"))

            # Test relay status
            result = subprocess.run(
                [sys.executable, "relays/relay.py", "--status"],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                self.passed.append("Relay system operational")
                print("[OK] Relay system responds")

                # Check for agent discovery
                if "DISCOVERED" in result.stdout:
                    agent_count = result.stdout.count("DISCOVERED")
                    self.passed.append(f"Discovered {agent_count} agents")
                    print(f"[OK] Discovered {agent_count} agents")
                else:
                    self.warnings.append("No agents discovered")
                    print("[WARNING] No agents discovered")

            else:
                self.issues.append("Relay system error")
                print(f"[ERROR] Relay system failed: {result.stderr}")

        except Exception as e:
            self.issues.append(f"Relay test failed: {e}")
            print(f"[ERROR] Relay test failed: {e}")

    def check_log_files(self):
        """Verify log file access"""
        print("\n[CHECK] Log System")
        print("-" * 18)

        log_dir = self.base_dir / "logs"
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            if log_files:
                self.passed.append(f"Found {len(log_files)} log files")
                print(
                    f"[OK] Found {len(log_files)} log files"
                )  # Check log file permissions
                for log_file in log_files[:3]:  # Check first 3
                    try:
                        with open(log_file, "a"):
                            pass  # Just test write access
                        self.passed.append(f"Log {log_file.name} writable")
                        print(f"[OK] {log_file.name} writable")
                    except Exception as e:
                        self.issues.append(f"Log {log_file.name} not writable")
                        print(f"[ERROR] {log_file.name} not writable: {e}")
            else:
                self.warnings.append("No log files found")
                print("[WARNING] No log files found")
        else:
            self.issues.append("Log directory missing")
            print("[ERROR] Log directory missing")

    def check_automation_setup(self):
        """Check automation scripts"""
        print("\n[CHECK] Automation Setup")
        print("-" * 24)

        automation_files = [
            "automation_control.bat",
            "setup_task_scheduler.py",
            "complete_setup.bat",
        ]

        for file_name in automation_files:
            file_path = self.base_dir / file_name
            if file_path.exists():
                self.passed.append(f"Automation script {file_name} ready")
                print(f"[OK] {file_name}")
            else:
                self.warnings.append(f"Missing automation script: {file_name}")
                print(f"[WARNING] Missing: {file_name}")

    def generate_report(self):
        """Generate final verification report"""
        print("\n" + "=" * 50)
        print(" SYSTEM VERIFICATION REPORT")
        print("=" * 50)

        print(f"\n[PASSED] {len(self.passed)} checks successful")
        print(f"[WARNINGS] {len(self.warnings)} warnings")
        print(f"[ISSUES] {len(self.issues)} critical issues")

        if self.issues:
            print("\nCRITICAL ISSUES:")
            for issue in self.issues:
                print(f"  - {issue}")

        if self.warnings:
            print("\nWARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")

        # Overall status
        if not self.issues:
            if not self.warnings:
                print("\n[RESULT] SYSTEM READY FOR PRODUCTION")
                print("All checks passed - autonomous operation ready!")
                return True
            else:
                print("\n[RESULT] SYSTEM READY WITH WARNINGS")
                print("Core functionality verified - warnings can be addressed later")
                return True
        else:
            print("\n[RESULT] SYSTEM NOT READY")
            print("Critical issues must be resolved before deployment")
            return False

    def run_full_verification(self):
        """Run complete system verification"""
        print("=" * 50)
        print(" KOR'TANA SYSTEM VERIFICATION")
        print("=" * 50)

        self.check_python_environment()
        self.check_database()
        self.check_file_structure()
        self.check_relay_system()
        self.check_log_files()
        self.check_automation_setup()

        return self.generate_report()


if __name__ == "__main__":
    verifier = SystemVerifier()
    is_ready = verifier.run_full_verification()

    if is_ready:
        print("\nNext steps:")
        print("1. Run 'automation_control.bat' to start autonomous operation")
        print("2. Choose automation level (Manual/Semi-Auto/Hands-Off)")
        print("3. Monitor system through logs or status checks")
        print("\nOptional:")
        print("- Configure Gemini API key for full AI summarization")
        print("- Set up monitoring dashboard")
    else:
        print("\nResolve critical issues before proceeding with deployment")

    sys.exit(0 if is_ready else 1)
