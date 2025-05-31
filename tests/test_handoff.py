import unittest
import sys
import os
import sqlite3
from datetime import datetime, timedelta
import time

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from relays.handoff import perform_handoff, DB_PATH, LOG_FILE_PATH
from relays.relay import AGENTS, register_agent, update_agent_handoff_time

class TestHandoff(unittest.TestCase):

    def setUp(self):
        """Clear AGENTS, torch_passes table, and torch_log.txt before each test."""
        AGENTS.clear()

        # Ensure logs directory exists
        logs_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        # Clear or ensure creation of the torch_passes table
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
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

        # Clear or ensure creation of the log file
        try:
            # Create the logs directory if it doesn't exist
            os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
            with open(LOG_FILE_PATH, 'w') as f: # Open in write mode to clear it
                f.write("")
        except IOError as e:
            self.fail(f"Log file setup failed: {e}")

    def _get_db_entries(self):
        """Helper to get all entries from torch_passes."""
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM torch_passes ORDER BY id")
            rows = cursor.fetchall()
            return rows
        except sqlite3.Error as e:
            self.fail(f"DB read failed: {e}")
        finally:
            if conn:
                conn.close()
        return []

    def _get_log_file_lines(self):
        """Helper to get all lines from the log file."""
        try:
            if os.path.exists(LOG_FILE_PATH):
                with open(LOG_FILE_PATH, 'r') as f:
                    return f.readlines()
        except IOError as e:
            self.fail(f"Log file read failed: {e}")
        return []

    def test_perform_handoff_new_agents(self):
        """Test handoff where both agents might be new to AGENTS dict, or outgoing exists."""
        # Case 1: Outgoing agent not in AGENTS initially (perform_handoff should register it)
        outgoing_agent_name = "OutAgentNew"
        incoming_agent_name = "InAgentNew"
        version = "1.0"
        summary = "Handoff to new incoming"
        tokens = 1000
        message = "Welcome"

        # Record time before handoff for outgoing agent if it gets registered by perform_handoff
        time_before_outgoing_register = datetime.now()
        time.sleep(0.01) # ensure distinct time

        perform_handoff(outgoing_agent_name, incoming_agent_name, version, summary, tokens, message)

        self.assertIn(outgoing_agent_name, AGENTS)
        self.assertIn(incoming_agent_name, AGENTS)

        # Outgoing agent's handoff time should be the time of this handoff
        # Incoming agent's registration time (also its last_handoff_time) is also time of this handoff
        self.assertAlmostEqual(AGENTS[outgoing_agent_name]['last_handoff_time'], AGENTS[incoming_agent_name]['last_handoff_time'], delta=timedelta(seconds=0.1))
        # Check it's later than when we defined time_before_outgoing_register
        self.assertGreater(AGENTS[outgoing_agent_name]['last_handoff_time'], time_before_outgoing_register)


        self.assertEqual(AGENTS[incoming_agent_name]['version'], version)

        db_entries = self._get_db_entries()
        self.assertEqual(len(db_entries), 1)
        db_entry = db_entries[0]
        self.assertEqual(db_entry['outgoing_agent_name'], outgoing_agent_name)
        self.assertEqual(db_entry['incoming_agent_name'], incoming_agent_name)
        self.assertEqual(db_entry['summary'], summary)
        self.assertEqual(db_entry['message_to_successor'], message)

        log_lines = self._get_log_file_lines()
        self.assertEqual(len(log_lines), 1)
        log_line = log_lines[0]
        self.assertIn(outgoing_agent_name, log_line)
        self.assertIn(incoming_agent_name, log_line)
        self.assertIn(summary, log_line)
        self.assertIn(message, log_line)

    def test_perform_handoff_existing_agents(self):
        """Test handoff where both agents are already registered."""
        out_agent = "OutAgentExisting"
        in_agent = "InAgentExisting"
        initial_version_in = "0.9"
        handoff_version_in = "1.0" # Simulating version update on handoff

        register_agent(out_agent, "0.5")
        time.sleep(0.01) # Ensure distinct timestamps
        register_agent(in_agent, initial_version_in)
        time.sleep(0.01)

        original_out_time = AGENTS[out_agent]['last_handoff_time']
        original_in_time = AGENTS[in_agent]['last_handoff_time']

        summary = "Handoff between existing agents"
        tokens = 1500

        perform_handoff(out_agent, in_agent, handoff_version_in, summary, tokens)

        self.assertGreater(AGENTS[out_agent]['last_handoff_time'], original_out_time)
        self.assertGreater(AGENTS[in_agent]['last_handoff_time'], original_in_time) # register_agent updates time
        self.assertEqual(AGENTS[in_agent]['version'], handoff_version_in) # Version updated

        db_entries = self._get_db_entries()
        self.assertEqual(len(db_entries), 1)
        self.assertEqual(db_entries[0]['outgoing_agent_name'], out_agent)
        self.assertEqual(db_entries[0]['incoming_agent_name'], in_agent)
        self.assertEqual(db_entries[0]['incoming_agent_version'], handoff_version_in)

        log_lines = self._get_log_file_lines()
        self.assertEqual(len(log_lines), 1)
        self.assertIn(f"IN: {in_agent} (v{handoff_version_in})", log_lines[0])


    def test_agent_restart_simulation(self):
        """Simulate an agent restarting and thus re-registering."""
        agent_a = "AgentA_Restart"
        agent_b = "AgentB_Restart"

        register_agent(agent_a, "1.0")
        time.sleep(0.01)

        # Handoff A -> B
        perform_handoff(agent_a, agent_b, "1.0", "A to B", 500)
        time.sleep(0.01)
        agent_b_first_handoff_time = AGENTS[agent_b]['last_handoff_time']

        # Simulate AgentB restarting and re-registering
        time.sleep(0.01)
        register_agent(agent_b, version="1.1") # Re-register with new version

        self.assertGreater(AGENTS[agent_b]['last_handoff_time'], agent_b_first_handoff_time)
        self.assertEqual(AGENTS[agent_b]['version'], "1.1")


if __name__ == '__main__':
    unittest.main()
