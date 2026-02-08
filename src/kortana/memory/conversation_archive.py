"""
Conversation Archive Manager

This module handles archiving of conversation history for long-term storage.
It manages conversation pruning, archival policies, and retrieval of archived conversations.
"""

import gzip
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _parse_timestamp(timestamp: Any) -> datetime:
    """Parse a timestamp from string or datetime object.

    Args:
        timestamp: Either a datetime object or an ISO format string

    Returns:
        datetime object

    Raises:
        ValueError: If timestamp cannot be parsed
    """
    if isinstance(timestamp, str):
        # Handle various timestamp formats
        # First try with 'Z' suffix (common UTC format)
        timestamp_str = timestamp.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(timestamp_str)
        except ValueError:
            # If that fails, try other common formats
            # This is a simple fallback - for production, consider using dateutil.parser
            try:
                return datetime.fromisoformat(timestamp)
            except ValueError:
                raise ValueError(f"Unable to parse timestamp: {timestamp}")
    elif isinstance(timestamp, datetime):
        return timestamp
    else:
        raise ValueError(f"Invalid timestamp type: {type(timestamp)}")


class ConversationArchive:
    """Manager for archiving conversation history."""

    def __init__(
        self,
        archive_dir: str,
        max_active_conversations: int = 100,
        archive_after_days: int = 30,
        compress_archives: bool = True,
    ):
        """Initialize the conversation archive manager.

        Args:
            archive_dir: Directory to store archived conversations
            max_active_conversations: Maximum number of active conversations before archiving
            archive_after_days: Archive conversations older than this many days
            compress_archives: Whether to compress archived conversations
        """
        self.archive_dir = Path(archive_dir)
        self.max_active_conversations = max_active_conversations
        self.archive_after_days = archive_after_days
        self.compress_archives = compress_archives

        # Ensure archive directory exists
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"ConversationArchive initialized: archive_dir={archive_dir}, "
            f"max_active={max_active_conversations}, archive_after={archive_after_days}d"
        )

    def should_archive(self, conversation_timestamp: datetime) -> bool:
        """Check if a conversation should be archived based on age.

        Args:
            conversation_timestamp: The timestamp of the conversation

        Returns:
            True if the conversation should be archived
        """
        age = datetime.now() - conversation_timestamp
        return age > timedelta(days=self.archive_after_days)

    def archive_conversation(
        self,
        conversation_id: str,
        conversation_data: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Archive a conversation.

        Args:
            conversation_id: Unique identifier for the conversation
            conversation_data: The conversation data to archive
            metadata: Optional metadata about the conversation

        Returns:
            True if archiving was successful
        """
        try:
            # Create a subdirectory for the year-month
            timestamp = _parse_timestamp(
                conversation_data.get("timestamp", datetime.now())
            )

            year_month = timestamp.strftime("%Y-%m")
            archive_subdir = self.archive_dir / year_month
            archive_subdir.mkdir(parents=True, exist_ok=True)

            # Prepare archive data
            archive_data = {
                "conversation_id": conversation_id,
                "archived_at": datetime.now().isoformat(),
                "metadata": metadata or {},
                "conversation": conversation_data,
            }

            # Determine file path
            file_name = f"{conversation_id}.json"
            if self.compress_archives:
                file_name += ".gz"

            file_path = archive_subdir / file_name

            # Write the archive
            if self.compress_archives:
                with gzip.open(file_path, "wt", encoding="utf-8") as f:
                    json.dump(archive_data, f, indent=2)
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(archive_data, f, indent=2)

            logger.info(f"Archived conversation {conversation_id} to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to archive conversation {conversation_id}: {e}")
            return False

    def retrieve_archived_conversation(
        self, conversation_id: str, year_month: str | None = None
    ) -> dict[str, Any] | None:
        """Retrieve an archived conversation.

        Args:
            conversation_id: The conversation ID to retrieve
            year_month: Optional year-month string (YYYY-MM) to narrow search

        Returns:
            The archived conversation data or None if not found
        """
        try:
            # Search strategy: if year_month provided, search there first
            search_dirs = []
            if year_month:
                search_dirs.append(self.archive_dir / year_month)

            # Also search all subdirectories
            search_dirs.extend(self.archive_dir.iterdir())

            for subdir in search_dirs:
                if not subdir.is_dir():
                    continue

                # Try both compressed and uncompressed
                for ext in [".json.gz", ".json"]:
                    file_path = subdir / f"{conversation_id}{ext}"
                    if file_path.exists():
                        if ext == ".json.gz":
                            with gzip.open(file_path, "rt", encoding="utf-8") as f:
                                data = json.load(f)
                        else:
                            with open(file_path, encoding="utf-8") as f:
                                data = json.load(f)

                        logger.info(f"Retrieved archived conversation {conversation_id}")
                        return data

            logger.warning(f"Archived conversation {conversation_id} not found")
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve archived conversation {conversation_id}: {e}")
            return None

    def prune_old_conversations(
        self, active_conversations: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], int]:
        """Prune old conversations by archiving them.

        Args:
            active_conversations: List of active conversation entries

        Returns:
            Tuple of (remaining active conversations, number archived)
        """
        try:
            archived_count = 0
            remaining_conversations = []

            for conv in active_conversations:
                timestamp_value = conv.get("timestamp")
                if timestamp_value is None:
                    # If no valid timestamp, keep it active
                    remaining_conversations.append(conv)
                    continue

                try:
                    timestamp = _parse_timestamp(timestamp_value)
                except (ValueError, TypeError):
                    # If parsing fails, keep it active
                    remaining_conversations.append(conv)
                    continue

                if self.should_archive(timestamp):
                    # Archive this conversation
                    conv_id = conv.get("id", f"conv_{timestamp.isoformat()}")
                    metadata = {
                        "role": conv.get("role"),
                        "tags": conv.get("tags", []),
                        "original_timestamp": timestamp.isoformat(),
                    }

                    if self.archive_conversation(conv_id, conv, metadata):
                        archived_count += 1
                    else:
                        # If archiving fails, keep it active
                        remaining_conversations.append(conv)
                else:
                    remaining_conversations.append(conv)

            logger.info(
                f"Pruned {archived_count} conversations, {len(remaining_conversations)} remain active"
            )
            return remaining_conversations, archived_count

        except Exception as e:
            logger.error(f"Error during conversation pruning: {e}")
            return active_conversations, 0

    def get_archive_statistics(self) -> dict[str, Any]:
        """Get statistics about the conversation archive.

        Returns:
            Dictionary with archive statistics
        """
        try:
            total_archives = 0
            total_size_bytes = 0
            archives_by_month: dict[str, int] = {}

            for subdir in self.archive_dir.iterdir():
                if not subdir.is_dir():
                    continue

                month_count = 0
                for file_path in subdir.iterdir():
                    if file_path.is_file():
                        # Use suffixes for more reliable extension checking
                        # .suffixes returns ['.json'] for 'file.json' and ['.json', '.gz'] for 'file.json.gz'
                        suffixes = file_path.suffixes
                        if ".json" in suffixes or (len(suffixes) >= 2 and suffixes[-2:] == [".json", ".gz"]):
                            total_archives += 1
                            month_count += 1
                            total_size_bytes += file_path.stat().st_size

                if month_count > 0:
                    archives_by_month[subdir.name] = month_count

            return {
                "total_archived_conversations": total_archives,
                "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
                "archives_by_month": archives_by_month,
                "archive_directory": str(self.archive_dir),
            }

        except Exception as e:
            logger.error(f"Error getting archive statistics: {e}")
            return {
                "error": str(e),
                "archive_directory": str(self.archive_dir),
            }
