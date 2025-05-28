#!/usr/bin/env python
"""
Simple script to add entries to Kor'tana's project memory.

Usage:
    python scripts/add_project_memory_entry.py <type> <content>

Example:
    python scripts/add_project_memory_entry.py decision "Decided to prioritize persona development."
    python scripts/add_project_memory_entry.py implementation_note "Added automatic summarization trigger in brain.py."
"""

import sys
import os
import argparse

# Add the src/ directory to sys.path to allow importing core.memory
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import the memory helper functions
from core.memory import save_decision, save_context_summary, save_implementation_note, save_project_insight

def main():
    parser = argparse.ArgumentParser(
        description='Add an entry to Kor\'tana\'s project memory.',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'type',
        choices=['decision', 'context_summary', 'implementation_note', 'project_insight'],
        help='Type of memory entry'
    )
    parser.add_argument('content', help='Content of the memory entry')

    args = parser.parse_args()

    try:
        if args.type == 'decision':
            save_decision(args.content)
        elif args.type == 'context_summary':
            save_context_summary(args.content)
        elif args.type == 'implementation_note':
            save_implementation_note(args.content)
        elif args.type == 'project_insight':
            save_project_insight(args.content)

        print(f'Successfully added {args.type} entry: "{args.content[:50]}..."')

    except Exception as e:
        print(f'Error adding memory entry: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main() 