import unittest
import subprocess
import sys
import os
import sqlite3
from datetime import datetime, timedelta
import time # For time.sleep if needed in tests, though less ideal

# Add project root to sys.path to allow importing relays module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from relays.relay import AGENTS, register_agent, update_agent_handoff_time, get_all_agents_status, get_torch_log_from_db, display_torch_log

# Define path to the database, assuming it's in ../logs/kortana.db relative to this test file
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'logs', 'kortana.db')
RELAY_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), '..', 'relays', 'relay.py')

class TestRelay(unittest.TestCase):

    def setUp(self):
        """Clear AGENTS and torch_passes table before each test."""
        AGENTS.clear()
        # Ensure logs directory exists
        logs_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        # Clear or ensure creation of the torch_passes table
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # Drop table if it exists and recreate, or just delete from it
            cursor.execute("DROP TABLE IF EXISTS torch_passes")
            cursor.execute("""
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
            conn.commit()
        except sqlite3.Error as e:
            self.fail(f"Database setup failed: {e}")
        finally:
            if conn:
                conn.close()

    def test_register_agent(self):
        """Test agent registration."""
        register_agent("Agent001", version="1.0")
        self.assertIn("Agent001", AGENTS)
        self.assertEqual(AGENTS["Agent001"]['version'], "1.0")
        self.assertIsInstance(AGENTS["Agent001"]['last_handoff_time'], datetime)

    def test_update_agent_handoff_time(self):
        """Test updating an agent's handoff time."""
        register_agent("Agent002", version="1.0")
        original_time = AGENTS["Agent002"]['last_handoff_time']
        # Simulate a delay to ensure the new timestamp is different
        time.sleep(0.01)
        new_handoff_time = datetime.now()
        update_agent_handoff_time("Agent002", new_handoff_time)
        self.assertEqual(AGENTS["Agent002"]['last_handoff_time'], new_handoff_time)
        self.assertNotEqual(original_time, new_handoff_time)

    def test_get_all_agents_status(self):
        """Test getting status of all registered agents."""
        register_agent("Agent003", version="1.1")
        time.sleep(0.01) # ensure different timestamps if that matters for output
        register_agent("Agent004", version="1.2")
        status_output = get_all_agents_status()
        self.assertIn("Agent003", status_output)
        self.assertIn("Version: 1.1", status_output)
        self.assertIn("Agent004", status_output)
        self.assertIn("Version: 1.2", status_output)
        self.assertIn("Status: active", status_output)

    def test_torch_log_empty(self):
        """Test fetching torch log when the database is empty."""
        log_entries = get_torch_log_from_db()
        self.assertEqual(log_entries, [])

        # Test display_torch_log with empty list
        # We need to capture stdout to check the print
        from io import StringIO
        import sys
        captured_output = StringIO()
        sys.stdout = captured_output
        display_torch_log(log_entries)
        sys.stdout = sys.__stdout__  # Reset stdout
        self.assertIn("No torch handoff events found.", captured_output.getvalue())

    def _add_mock_db_entry(self, outgoing="OutMock", incoming="InMock", version="1.0", summary="Test summary", tokens=100, msg="Test msg"):
        """Helper to add a mock entry to the database."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            ts = datetime.now()
            cursor.execute("""
                INSERT INTO torch_passes (timestamp, outgoing_agent_name, incoming_agent_name, incoming_agent_version, summary, token_count_at_handoff, message_to_successor)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (ts, outgoing, incoming, version, summary, tokens, msg))
            conn.commit()
            return ts # Return timestamp for verification
        except sqlite3.Error as e:
            self.fail(f"Failed to add mock DB entry: {e}")
        finally:
            if conn:
                conn.close()

    def test_torch_log_with_data(self):
        """Test fetching and displaying torch log with data."""
        mock_ts = self._add_mock_db_entry(summary="Data test")

        log_entries = get_torch_log_from_db()
        self.assertEqual(len(log_entries), 1)
        entry = log_entries[0]
        # Timestamp from DB is string, convert mock_ts for comparison if needed, or compare parts
        self.assertEqual(entry['summary'], "Data test")
        self.assertEqual(entry['outgoing_agent_name'], "OutMock")

        from io import StringIO
        import sys
        captured_output = StringIO()
        sys.stdout = captured_output
        display_torch_log(log_entries)
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        self.assertIn("OutMock -> InMock (v1.0)", output)
        self.assertIn("Data test", output)
        self.assertIn("Tokens: 100", output)
        self.assertIn("Msg: Test msg", output)

    def test_main_status_output(self):
        """Test `python relays/relay.py --status` output."""
        # Need to register agents in the context of the script being run
        # This test assumes that the AGENTS dict is global and will be populated
        # by the script when it runs. This is tricky because the script's AGENTS
        # is distinct from this test's AGENTS unless carefully managed.
        # For simplicity, we'll assume the script's internal registration works.
        # The script already has sample registrations in its `if __name__ == "__main__":`

        process = subprocess.run(
            [sys.executable, RELAY_SCRIPT_PATH, '--status'],
            capture_output=True, text=True, check=False
        )
        output = process.stdout
        self.assertIn("Agent001", output) # From script's own registration
        self.assertIn("Version: 1.1", output)
        self.assertIn("Agent002", output) # From script's own registration
        self.assertIn("Version: 1.0", output)

    def test_main_torch_log_output(self):
        """Test `python relays/relay.py --torch-log` output."""
        self._add_mock_db_entry(outgoing="CLIOut", incoming="CLIIn", summary="CLI Test")

        process = subprocess.run(
            [sys.executable, RELAY_SCRIPT_PATH, '--torch-log'],
            capture_output=True, text=True, check=False
        )
        output = process.stdout
        self.assertIn("CLIOut -> CLIIn", output)
        self.assertIn("CLI Test", output)

if __name__ == '__main__':
    unittest.main()
