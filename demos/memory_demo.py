#!/usr/bin/env python
"""
Kor'tana Memory System Demo

This script demonstrates how to use the Kor'tana memory system
for storing and retrieving different types of memories.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config
from kortana.memory.memory import (
    get_memory_by_type,
    get_recent_memories_by_type,
    load_memory,
    save_context_summary,
    save_decision,
    save_implementation_note,
    save_project_insight,
)


def main():
    """Run a demo of Kor'tana's memory system."""
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger("memory_demo")

    logger.info("\n🧠 Kor'tana Memory System Demo 🧠\n")

    try:
        # Load configuration
        settings = load_config()

        # Load existing memories
        memories = load_memory()
        logger.info(f"Loaded {len(memories)} existing memories")

        # Save new memories of different types
        timestamp = datetime.now().isoformat()

        # Save a decision
        save_decision(
            decision="Implemented configurable memory threshold for summarization",
            context="During the memory system demo, we tested different threshold values",
            reasoning="A configurable threshold allows for adaptive memory management",
        )
        logger.info("✅ Saved a new decision")

        # Save an implementation note
        save_implementation_note(
            note="Memory system now uses a vector store for semantic search",
            details="Integrated with Pinecone for vector storage and similarity search",
            components=["memory_manager.py", "memory.py", "vector_store.py"],
        )
        logger.info("✅ Saved an implementation note")

        # Save a project insight
        save_project_insight(
            insight="Auto-summarization improves context management for long conversations",
            impact="Reduces token usage and maintains coherence in extended dialogues",
            next_steps="Test with different summarization strategies",
        )
        logger.info("✅ Saved a project insight")

        # Save a context summary
        save_context_summary(
            summary="Memory system demo showed successful integration of vector search",
            key_points=["Vector search worked well", "Processing time was acceptable"],
            source="Memory demo script",
        )
        logger.info("✅ Saved a context summary")

        # Reload memories to see the new ones
        updated_memories = load_memory()
        logger.info(
            f"\nNow have {len(updated_memories)} memories (added {len(updated_memories) - len(memories)} new ones)"
        )

        # Demonstrate retrieving memories by type
        decisions = get_memory_by_type(updated_memories, "decision")
        logger.info(f"\nFound {len(decisions)} decisions in memory")
        if decisions:
            logger.info(f"Latest decision: {decisions[-1]['decision']}")

        # Demonstrate retrieving recent memories
        recent_notes = get_recent_memories_by_type(
            updated_memories, "implementation_note", limit=2
        )
        logger.info(f"\nFound {len(recent_notes)} recent implementation notes")
        for note in recent_notes:
            logger.info(f"- {note['note']}")

        logger.info("\n🎉 Memory system demo completed successfully!")

    except Exception as e:
        logger.error(f"Error in memory demo: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
