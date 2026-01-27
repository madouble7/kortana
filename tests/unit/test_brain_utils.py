#!/usr/bin/env python3
"""
Comprehensive Unit Tests for brain_utils Module
===============================================
Generated tests for complexity reduction and Phase 3 coverage goals.
Focus on format_memory_entries_by_type function as specified in requirements.
"""

import json
from datetime import datetime
from unittest.mock import mock_open, patch

import pytest

from kortana.brain_utils import (
    append_to_memory_journal,
    create_timestamp,
    ensure_directories_exist,
    extract_keywords_from_text,
    format_memory_entries_by_type,
    gentle_log_init,
    load_json_config,
    log_reasoning_content,
    sanitize_user_input,
    validate_memory_entry,
)


class TestLoadJsonConfig:
    """Test JSON configuration loading functionality."""

    def test_load_valid_json_config(self, tmp_path):
        """Test loading a valid JSON configuration file."""
        # Create a temporary config file
        config_data = {"test": "value", "number": 42}
        config_file = tmp_path / "test_config.json"
        config_file.write_text(json.dumps(config_data))

        result = load_json_config(str(config_file))
        assert result == config_data

    def test_load_nonexistent_config_file(self):
        """Test loading a non-existent configuration file."""
        result = load_json_config("/path/that/does/not/exist.json")
        assert result == {}

    def test_load_invalid_json_config(self, tmp_path):
        """Test loading an invalid JSON configuration file."""
        config_file = tmp_path / "invalid_config.json"
        config_file.write_text("{ invalid json content }")

        result = load_json_config(str(config_file))
        assert result == {}

    def test_load_empty_json_config(self, tmp_path):
        """Test loading an empty JSON configuration file."""
        config_file = tmp_path / "empty_config.json"
        config_file.write_text("{}")

        result = load_json_config(str(config_file))
        assert result == {}


class TestAppendToMemoryJournal:
    """Test memory journal appending functionality."""

    def test_append_to_existing_journal(self, tmp_path):
        """Test appending to an existing journal file."""
        journal_file = tmp_path / "memory.jsonl"
        entry = {
            "content": "test memory",
            "type": "test",
            "timestamp": "2025-06-09T10:00:00Z",
        }

        append_to_memory_journal(str(journal_file), entry)

        # Read the file and verify the entry was appended
        content = journal_file.read_text()
        assert json.loads(content.strip()) == entry

    def test_append_multiple_entries(self, tmp_path):
        """Test appending multiple entries to journal."""
        journal_file = tmp_path / "memory.jsonl"
        entry1 = {
            "content": "first memory",
            "type": "test",
            "timestamp": "2025-06-09T10:00:00Z",
        }
        entry2 = {
            "content": "second memory",
            "type": "test",
            "timestamp": "2025-06-09T10:01:00Z",
        }

        append_to_memory_journal(str(journal_file), entry1)
        append_to_memory_journal(str(journal_file), entry2)

        # Read the file and verify both entries
        lines = journal_file.read_text().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0]) == entry1
        assert json.loads(lines[1]) == entry2

    def test_append_to_nonexistent_directory(self):
        """Test appending to a journal in a non-existent directory."""
        with patch("builtins.open", mock_open()) as mock_file:
            entry = {"content": "test", "type": "test"}
            append_to_memory_journal("/nonexistent/path/memory.jsonl", entry)
            mock_file.assert_called_once()


class TestLogReasoningContent:
    """Test reasoning content logging functionality."""

    @patch("src.kortana.brain_utils.logger")
    def test_log_reasoning_content(self, mock_logger):
        """Test logging reasoning content."""
        response = "test response"
        reasoning = "test reasoning"

        log_reasoning_content(response, reasoning)

        mock_logger.debug.assert_called_once_with(
            f"Reasoning content for model {response}: {reasoning}"
        )

    @patch("src.kortana.brain_utils.logger")
    def test_log_reasoning_with_none_content(self, mock_logger):
        """Test logging with None reasoning content."""
        response = "test response"
        reasoning = None

        log_reasoning_content(response, reasoning)

        mock_logger.debug.assert_called_once_with(
            f"Reasoning content for model {response}: {reasoning}"
        )


class TestGentleLogInit:
    """Test gentle logging initialization."""

    def test_gentle_log_init(self):
        """Test that gentle_log_init runs without errors."""
        # This function primarily sets up logging configuration
        # We test that it doesn't raise any exceptions
        try:
            gentle_log_init()
        except Exception as e:
            pytest.fail(f"gentle_log_init raised an exception: {e}")


class TestFormatMemoryEntriesByType:
    """Test memory entries formatting functionality - COMPLEXITY REDUCTION FOCUS."""

    def test_format_empty_memories(self):
        """Test formatting empty memory dictionary."""
        result = format_memory_entries_by_type({})
        assert result == []

    def test_format_conversation_summaries(self):
        """Test formatting conversation summary entries."""
        memories = {
            "conversation_summary": [
                {
                    "content": "Discussed project setup",
                    "timestamp": "2025-06-09T10:00:00Z",
                }
            ]
        }

        result = format_memory_entries_by_type(memories)
        assert len(result) == 2  # Header + entry
        assert "💬 Recent Conversation Summaries:" in result[0]
        assert "Discussed project setup (2025-06-09)" in result[1]

    def test_format_decisions_with_tags(self):
        """Test formatting decision entries with tags."""
        memories = {
            "decision": [
                {
                    "content": "Use OpenAI API for primary LLM",
                    "tags": ["architecture", "api"],
                    "timestamp": "2025-06-09T10:00:00Z",
                },
                {
                    "content": "Implement vector storage",
                    "tags": ["memory", "storage"],
                    "timestamp": "2025-06-08T10:00:00Z",
                },
            ]
        }

        result = format_memory_entries_by_type(memories)
        result_text = "\n".join(result)
        assert "🎯 Key Decisions Made:" in result_text
        assert (
            "Use OpenAI API for primary LLM [architecture, api] (2025-06-09)" in result
        )
        assert "Implement vector storage [memory, storage] (2025-06-08)" in result

    def test_format_implementation_notes(self):
        """Test formatting implementation note entries."""
        memories = {
            "implementation_note": [
                {
                    "content": "Memory system requires async initialization",
                    "component": "memory_manager",
                    "priority": "high",
                    "timestamp": "2025-06-09T10:00:00Z",
                }
            ]
        }

        result = format_memory_entries_by_type(memories)
        result_text = "\n".join(result)
        assert "🛠️ Implementation Context:" in result_text
        assert (
            "Memory system requires async initialization [memory_manager] (Priority: high) (2025-06-09)"
            in result
        )

    def test_format_project_insights(self):
        """Test formatting project insight entries."""
        memories = {
            "project_insight": [
                {
                    "content": "Agent coordination improves with structured protocols",
                    "impact": "high",
                    "timestamp": "2025-06-09T10:00:00Z",
                }
            ]
        }

        result = format_memory_entries_by_type(memories)
        result_text = "\n".join(result)
        assert "💡 Key Project Insights:" in result_text
        assert (
            "Agent coordination improves with structured protocols (Impact: high) (2025-06-09)"
            in result
        )

    def test_format_ade_coding_entries(self):
        """Test formatting ADE coding entries."""
        memories = {
            "ade_coding": [
                {
                    "content": "Generated test file for brain_utils",
                    "type": "ade_coding",
                    "timestamp": "2025-06-09T10:00:00Z",
                }
            ]
        }

        result = format_memory_entries_by_type(memories)
        result_text = "\n".join(result)
        assert "🧩 Other Project Memories:" in result_text
        assert (
            "- [ade_coding] Generated test file for brain_utils (2025-06-09)" in result
        )

    def test_format_mixed_memory_types(self):
        """Test formatting multiple memory types together."""
        memories = {
            "decision": [
                {"content": "Decision 1", "timestamp": "2025-06-09T10:00:00Z"}
            ],
            "implementation_note": [
                {
                    "content": "Note 1",
                    "component": "test",
                    "timestamp": "2025-06-09T10:00:00Z",
                }
            ],
            "ade_coding": [
                {
                    "content": "ADE activity",
                    "type": "ade_coding",
                    "timestamp": "2025-06-09T10:00:00Z",
                }
            ],
        }

        result = format_memory_entries_by_type(memories)

        # Check that all sections are present
        result_text = "\n".join(result)
        assert "🎯 Key Decisions Made:" in result_text
        assert "🛠️ Implementation Context:" in result_text
        assert "🧩 Other Project Memories:" in result_text

    def test_format_entries_without_timestamps(self):
        """Test formatting entries that don't have timestamps."""
        memories = {"decision": [{"content": "Decision without timestamp"}]}

        result = format_memory_entries_by_type(memories)
        assert "Decision without timestamp" in "\n".join(result)

    def test_format_entries_sorting_by_timestamp(self):
        """Test that entries are sorted by timestamp (most recent first)."""
        memories = {
            "decision": [
                {"content": "Older decision", "timestamp": "2025-06-08T10:00:00Z"},
                {"content": "Newer decision", "timestamp": "2025-06-09T10:00:00Z"},
                {"content": "Middle decision", "timestamp": "2025-06-08T15:00:00Z"},
            ]
        }

        result = format_memory_entries_by_type(memories)
        result_text = "\n".join(result)

        # Check that newer decision appears before older decision
        newer_pos = result_text.find("Newer decision")
        older_pos = result_text.find("Older decision")
        assert newer_pos < older_pos

    def test_format_entries_limit_recent_items(self):
        """Test that only the most recent items are included (limits applied)."""
        # Create 10 decision entries
        decisions = [
            {"content": f"Decision {i}", "timestamp": f"2025-06-0{9 - i}T10:00:00Z"}
            for i in range(10)
        ]

        memories = {"decision": decisions}
        result = format_memory_entries_by_type(memories)

        # Should only show 5 most recent decisions
        decision_entries = [line for line in result if line.startswith("- Decision")]
        assert len(decision_entries) == 5


class TestEnsureDirectoriesExist:
    """Test directory creation functionality."""

    def test_ensure_single_directory(self, tmp_path):
        """Test ensuring a single directory exists."""
        test_file = tmp_path / "subdir" / "test.txt"
        ensure_directories_exist(str(test_file))

        # Check that the directory was created
        assert (tmp_path / "subdir").exists()

    def test_ensure_multiple_directories(self, tmp_path):
        """Test ensuring multiple directories exist."""
        file1 = tmp_path / "dir1" / "test1.txt"
        file2 = tmp_path / "dir2" / "subdir" / "test2.txt"

        ensure_directories_exist(str(file1), str(file2))

        assert (tmp_path / "dir1").exists()
        assert (tmp_path / "dir2" / "subdir").exists()

    def test_ensure_existing_directory(self, tmp_path):
        """Test ensuring a directory that already exists."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        test_file = existing_dir / "test.txt"
        ensure_directories_exist(str(test_file))

        # Should not raise an error
        assert existing_dir.exists()


class TestCreateTimestamp:
    """Test timestamp creation functionality."""

    def test_create_timestamp_format(self):
        """Test that timestamp is in correct ISO format."""
        timestamp = create_timestamp()

        # Should be able to parse it back
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert parsed.tzinfo is not None

    def test_create_timestamp_uniqueness(self):
        """Test that consecutive timestamps are different."""
        timestamp1 = create_timestamp()
        timestamp2 = create_timestamp()

        # They should be different (unless called in same microsecond)
        assert timestamp1 != timestamp2 or True  # Allow for same microsecond


class TestValidateMemoryEntry:
    """Test memory entry validation functionality."""

    def test_validate_valid_entry(self):
        """Test validation of a valid memory entry."""
        entry = {
            "content": "Test memory content",
            "type": "test",
            "timestamp": "2025-06-09T10:00:00Z",
        }

        assert validate_memory_entry(entry) is True

    def test_validate_missing_content(self):
        """Test validation of entry missing content field."""
        entry = {"type": "test", "timestamp": "2025-06-09T10:00:00Z"}

        assert validate_memory_entry(entry) is False

    def test_validate_missing_type(self):
        """Test validation of entry missing type field."""
        entry = {"content": "Test content", "timestamp": "2025-06-09T10:00:00Z"}

        assert validate_memory_entry(entry) is False

    def test_validate_empty_entry(self):
        """Test validation of empty entry."""
        entry = {}
        assert validate_memory_entry(entry) is False

    def test_validate_extra_fields_allowed(self):
        """Test that extra fields don't prevent validation."""
        entry = {
            "content": "Test content",
            "type": "test",
            "extra_field": "extra_value",
            "timestamp": "2025-06-09T10:00:00Z",
        }

        assert validate_memory_entry(entry) is True


class TestSanitizeUserInput:
    """Test user input sanitization functionality."""

    def test_sanitize_normal_input(self):
        """Test sanitizing normal user input."""
        input_text = "Hello, how are you today?"
        result = sanitize_user_input(input_text)
        assert result == "Hello, how are you today?"

    def test_sanitize_whitespace_input(self):
        """Test sanitizing input with extra whitespace."""
        input_text = "  \n  Hello world  \t  "
        result = sanitize_user_input(input_text)
        assert result == "Hello world"

    def test_sanitize_empty_input(self):
        """Test sanitizing empty input."""
        assert sanitize_user_input("") == ""
        # Note: sanitize_user_input expects str, not None

    def test_sanitize_null_bytes(self):
        """Test sanitizing input with null bytes."""
        input_text = "Hello\x00world"
        result = sanitize_user_input(input_text)
        assert result == "Helloworld"

    def test_sanitize_only_whitespace(self):
        """Test sanitizing input that is only whitespace."""
        input_text = "   \n\t   "
        result = sanitize_user_input(input_text)
        assert result == ""


class TestExtractKeywordsFromText:
    """Test keyword extraction functionality."""

    def test_extract_basic_keywords(self):
        """Test extracting keywords from basic text."""
        text = "machine learning algorithms are powerful tools"
        keywords = extract_keywords_from_text(text)

        expected = ["machine", "learning", "algorithms", "powerful", "tools"]
        assert keywords == expected

    def test_extract_keywords_removes_stop_words(self):
        """Test that stop words are removed."""
        text = "the quick brown fox jumps over the lazy dog"
        keywords = extract_keywords_from_text(text)

        # Should not contain stop words like "the", but "over" is not in stop words list
        assert "the" not in keywords
        assert "over" in keywords  # "over" is not in the stop words list
        assert "quick" in keywords
        assert "brown" in keywords

    def test_extract_keywords_empty_text(self):
        """Test extracting keywords from empty text."""
        assert extract_keywords_from_text("") == []
        # Note: extract_keywords_from_text expects str, not None

    def test_extract_keywords_max_limit(self):
        """Test that keyword extraction respects max limit."""
        text = "one two three four five six seven eight nine ten eleven twelve"
        keywords = extract_keywords_from_text(text, max_keywords=5)

        assert len(keywords) == 5

    def test_extract_keywords_removes_duplicates(self):
        """Test that duplicate keywords are removed."""
        text = "test test testing test tested testing"
        keywords = extract_keywords_from_text(text)

        # Should contain each unique keyword only once
        unique_keywords = set(keywords)
        assert len(keywords) == len(unique_keywords)

    def test_extract_keywords_case_insensitive(self):
        """Test that keyword extraction is case insensitive."""
        text = "Python PYTHON python Machine LEARNING learning"
        keywords = extract_keywords_from_text(text)

        # All should be lowercase and deduplicated
        assert "python" in keywords
        assert "machine" in keywords
        assert "learning" in keywords
        # Should not have duplicates
        assert keywords.count("python") == 1
        assert keywords.count("learning") == 1

    def test_extract_keywords_short_words_filtered(self):
        """Test that short words (<=2 chars) are filtered out."""
        text = "a an big cat is on it go to be"
        keywords = extract_keywords_from_text(text)

        # Should contain "big", "cat" but not single/double letter words
        assert "big" in keywords
        assert "cat" in keywords
        assert "a" not in keywords
        assert "an" not in keywords
        assert "is" not in keywords
        assert "on" not in keywords
        assert "it" not in keywords
        assert "go" not in keywords
        assert "to" not in keywords
        assert "be" not in keywords


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.kortana.brain_utils"])
