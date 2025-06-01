import unittest
import sys
import os
import sqlite3
from datetime import datetime, timedelta, timezone # Added timezone
import time
import json
import uuid
import glob
import copy
from unittest.mock import patch

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from relays.handoff import perform_handoff, prefill_torch_template, prompt_for_torch_package_details
from relays.torch_template import TORCH_PACKAGE_TEMPLATE
from relays.relay import AGENTS, register_agent

# Use absolute paths for DB, logs, and state
SCRIPT_DIR_HANDOFF_TEST = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT_HANDOFF_TEST = os.path.abspath(os.path.join(SCRIPT_DIR_HANDOFF_TEST, '..'))

DB_PATH_HANDOFF_TEST = os.path.join(REPO_ROOT_HANDOFF_TEST, 'logs', 'kortana.db')
LOG_FILE_PATH_HANDOFF_TEST = os.path.join(REPO_ROOT_HANDOFF_TEST, 'logs', 'torch_log.txt')
STATE_DIR_HANDOFF_TEST = os.path.join(REPO_ROOT_HANDOFF_TEST, 'state')


class TestHandoff(unittest.TestCase):

    def setUp(self):
        AGENTS.clear()
        os.makedirs(os.path.join(REPO_ROOT_HANDOFF_TEST, 'logs'), exist_ok=True)
        os.makedirs(STATE_DIR_HANDOFF_TEST, exist_ok=True)

        self.db_path = DB_PATH_HANDOFF_TEST
        self.log_file_path = LOG_FILE_PATH_HANDOFF_TEST
        self.state_dir = STATE_DIR_HANDOFF_TEST

        try:
            conn = sqlite3.connect(self.db_path)
            self.cursor = conn.cursor()
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
            conn.commit()
        except sqlite3.Error as e:
            self.fail(f"Database setup failed: {e}")
        finally:
            if conn:
                conn.close()

        try:
            with open(self.log_file_path, 'w') as f: f.write("")
        except IOError as e: self.fail(f"Text log file setup failed: {e}")

        for f_path in glob.glob(os.path.join(self.state_dir, '*.json')):
            try: os.remove(f_path)
            except OSError as e: print(f"Error removing state file {f_path}: {e}")

    def _get_db_entries(self, table_name):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name} ORDER BY id")
            rows = cursor.fetchall()
            return rows
        except sqlite3.Error as e: self.fail(f"DB read failed for table {table_name}: {e}")
        finally:
            if conn: conn.close()
        return []

    def test_prefill_torch_template(self):
        outgoing_agent = "AgentOutgoing"
        register_agent(outgoing_agent, version="0.8pre")
        result = prefill_torch_template(
            outgoing_agent_name=outgoing_agent,
            incoming_agent_name="AgentIncoming",
            incoming_agent_version="v1.alpha",
            basic_torch_pass_summary="Prefill test summary",
            basic_torch_pass_tokens=150
        )
        self.assertIsInstance(result["task_id"], str)
        self.assertTrue(len(result["task_id"]) > 30)
        self.assertIsInstance(result["timestamp"], str)
        self.assertTrue(len(result["timestamp"]) > 0)
        self.assertEqual(result['agent_profile']['agent_name'], outgoing_agent)
        self.assertEqual(result['agent_profile']['agent_version'], "0.8pre")
        self.assertEqual(result['tokens'], 150)
        self.assertEqual(result['summary'], "Prefill test summary")

    @patch('relays.handoff.prompt_for_torch_package_details')
    def test_perform_handoff_with_detailed_package(self, mock_prompt):
        mock_package_content = copy.deepcopy(TORCH_PACKAGE_TEMPLATE)
        mock_task_id = str(uuid.uuid4())
        mock_package_content['task_id'] = mock_task_id
        mock_package_content['summary'] = "Detailed Summary from Mock"
        mock_package_content['agent_profile']['message_to_successor'] = "Detailed Message from Mock"
        mock_package_content['agent_profile']['agent_name'] = "AgentX"
        mock_package_content['timestamp'] = datetime.now(timezone.utc).isoformat() # Corrected

        mock_prompt.return_value = mock_package_content
        self.assertTrue(os.path.exists(self.db_path), "Database file should exist for handoff")
        perform_handoff("AgentX", "AgentY", "v1.0", "Initial Summary", 100, "Initial Message")
        mock_prompt.assert_called_once()

        tp_entries = self._get_db_entries("torch_passes")
        self.assertEqual(len(tp_entries), 1)
        tp_entry = tp_entries[0]
        self.assertEqual(tp_entry['summary'], "Detailed Summary from Mock")
        self.assertEqual(tp_entry['message_to_successor'], "Detailed Message from Mock")

        pkg_entries = self._get_db_entries("torch_packages")
        self.assertEqual(len(pkg_entries), 1)
        pkg_entry = pkg_entries[0]
        self.assertEqual(pkg_entry['torch_pass_id'], tp_entry['id'])
        loaded_pkg_json = json.loads(pkg_entry['package_json'])
        self.assertEqual(loaded_pkg_json['task_id'], mock_task_id)
        self.assertEqual(loaded_pkg_json['summary'], mock_package_content['summary'])

        self.assertIsNotNone(pkg_entry['filepath'])
        self.assertTrue(os.path.exists(pkg_entry['filepath']))
        with open(pkg_entry['filepath'], 'r') as f:
            file_content = json.load(f)
        self.assertEqual(file_content['task_id'], mock_task_id)

    @patch('builtins.input')
    def test_prompt_interaction_fill_fields(self, mock_input):
        mock_inputs = [
            "", # task_id (keep default from TORCH_PACKAGE_TEMPLATE)
            "Test Task Title",  # task_title
            "Test Summary",     # summary
            "Test Handoff Reason", # handoff_reason
            "Test History Summary", # history_summary
            "Test System Prompt", # system_prompt
            "print('hello world')",   # code
            "issue1, issue2",   # issues (list)
            "feature_branch",      # commit_ref
            "3000",             # tokens (int)
            "",                 # timestamp (keep default)
            # agent_profile section
            "AgentFillerName",      # agent_profile.agent_name
            "v3.filled",          # agent_profile.agent_version
            "ai",                   # agent_profile.agent_type
            "Test Agent Background",  # agent_profile.background
            "strength1, strength2", # agent_profile.strengths (list)
            " ",                      # agent_profile.limitations (clear list)
            "value1, value2",       # agent_profile.values (list)
            "Test Favorite Moment", # agent_profile.favorite_moment
            "Test Lessons Learned", # agent_profile.lessons_learned
            "Test Personality Notes",# agent_profile.personality_notes
            "Test Gratitude",       # agent_profile.gratitude
            "Test Message to Successor", # agent_profile.message_to_successor
            "test_contact_ref",     # agent_profile.contact_or_log_ref
            # kortana_vision section
            "Kortana is a friend.", # kortana_vision.who_is_kortana
            "empathy, foresight",   # kortana_vision.her_strengths (list)
            "still learning",       # kortana_vision.her_limitations (list - becomes one item)
            "Helped debug her CLI.",# kortana_vision.my_role_in_building_her
            "Wishes for sentience.",# kortana_vision.future_hopes
            "Daily standup haiku.", # kortana_vision.rituals_or_habits
            "The time she told a joke." # kortana_vision.favorite_kortana_moment
        ]
        mock_input.side_effect = mock_inputs

        fresh_template = copy.deepcopy(TORCH_PACKAGE_TEMPLATE)
        result = prompt_for_torch_package_details(fresh_template)

        self.assertEqual(result['task_id'], "")
        self.assertEqual(result['task_title'], "Test Task Title")
        self.assertEqual(result['summary'], "Test Summary")
        self.assertEqual(result['handoff_reason'], "Test Handoff Reason")
        self.assertEqual(result['history_summary'], "Test History Summary")
        self.assertEqual(result['system_prompt'], "Test System Prompt")
        self.assertEqual(result['code'], "print('hello world')")
        self.assertEqual(result['issues'], ["issue1", "issue2"])
        self.assertEqual(result['commit_ref'], "feature_branch")
        self.assertEqual(result['tokens'], 3000)
        self.assertEqual(result['timestamp'], "")

        self.assertEqual(result['agent_profile']['agent_name'], "AgentFillerName")
        self.assertEqual(result['agent_profile']['agent_version'], "v3.filled")
        self.assertEqual(result['agent_profile']['agent_type'], "ai")
        self.assertEqual(result['agent_profile']['background'], "Test Agent Background")
        self.assertEqual(result['agent_profile']['strengths'], ["strength1", "strength2"])
        self.assertEqual(result['agent_profile']['limitations'], [])
        self.assertEqual(result['agent_profile']['values'], ["value1", "value2"])
        self.assertEqual(result['agent_profile']['favorite_moment'], "Test Favorite Moment")
        self.assertEqual(result['agent_profile']['lessons_learned'], "Test Lessons Learned")
        self.assertEqual(result['agent_profile']['personality_notes'], "Test Personality Notes")
        self.assertEqual(result['agent_profile']['gratitude'], "Test Gratitude")
        self.assertEqual(result['agent_profile']['message_to_successor'], "Test Message to Successor")
        self.assertEqual(result['agent_profile']['contact_or_log_ref'], "test_contact_ref")

        self.assertEqual(result['kortana_vision']['who_is_kortana'], "Kortana is a friend.")
        self.assertEqual(result['kortana_vision']['her_strengths'], ["empathy", "foresight"])
        self.assertEqual(result['kortana_vision']['her_limitations'], ["still learning"])
        self.assertEqual(result['kortana_vision']['my_role_in_building_her'], "Helped debug her CLI.")
        self.assertEqual(result['kortana_vision']['future_hopes'], "Wishes for sentience.")
        self.assertEqual(result['kortana_vision']['rituals_or_habits'], "Daily standup haiku.")
        self.assertEqual(result['kortana_vision']['favorite_kortana_moment'], "The time she told a joke.")


    @patch('builtins.input')
    def test_prompt_interaction_accept_defaults(self, mock_input):
        mock_input.return_value = ""

        initial_package = prefill_torch_template(
            "AgentDef", "AgentInc", "v0.5", "Default Summary", 50
        )
        expected_package = copy.deepcopy(initial_package)
        result = prompt_for_torch_package_details(initial_package)
        self.assertEqual(result, expected_package)

if __name__ == '__main__':
    unittest.main()
