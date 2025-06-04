#!/usr/bin/env python
"""
Kor'tana Memory CLI Tool

A command line interface for adding entries to project memory.
"""

import argparse
import os
import sys

from kortana.core.memory import (
    save_context_summary,
    save_decision,
    save_implementation_note,
    save_project_insight,
)

# Add the parent directory (src/) to sys.path to allow importing from core
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

# Import the memory helper functions


def main() -> None:
    """
    Main entry point for the memory CLI tool.

    Parses command line arguments and executes the appropriate command
    to save different types of memory entries.
    """
    parser = argparse.ArgumentParser(
        description="Kor'tana Project Memory CLI tool",
        formatter_class=argparse.RawTextHelpFormatter,  # Preserve newlines in help
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- Add command ---
    add_parser = subparsers.add_parser("add", help="Add a new memory entry")
    add_parser.add_argument(
        "type",
        choices=[
            "decision",
            "context_summary",
            "implementation_note",
            "project_insight",
        ],
        help="Type of memory entry",
    )
    add_parser.add_argument("content", help="Content of the memory entry")

    # --- List command ---
    # The list command is currently causing syntax errors and is being removed.
    # list_parser = subparsers.add_parser('list', help='List memory entries')
    # list_parser.add_argument(
    #     'type',
    #     choices=['decision', 'context_summary', 'implementation_note', 'project_insight', 'all'],
    #     help='Type of memory entries to list (or 'all')'
    # )
    # list_parser.add_argument(
    #     '-n', '--limit',
    #     type=int,
    #     default=5,
    #     help='Number of recent entries to list (default: 5). Ignored if type is 'all'.'
    # )

    args = parser.parse_args()

    if args.command == "add":
        if args.type == "decision":
            save_decision(args.content)
        elif args.type == "context_summary":
            save_context_summary(args.content)
        elif args.type == "implementation_note":
            save_implementation_note(args.content)
        elif args.type == "project_insight":
            save_project_insight(args.content)
        print(f"Successfully added {args.type} entry.")

    # elif args.command == 'list':
    #     if args.type == 'all':
    #         all_memories = load_memory()
    #         if not all_memories:
    #             print('No memory entries found.')
    #             return
    #         print('-- All Memory Entries --')
    #         for entry in all_memories:
    #             print(f"[{entry.get('timestamp', 'N/A')}] ({entry.get('type', 'unknown')}): {entry.get('content', '[empty]')[:100]}...") # Truncate for display
    #     else:
    #         recent_memories = get_recent_memories_by_type(args.type, limit=args.limit)
    #         if not recent_memories:
    #             print(f'No recent {args.type} entries found.')
    #             return
    #         print(f'-- Recent {args.type.capitalize()} Entries (--limit {args.limit}) --')
    #         for entry in recent_memories:
    # print(f"[{entry.get('timestamp', 'N/A')}] {entry.get('content',
    # '[empty]')[:100]}...") # Truncate for display

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
    main()
