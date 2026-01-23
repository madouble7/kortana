"""
Demonstration script for TIL (Today I Learned) feature.

This script shows how to use the TIL API programmatically without 
requiring the full server to be running. It uses an in-memory database
for demonstration purposes.
"""

import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup in-memory database for demonstration
from src.kortana.core.models import TILNote
from src.kortana.modules.til.schemas import TILNoteCreate, TILNoteUpdate
from src.kortana.modules.til.services import TILService
from src.kortana.services.database import Base


def setup_demo_db():
    """Create an in-memory database for demonstration."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def demonstrate_til_features():
    """Demonstrate TIL features with examples."""
    print("=" * 70)
    print("TIL (Today I Learned) Feature Demonstration")
    print("=" * 70)
    print()
    
    # Setup
    db = setup_demo_db()
    til_service = TILService(db)
    
    # 1. Create notes
    print("1. Creating TIL notes...")
    print("-" * 70)
    
    notes_data = [
        {
            "title": "Python List Comprehensions",
            "content": "List comprehensions in Python are not only more readable but also significantly faster than traditional for loops. They provide a concise way to create lists.",
            "category": "python",
            "tags": ["python", "performance", "tips"],
            "source": "manual"
        },
        {
            "title": "Docker Multi-Stage Builds",
            "content": "Use multi-stage builds in Docker to reduce image size. Build dependencies can be in one stage, and only the artifacts are copied to the final stage.",
            "category": "devops",
            "tags": ["docker", "optimization", "devops"],
            "source": "manual"
        },
        {
            "title": "Git Rebase Interactive",
            "content": "Use 'git rebase -i HEAD~n' to interactively edit the last n commits. This is useful for cleaning up commit history before merging.",
            "category": "git",
            "tags": ["git", "workflow", "tips"],
            "source": "manual"
        },
        {
            "title": "Quickly Organizing Ideas",
            "content": "Use a structured format: Premise, Background, Birth of the idea, Test, Related results, Discussion. This helps in quickly organizing and documenting ideas or experiments.",
            "category": "productivity",
            "tags": ["productivity", "organization", "research"],
            "source": "conversation"
        }
    ]
    
    created_notes = []
    for note_data in notes_data:
        note_create = TILNoteCreate(**note_data)
        note = til_service.create_note(note_create)
        created_notes.append(note)
        print(f"  ✓ Created: {note.title} (ID: {note.id})")
    
    print()
    
    # 2. List all notes
    print("2. Listing all notes...")
    print("-" * 70)
    all_notes = til_service.get_all_notes()
    print(f"  Total notes: {len(all_notes)}")
    for note in all_notes:
        print(f"  • [{note.category}] {note.title}")
    print()
    
    # 3. Get notes by category
    print("3. Filtering by category (python)...")
    print("-" * 70)
    python_notes = til_service.get_all_notes(category="python")
    for note in python_notes:
        print(f"  • {note.title}")
        print(f"    Tags: {json.loads(note.tags) if note.tags else []}")
    print()
    
    # 4. Search notes
    print("4. Searching for 'optimization'...")
    print("-" * 70)
    search_results = til_service.search_notes("optimization")
    for note in search_results:
        print(f"  • {note.title}")
        print(f"    Content excerpt: {note.content[:80]}...")
    print()
    
    # 5. Get categories with counts
    print("5. Categories with note counts...")
    print("-" * 70)
    categories = til_service.get_categories()
    for cat in categories:
        print(f"  • {cat['category']}: {cat['count']} note(s)")
    print()
    
    # 6. Get notes by tag
    print("6. Getting notes with 'tips' tag...")
    print("-" * 70)
    tagged_notes = til_service.get_notes_by_tag("tips")
    for note in tagged_notes:
        tags = json.loads(note.tags) if note.tags else []
        print(f"  • {note.title} (Tags: {', '.join(tags)})")
    print()
    
    # 7. Update a note
    print("7. Updating a note...")
    print("-" * 70)
    first_note = created_notes[0]
    print(f"  Original title: {first_note.title}")
    
    update_data = TILNoteUpdate(
        title="Python List Comprehensions - Updated",
        tags=["python", "performance", "tips", "beginners"]
    )
    updated_note = til_service.update_note(first_note.id, update_data)
    print(f"  Updated title: {updated_note.title}")
    print(f"  Updated tags: {json.loads(updated_note.tags)}")
    print()
    
    # 8. Get a specific note
    print("8. Retrieving a specific note...")
    print("-" * 70)
    retrieved_note = til_service.get_note_by_id(created_notes[1].id)
    print(f"  Title: {retrieved_note.title}")
    print(f"  Category: {retrieved_note.category}")
    print(f"  Created: {retrieved_note.created_at}")
    print(f"  Content: {retrieved_note.content}")
    print()
    
    # 9. Delete a note
    print("9. Deleting a note...")
    print("-" * 70)
    note_to_delete = created_notes[-1]
    print(f"  Deleting: {note_to_delete.title}")
    success = til_service.delete_note(note_to_delete.id)
    print(f"  Deleted: {success}")
    
    # Verify deletion
    remaining_notes = til_service.get_all_notes()
    print(f"  Remaining notes: {len(remaining_notes)}")
    print()
    
    # Summary
    print("=" * 70)
    print("Demonstration Complete!")
    print("=" * 70)
    print()
    print("Key Features Demonstrated:")
    print("  ✓ Create notes with categories and tags")
    print("  ✓ List and filter notes by category")
    print("  ✓ Search notes by content")
    print("  ✓ Get category statistics")
    print("  ✓ Filter by tags")
    print("  ✓ Update notes")
    print("  ✓ Delete notes")
    print()
    print("For API usage, see: docs/TIL_FEATURE_GUIDE.md")
    print("For CLI usage, run: python til_cli.py --help")
    print()
    
    db.close()


if __name__ == "__main__":
    try:
        demonstrate_til_features()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
