import os
import pytest
from pathlib import Path

from kortana.memory.memory_manager import MemoryManager
from kortana.config import load_kortana_config

@pytest.fixture(scope="function")
def memory_manager_instance():
    """Provides a MemoryManager instance with test config."""
    settings = load_kortana_config()
    # Override paths for testing if needed, though load_kortana_config might suffice
    manager = MemoryManager(settings=settings)
    return manager


def test_memory_manager_initialization(memory_manager_instance: MemoryManager):
    assert memory_manager_instance is not None
    assert os.path.basename(memory_manager_instance.heart_log_path) == "test_heart.log"


def test_store_gravity_anchor(memory_manager_instance: MemoryManager):
    test_text = "A moment of profound significance."
    test_emotion = "awe"
    test_mode = "intimate"
    test_presence = "high"
    memory_manager_instance.store_gravity_anchor(
        test_text, test_emotion, test_mode, test_presence
    )

    assert os.path.exists(memory_manager_instance.heart_log_path)
    with open(memory_manager_instance.heart_log_path, encoding="utf-8") as f:
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
    memory_manager_instance.store_ritual_marker(
        test_utterance, test_tone, test_mode, test_presence
    )

    assert os.path.exists(memory_manager_instance.lit_log_path)
    with open(memory_manager_instance.lit_log_path, encoding="utf-8") as f:
        content = f.read()
        assert test_utterance in content
        assert f"- Tone: {test_tone}" in content


def test_add_to_soul_index(memory_manager_instance: MemoryManager):
    date_str = datetime.now(UTC).strftime("%Y-%m-%d")
    theme = "test_theme"
    ref = "heart.log#test_ref"
    memory_manager_instance.add_to_soul_index(date_str, theme, ref)

    assert os.path.exists(memory_manager_instance.soul_index_path)
    with open(memory_manager_instance.soul_index_path, encoding="utf-8") as f:
        content = f.read()
        assert f"{date_str}: #{theme} -> {ref}" in content


def test_save_interaction_to_journal(memory_manager_instance: MemoryManager):
    interaction = {
        "role": "user",
        "content": "Test journal entry.",
        "timestamp_utc": datetime.now(UTC).isoformat(),
    }
    memory_manager_instance.save_interaction_to_journal(interaction)

    assert os.path.exists(memory_manager_instance.memory_journal_path)
    with open(memory_manager_instance.memory_journal_path, encoding="utf-8") as f:
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
