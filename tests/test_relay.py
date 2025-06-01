import unittest
import subprocess
import sys
import os
import sqlite3
from datetime import datetime, timedelta
import time
import json # For test_main_torch_log_with_package_indicator

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from relays.relay import AGENTS, register_agent, update_agent_handoff_time, get_all_agents_status, get_torch_log_from_db, display_torch_log

# Use absolute paths
SCRIPT_DIR_RELAY_TEST = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT_RELAY_TEST = os.path.abspath(os.path.join(SCRIPT_DIR_RELAY_TEST, '..'))

DB_PATH_RELAY_TEST = os.path.join(REPO_ROOT_RELAY_TEST, 'logs', 'kortana.db')
RELAY_SCRIPT_PATH = os.path.join(REPO_ROOT_RELAY_TEST, 'relays', 'relay.py')


class TestRelay(unittest.TestCase):

    def setUp(self):
        """Clear AGENTS and DB tables before each test."""
        AGENTS.clear()

        self.db_path = DB_PATH_RELAY_TEST # For clarity
        logs_dir = os.path.join(REPO_ROOT_RELAY_TEST, 'logs')
        os.makedirs(logs_dir, exist_ok=True)

        try:
            self.conn = sqlite3.connect(self.db_path) # Use self.conn for access in helper methods
            self.cursor = self.conn.cursor()

            self.cursor.execute("DROP TABLE IF EXISTS torch_passes")
            self.cursor.execute("""
                CREATE TABLE torch_passes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    outgoing_agent_name TEXT NOT NULL,
                    incoming_agent_name TEXT NOT NULL,
                    incoming_agent_version TEXT,
                    summary TEXT,
                    token_count_at_handoff INTEGER,
                    message_to_successor TEXT
                )
            """)

            self.cursor.execute("DROP TABLE IF EXISTS torch_packages")
            self.cursor.execute("""
                CREATE TABLE torch_packages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    torch_pass_id INTEGER NOT NULL,
                    package_json TEXT NOT NULL,
                    filepath TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (torch_pass_id) REFERENCES torch_passes(id)
                )
            """)
            self.conn.commit()
        except sqlite3.Error as e:
            # Close connection if it was opened before failing
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
            self.fail(f"Database setup failed: {e}")
        # Don't close self.conn here, helper methods might use it. Close in tearDown if needed.

    def tearDown(self):
        """Close database connection after each test if it's open."""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

    def _add_mock_torch_pass(self, outgoing="OutMock", incoming="InMock", version="1.0", summary="Test summary", tokens=100, msg="Test msg", ts=None):
        """Helper to add a mock torch_passes entry and return its ID."""
        if ts is None:
            ts = datetime.now()
        try:
            self.cursor.execute("""
                INSERT INTO torch_passes (timestamp, outgoing_agent_name, incoming_agent_name, incoming_agent_version, summary, token_count_at_handoff, message_to_successor)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (ts, outgoing, incoming, version, summary, tokens, msg))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            self.fail(f"Failed to add mock torch_pass entry: {e}")
        return None

    def _add_mock_torch_package(self, torch_pass_id, package_data=None, filepath="dummy/path.json"):
        """Helper to add a mock torch_packages entry."""
        if package_data is None:
            package_data = {"detail": "mock package"}
        try:
            self.cursor.execute("""
                INSERT INTO torch_packages (torch_pass_id, package_json, filepath)
                VALUES (?, ?, ?)
            """, (torch_pass_id, json.dumps(package_data), filepath))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            self.fail(f"Failed to add mock torch_package entry: {e}")
        return None


    def test_register_agent(self):
        register_agent("Agent001", version="1.0")
        self.assertIn("Agent001", AGENTS)
        self.assertEqual(AGENTS["Agent001"]['version'], "1.0")
        self.assertIsInstance(AGENTS["Agent001"]['last_handoff_time'], datetime)

    def test_update_agent_handoff_time(self):
        register_agent("Agent002", version="1.0")
        original_time = AGENTS["Agent002"]['last_handoff_time']
        time.sleep(0.01)
        new_handoff_time = datetime.now()
        update_agent_handoff_time("Agent002", new_handoff_time)
        self.assertEqual(AGENTS["Agent002"]['last_handoff_time'], new_handoff_time)
        self.assertNotEqual(original_time, new_handoff_time)

    def test_get_all_agents_status(self):
        register_agent("Agent003", version="1.1")
        time.sleep(0.01)
        register_agent("Agent004", version="1.2")
        status_output = get_all_agents_status()
        self.assertIn("Agent003", status_output)
        self.assertIn("Agent004", status_output)

    def test_torch_log_empty(self):
        log_entries = get_torch_log_from_db() # Uses the relay module's DB_PATH
        self.assertEqual(log_entries, [])
        from io import StringIO
        captured_output = StringIO()
        sys.stdout = captured_output
        display_torch_log(log_entries)
        sys.stdout = sys.__stdout__
        self.assertIn("No torch handoff events found.", captured_output.getvalue())

    def test_torch_log_with_data_and_package_indicator(self):
        """Test fetching and displaying torch log with and without package indicators."""
        tp_id1 = self._add_mock_torch_pass(summary="Log 1 no package")
        tp_id2 = self._add_mock_torch_pass(summary="Log 2 with package", outgoing="AgentC", incoming="AgentD")
        self._add_mock_torch_package(tp_id2) # Link a package to the second pass

        log_entries = get_torch_log_from_db()
        self.assertEqual(len(log_entries), 2)

        from io import StringIO
        captured_output = StringIO()
        sys.stdout = captured_output
        display_torch_log(log_entries)
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()

        self.assertIn("Log 1 no package", output)
        self.assertNotIn("Log 1 no package | Tokens: 100 | Msg: Test msg [+package]", output) # Check that [+package] is not on the item without it

        self.assertIn("Log 2 with package", output)
        self.assertIn("Log 2 with package | Tokens: 100 | Msg: Test msg [+package]", output) # Correctly include the message part

    def test_main_status_output(self):
        process = subprocess.run(
            [sys.executable, RELAY_SCRIPT_PATH, '--status'],
            capture_output=True, text=True, check=False
        )
        output = process.stdout
        # These agents are registered in relay.py's main block
        self.assertIn("Agent001", output)
        self.assertIn("Agent002", output)

    def test_main_torch_log_output_with_package_indicator(self):
        """Test `python relays/relay.py --torch-log` output with package indicators."""
        # Clear existing data by calling setUp helpers directly if needed, or ensure setUp runs first
        # For subprocess calls, the script runs in its own context, so DB must be set up prior to call

        # Add data directly to DB that the subprocess will read
        tp_id1 = self._add_mock_torch_pass(summary="CLI Log 1 NoPkg", ts=datetime.now() - timedelta(seconds=10))
        tp_id2 = self._add_mock_torch_pass(summary="CLI Log 2 WithPkg", outgoing="AgentCliC", ts=datetime.now() - timedelta(seconds=5))
        self._add_mock_torch_package(tp_id2, filepath="cli_dummy.json")

        process = subprocess.run(
            [sys.executable, RELAY_SCRIPT_PATH, '--torch-log'],
            capture_output=True, text=True, check=False
        )
        output = process.stdout

        self.assertIn("CLI Log 1 NoPkg", output)
        # To precisely check for absence of [+package], find the line and test it
        lines = output.splitlines()
        line1_found = False
        for line in lines:
            if "CLI Log 1 NoPkg" in line:
                self.assertNotIn("[+package]", line)
                line1_found = True
                break
        self.assertTrue(line1_found, "CLI Log 1 NoPkg line not found in output")

        line2_found = False
        for line in lines:
            if "CLI Log 2 WithPkg" in line:
                self.assertIn("[+package]", line)
                line2_found = True
                break
        self.assertTrue(line2_found, "CLI Log 2 WithPkg line not found in output")


if __name__ == '__main__':
    unittest.main()
