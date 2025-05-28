# C:\kortana\tests\test_memory.py
import pytest
import os
import json
from pathlib import Path
from datetime import datetime, timezone

# Adjust import based on how you run tests
try:
    from src.memory import MemoryManager 
except ImportError:
    import sys
    from pathlib import Path
    src_path = str(Path(__file__).parent.parent / "src")
    if src_path not in sys.path:
        sys.path.append(src_path)
    from src.memory import MemoryManager

# Define test paths relative to this test file's location
TEST_CORE_LOGS_PATH = Path(__file__).parent.parent / "kortana.core" / "test_logs_memory"
TEST_DATA_PATH = Path(__file__).parent.parent / "data" / "test_data_memory"

@pytest.fixture(scope="function") # Use function scope to ensure clean state for each test
def memory_manager_instance():
    """Provides a MemoryManager instance with dedicated test log paths."""
    TEST_CORE_LOGS_PATH.mkdir(parents=True, exist_ok=True)
    TEST_DATA_PATH.mkdir(parents=True, exist_ok=True)

    manager = MemoryManager(
        memory_journal_path=str(TEST_DATA_PATH / "test_journal.jsonl"),
        heart_log_path=str(TEST_CORE_LOGS_PATH / "test_heart.log"),
        soul_index_path=str(TEST_CORE_LOGS_PATH / "test_soul.index"),
        lit_log_path=str(TEST_CORE_LOGS_PATH / "test_lit.log")
    )
    # Clear files before each test if they exist
    for p in [manager.memory_journal_path, manager.heart_log_path, manager.soul_index_path, manager.lit_log_path]:
        if os.path.exists(p):
            os.remove(p)
    return manager

def test_memory_manager_initialization(memory_manager_instance: MemoryManager):
    assert memory_manager_instance is not None
    assert os.path.basename(memory_manager_instance.heart_log_path) == "test_heart.log"

def test_store_gravity_anchor(memory_manager_instance: MemoryManager):
    test_text = "A moment of profound significance."
    test_emotion = "awe"
    test_mode = "intimate"
    test_presence = "high"
    memory_manager_instance.store_gravity_anchor(test_text, test_emotion, test_mode, test_presence)

    assert os.path.exists(memory_manager_instance.heart_log_path)
    with open(memory_manager_instance.heart_log_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert test_text in content
        assert f"- Emotion: {test_emotion}" in content
        assert f"- Voice Mode: {test_mode}" in content
        assert f"- Presence: {test_presence}" in content

def test_store_ritual_marker(memory_manager_instance: MemoryManager):
    test_utterance = "This, I hold sacred."
    test_tone = "reverent"
    test_mode = "presence"
    test_presence = "full"
    memory_manager_instance.store_ritual_marker(test_utterance, test_tone, test_mode, test_presence)

    assert os.path.exists(memory_manager_instance.lit_log_path)
    with open(memory_manager_instance.lit_log_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert test_utterance in content
        assert f"- Tone: {test_tone}" in content

def test_add_to_soul_index(memory_manager_instance: MemoryManager):
    date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    theme = "test_theme"
    ref = "heart.log#test_ref"
    memory_manager_instance.add_to_soul_index(date_str, theme, ref)

    assert os.path.exists(memory_manager_instance.soul_index_path)
    with open(memory_manager_instance.soul_index_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert f"{date_str}: #{theme} -> {ref}" in content

def test_save_interaction_to_journal(memory_manager_instance: MemoryManager):
    interaction = {"role": "user", "content": "Test journal entry.", "timestamp_utc": datetime.now(timezone.utc).isoformat()}
    memory_manager_instance.save_interaction_to_journal(interaction)

    assert os.path.exists(memory_manager_instance.memory_journal_path)
    with open(memory_manager_instance.memory_journal_path, "r", encoding="utf-8") as f:
        line = f.readline()
        assert "Test journal entry." in line
        loaded_interaction = json.loads(line)
        assert loaded_interaction["role"] == "user"

# Clean up test log directories after all tests in this module are done (optional)
# def teardown_module(module):
#     if os.path.exists(TEST_CORE_LOGS_PATH):
#         import shutil
#         shutil.rmtree(TEST_CORE_LOGS_PATH)
#     if os.path.exists(TEST_DATA_PATH):
#         import shutil
#         shutil.rmtree(TEST_DATA_PATH)
#     print("Cleaned up test log directories for memory tests.")
