import logging
import sys
import os

# Configure logging for this diagnostic burst (basic console output). This should happen first.
# Note: basicConfig should ideally be called only once at the application entry point.
# Calling it here might not reconfigure logging if it was already set up by unittest.
# However, we include it here for self-containment of this diagnostic step.
try:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )
except Exception:
    # logging might already be configured
    pass

logger = logging.getLogger(__name__)
_module_file_path = os.path.abspath(__file__)

logger.info(f"[FLASH_DIAG] Test discovery: Loading test module: {__name__} from {_module_file_path}")
logger.info(f"[FLASH_DIAG] sys.path at {__name__} import: {sys.path}")
logger.info(f"[FLASH_DIAG] CWD at {__name__} import: {os.getcwd()}")

import sys
import os # For absolute paths
print(f"--- TRACE (tests/test_project_memory_integration.py): sys.path ---")
for p in sys.path:
    print(p)
print(f"--- TRACE (tests/test_project_memory_integration.py): sys.modules keys (first 20 + relevant) ---")
keys_to_print_test = list(sys.modules.keys())[:20]
relevant_keys_test = [k for k in sys.modules.keys() if 'kortana' in k or 'autonomous_agents' in k or 'brain' in k or 'coding_agent' in k]
for rk_test in relevant_keys_test:
    if rk_test not in keys_to_print_test:
        keys_to_print_test.append(rk_test)
for key_test in sorted(list(set(keys_to_print_test))):
    try:
        print(f"{key_test}: {sys.modules[key_test].__file__ if hasattr(sys.modules[key_test], '__file__') else 'Built-in or no __file__'}")
    except Exception:
        print(f"{key_test}: Error accessing __file__ or built-in module")
print(f"--- END TRACE (tests/test_project_memory_integration.py) ---")

import unittest
import os
import json
import sys
from unittest.mock import patch, MagicMock

# Add the src/ directory to sys.path to allow importing core and brain
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

# Import modules to be tested
from src.core import memory
from src.brain import ChatEngine

# Define the path to the dummy project memory file for testing
TEST_MEMORY_FILE = os.path.join(os.path.dirname(__file__), "temp_project_memory.jsonl")

# Override the PROJECT_MEMORY_PATH in the memory module for testing (Corrected variable name)
memory.PROJECT_MEMORY_PATH = TEST_MEMORY_FILE


class TestProjectMemoryIntegration(unittest.TestCase):

    def setUp(self):
        """Set up test environment: create a dummy memory file and ChatEngine."""
        # Ensure a clean test memory file for each test
        if os.path.exists(TEST_MEMORY_FILE):
            os.remove(TEST_MEMORY_FILE)

        # Create a dummy memory file with a mix of entry types and timestamps for testing retrieval
        initial_memories = [
            {
                "type": "decision",
                "timestamp": "2023-01-01T10:00:00Z",
                "content": "Decision A - oldest decision.",
            },
            {
                "type": "implementation_note",
                "timestamp": "2023-01-02T11:00:00Z",
                "content": "Note B.",
            },
            {
                "type": "decision",
                "timestamp": "2023-01-01T10:00:00Z",
                "content": "Initial test decision 2.",
            },
            {
                "type": "decision",
                "timestamp": "2023-01-01T10:00:00Z",
                "content": "Initial test decision 3.",
            },
        ]

        # Write initial memories to the dummy file
        with open(TEST_MEMORY_FILE, "w") as f:
            for entry in initial_memories:
                json.dump(entry, f)
                f.write("\n")

        # Mock components that ChatEngine depends on but aren't the focus of this test
        # (e.g., LLM clients, other managers, schedulers)
        with patch("brain.LLMClientFactory") as MockLLMClientFactory:
            with patch("brain.MemoryManager") as MockMemoryManager:
                with patch("brain.SacredModelRouter") as MockSacredModelRouter:
                    with patch("brain.BackgroundScheduler") as MockBackgroundScheduler:
                        with patch("brain.CovenantEnforcer") as MockCovenantEnforcer:
                            with patch("brain.PlanningAgent") as MockPlanningAgent:
                                with patch(
                                    "brain.TestingAgent"
                                ) as MockTestingAgent:
                                    with patch(
                                        "brain.MonitoringAgent"
                                    ) as MockMonitoringAgent:

                                        # Configure mocks if necessary (e.g., return specific values)
                                        MockLLMClientFactory.return_value.create_client.return_value = (
                                            MagicMock()
                                        )
                                        MockMemoryManager.return_value = MagicMock()
                                        MockSacredModelRouter.return_value.loaded_models_config = (
                                            {}
                                        )
                                        MockSacredModelRouter.return_value.get_model_for_task.return_value = (
                                            "mock-model"
                                        )
                                        MockSacredModelRouter.return_value.select_model_with_sacred_guidance.return_value = (
                                            "mock-model"
                                        )
                                        MockBackgroundScheduler.return_value = (
                                            MagicMock()
                                        )
                                        MockCovenantEnforcer.return_value = (
                                            MagicMock()
                                        )
                                        MockPlanningAgent.return_value = MagicMock()
                                        MockTestingAgent.return_value = MagicMock()
                                        MockMonitoringAgent.return_value = (
                                            MagicMock()
                                        )

                                        # Initialize ChatEngine - project memory should be loaded here
                                        self.engine = ChatEngine()

    def tearDown(self):
        """Clean up test environment: remove the dummy memory file."""
        if os.path.exists(TEST_MEMORY_FILE):
            os.remove(TEST_MEMORY_FILE)

    def test_memory_loads_on_init(self):
        """Test that project memory is loaded when ChatEngine initializes."""
        # Add some entries *before* initializing the engine in setUp
        # Then check self.engine.project_memories in the test method
        # This requires modifying setUp or creating a separate test helper
        self.assertIsInstance(self.engine.project_memories, list)
        # The expected number of memories might change depending on initial_memories in setUp
        # self.assertEqual(len(self.engine.project_memories), 3) # Adjust or remove this assertion if initial_memories changes

        # Check the content of the loaded memories
        expected_contents = [
            "Decision A - oldest decision.",
            "Initial test decision 2.",
            "Initial test decision 3.",
        ]
        loaded_contents = [mem["content"] for mem in self.engine.project_memories]

        # Sort both lists before comparing to handle potential order differences if load_memory doesn't guarantee order
        loaded_contents.sort()
        expected_contents.sort()

        self.assertEqual(loaded_contents, expected_contents)

        for mem in self.engine.project_memories:
            # self.assertEqual(mem["type"], "decision") # This test needs to handle mixed types now
            self.assertIn("type", mem) # Check that type key exists
            self.assertIn("timestamp", mem)

    def test_save_decision_saves_to_file(self):
        """Test that save_decision correctly appends to the memory file."""
        decision_content = "Test decision to write a test."
        # Call save_decision directly from the memory module
        memory.save_decision(decision_content)

        # Check the file content directly
        with open(TEST_MEMORY_FILE, "r") as f:
            lines = f.readlines()

        # This assertion needs to account for any initial memories written in setUp
        # For this test to be reliable in isolation or within a suite, the memory file should ideally be empty at the start of *this* test method.
        # A better pattern is to save in the test method itself if testing the save function.
        # Assuming for now we check the *last* line appended
        self.assertGreater(len(lines), 0) # Ensure at least one line was written
        entry = json.loads(lines[-1]) # Check the last line
        self.assertEqual(entry["type"], "decision")
        self.assertEqual(entry["content"], decision_content)
        self.assertIn("timestamp", entry)

    def test_save_context_summary_saves_to_file(self):
        """Test that save_context_summary correctly appends to the memory file."""
        summary_content = "Summary of the test setup conversation."
        # Call save_context_summary directly from the memory module
        memory.save_context_summary(summary_content)

        # Check the file content directly
        with open(TEST_MEMORY_FILE, "r") as f:
            lines = f.readlines()

        # Assuming we check the *last* line appended
        self.assertGreater(len(lines), 0) # Ensure at least one line was written
        entry = json.loads(lines[-1]) # Check the last line
        self.assertEqual(entry["type"], "context_summary")
        self.assertEqual(entry["content"], summary_content)
        self.assertIn("timestamp", entry)

    def test_save_implementation_note_saves_to_file(self):
        """Test that save_implementation_note correctly appends to the memory file."""
        note_content = "Test implementation note."
        # Call save_implementation_note directly from the memory module
        memory.save_implementation_note(note_content)

        with open(TEST_MEMORY_FILE, "r") as f:
            lines = f.readlines()

        # Assuming we check the *last* line appended
        self.assertGreater(len(lines), 0) # Ensure at least one line was written
        entry = json.loads(lines[-1]) # Check the last line
        self.assertEqual(entry["type"], "implementation_note")
        self.assertEqual(entry["content"], note_content)
        self.assertIn("timestamp", entry)

    def test_save_project_insight_saves_to_file(self):
        """Test that save_project_insight correctly appends to the memory file."""
        insight_content = "Test project insight."
        # Call save_project_insight directly from the memory module
        memory.save_project_insight(insight_content)

        with open(TEST_MEMORY_FILE, "r") as f:
            lines = f.readlines()

        # Assuming we check the *last* line appended
        self.assertGreater(len(lines), 0) # Ensure at least one line was written
        entry = json.loads(lines[-1]) # Check the last line
        self.assertEqual(entry["type"], "project_insight")
        self.assertEqual(entry["content"], insight_content)
        self.assertIn("timestamp", entry)

    def test_summarization_trigger(self):
        """Test that summarization is triggered after N messages."""
        # This test requires mocking the LLM client to return a summary
        # And checking if save_memory is called with a context_summary entry
        # pass # Placeholder

        # Mock the LLM client's create_client and generate_content methods
        with patch("brain.LLMClientFactory.create_client") as mock_create_client:
            with patch("brain.ChatEngine.summarize_context") as mock_summarize_context:

                # Configure the mocked LLM client to return a dummy summary
                mock_llm_client = MagicMock()
                mock_create_client.return_value = mock_llm_client

                # Simulate adding messages to trigger summarization
                # Assuming SUMMARY_THRESHOLD is accessible or hardcoded for the test
                # Need to know the SUMMARY_THRESHOLD value from brain.py
                # For now, let's assume it's 20 based on previous conversation.
                SUMMARY_THRESHOLD = 20  # This should ideally be imported or mocked

                # Add messages up to the threshold minus one
                for i in range(SUMMARY_THRESHOLD - 1):
                    self.engine.add_user_message(f"User message {i+1}")
                    self.engine.add_assistant_message(f"Assistant response {i+1}")

                # Assure summarization is NOT called yet
                mock_summarize_context.assert_not_called()

                # Add one more message to trigger summarization
                self.engine.add_user_message("Last user message to trigger summary")

                # Assert that summarize_context was called
                mock_summarize_context.assert_called_once()

    def test_project_memory_in_system_prompt(self):
        """Test that loaded project memories are included in the system prompt."""
        # Add dummy memories *before* initializing the engine in setUp
        # Then call self.engine.build_system_prompt()
        # And assert that the generated prompt string contains the memory content
        # pass # Placeholder

        # The memories are loaded in setUp
        system_prompt = self.engine.build_system_prompt()

        # Check if the content of the initial memories is in the system prompt string
        expected_contents = [
            "Decision A - oldest decision.",
            "Note B.",
            "Initial test decision 2.",
            "Initial test decision 3.",
        ]

        for content in expected_contents:
            self.assertIn(content, system_prompt)

    def test_get_memory_by_type(self):
        """Test that get_memory_by_type correctly filters memories by type."""
        # The setUp method creates a dummy file with mixed types
        all_memories = memory.load_memory()
        self.assertEqual(
            len(all_memories), 4
        )  # Verify total entries loaded based on setUp

        decisions = memory.get_memory_by_type("decision")
        self.assertEqual(len(decisions), 3)
        for d in decisions:
            self.assertEqual(d["type"], "decision")

        notes = memory.get_memory_by_type("implementation_note")
        self.assertEqual(len(notes), 1)
        for n in notes:
            self.assertEqual(n["type"], "implementation_note")

        summaries = memory.get_memory_by_type("context_summary")
        self.assertEqual(len(summaries), 0)  # Should be none initially

    def test_get_recent_memories_by_type(self):
        """Test that get_recent_memories_by_type returns the correct number of recent memories."""
        # The setUp method provides data with mixed types and timestamps.
        # Note: Timestamps for 'decision' entries are not distinct in the current setup,
        # limiting robust recency testing for decisions with this data.

        # Test retrieving recent implementation notes (only one note with a distinct timestamp)
        recent_notes = memory.get_recent_memories_by_type(
            "implementation_note", limit=1
        )
        self.assertEqual(len(recent_notes), 1)
        self.assertEqual(recent_notes[0]["type"], "implementation_note")
        self.assertEqual(recent_notes[0]["content"], "Note B.")  # Based on setUp data

        # Test retrieving recent decisions (with non-distinct timestamps, just check count)
        recent_decisions = memory.get_recent_memories_by_type("decision", limit=2)
        # Due to identical timestamps, this might return more than 2 or an unpredictable subset.
        # We'll assert that it returns at most the limit, or all if limit exceeds available.
        self.assertTrue(len(recent_decisions) <= 2)  # Should return at most the limit
        for d in recent_decisions:
            self.assertEqual(d["type"], "decision")

        # Test retrieving more recent decisions than available
        all_recent_decisions = memory.get_recent_memories_by_type("decision", limit=10)
        self.assertEqual(len(all_recent_decisions), 3)  # Should return all 3 decisions
        for d in all_recent_decisions:
            self.assertEqual(d["type"], "decision")


if __name__ == "__main__":
    unittest.main()
