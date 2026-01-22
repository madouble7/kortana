"""Tests for TIL (Today I Learned) module."""

import json
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.kortana.core.models import TILNote
from src.kortana.modules.til.schemas import TILNoteCreate, TILNoteUpdate
from src.kortana.modules.til.services import TILService
from src.kortana.services.database import Base


@pytest.fixture
def db_session():
    """Create a test database session."""
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def til_service(db_session):
    """Create a TIL service instance."""
    return TILService(db_session)


def test_create_note(til_service):
    """Test creating a TIL note."""
    note_create = TILNoteCreate(
        title="Test TIL Note",
        content="This is a test note about something I learned today.",
        category="testing",
        tags=["test", "learning"],
        source="manual",
    )

    note = til_service.create_note(note_create)

    assert note.id is not None
    assert note.title == "Test TIL Note"
    assert note.content == "This is a test note about something I learned today."
    assert note.category == "testing"
    assert note.source == "manual"
    
    # Tags should be stored as JSON string
    assert note.tags is not None
    tags = json.loads(note.tags)
    assert "test" in tags
    assert "learning" in tags


def test_get_note_by_id(til_service):
    """Test retrieving a note by ID."""
    # Create a note first
    note_create = TILNoteCreate(
        title="Sample Note",
        content="Sample content",
        category="sample",
    )
    created_note = til_service.create_note(note_create)

    # Retrieve it
    retrieved_note = til_service.get_note_by_id(created_note.id)

    assert retrieved_note is not None
    assert retrieved_note.id == created_note.id
    assert retrieved_note.title == "Sample Note"


def test_get_note_by_id_not_found(til_service):
    """Test retrieving a non-existent note."""
    note = til_service.get_note_by_id(99999)
    assert note is None


def test_get_all_notes(til_service):
    """Test getting all notes."""
    # Create multiple notes
    for i in range(5):
        note_create = TILNoteCreate(
            title=f"Note {i}",
            content=f"Content {i}",
            category="test",
        )
        til_service.create_note(note_create)

    # Get all notes
    notes = til_service.get_all_notes(limit=10)

    assert len(notes) == 5
    # Notes should be in descending order by created_at
    assert notes[0].title == "Note 4"


def test_get_all_notes_with_category_filter(til_service):
    """Test getting notes filtered by category."""
    # Create notes in different categories
    for i in range(3):
        note_create = TILNoteCreate(
            title=f"Python Note {i}",
            content=f"Python content {i}",
            category="python",
        )
        til_service.create_note(note_create)

    for i in range(2):
        note_create = TILNoteCreate(
            title=f"Productivity Note {i}",
            content=f"Productivity content {i}",
            category="productivity",
        )
        til_service.create_note(note_create)

    # Get only python notes
    python_notes = til_service.get_all_notes(category="python")

    assert len(python_notes) == 3
    for note in python_notes:
        assert note.category == "python"


def test_search_notes(til_service):
    """Test searching notes by content."""
    # Create notes with searchable content
    note_create_1 = TILNoteCreate(
        title="Python Tips",
        content="Use list comprehensions for better performance",
        category="python",
    )
    til_service.create_note(note_create_1)

    note_create_2 = TILNoteCreate(
        title="Docker Tips",
        content="Use multi-stage builds to reduce image size",
        category="devops",
    )
    til_service.create_note(note_create_2)

    # Search for "performance"
    results = til_service.search_notes("performance")
    assert len(results) == 1
    assert "performance" in results[0].content.lower()

    # Search for "tips" (in title)
    results = til_service.search_notes("tips")
    assert len(results) == 2


def test_update_note(til_service):
    """Test updating a note."""
    # Create a note
    note_create = TILNoteCreate(
        title="Original Title",
        content="Original content",
        category="test",
    )
    created_note = til_service.create_note(note_create)

    # Update it
    note_update = TILNoteUpdate(
        title="Updated Title",
        content="Updated content",
    )
    updated_note = til_service.update_note(created_note.id, note_update)

    assert updated_note is not None
    assert updated_note.title == "Updated Title"
    assert updated_note.content == "Updated content"
    assert updated_note.category == "test"  # Should remain unchanged


def test_update_note_not_found(til_service):
    """Test updating a non-existent note."""
    note_update = TILNoteUpdate(title="New Title")
    result = til_service.update_note(99999, note_update)
    assert result is None


def test_delete_note(til_service):
    """Test deleting a note."""
    # Create a note
    note_create = TILNoteCreate(
        title="To Be Deleted",
        content="This will be deleted",
        category="test",
    )
    created_note = til_service.create_note(note_create)

    # Delete it
    success = til_service.delete_note(created_note.id)
    assert success is True

    # Verify it's gone
    deleted_note = til_service.get_note_by_id(created_note.id)
    assert deleted_note is None


def test_delete_note_not_found(til_service):
    """Test deleting a non-existent note."""
    success = til_service.delete_note(99999)
    assert success is False


def test_get_categories(til_service):
    """Test getting categories with counts."""
    # Create notes in different categories
    for i in range(3):
        note_create = TILNoteCreate(
            title=f"Python Note {i}",
            content=f"Content {i}",
            category="python",
        )
        til_service.create_note(note_create)

    for i in range(2):
        note_create = TILNoteCreate(
            title=f"Productivity Note {i}",
            content=f"Content {i}",
            category="productivity",
        )
        til_service.create_note(note_create)

    note_create = TILNoteCreate(
        title="Docker Note",
        content="Content",
        category="devops",
    )
    til_service.create_note(note_create)

    # Get categories
    categories = til_service.get_categories()

    assert len(categories) == 3
    
    # Find specific categories
    python_cat = next(c for c in categories if c["category"] == "python")
    assert python_cat["count"] == 3

    productivity_cat = next(c for c in categories if c["category"] == "productivity")
    assert productivity_cat["count"] == 2

    devops_cat = next(c for c in categories if c["category"] == "devops")
    assert devops_cat["count"] == 1


def test_get_notes_by_tag(til_service):
    """Test getting notes by tag."""
    # Create notes with tags
    note_create_1 = TILNoteCreate(
        title="Python Note",
        content="About Python",
        category="python",
        tags=["python", "programming", "tips"],
    )
    til_service.create_note(note_create_1)

    note_create_2 = TILNoteCreate(
        title="JavaScript Note",
        content="About JavaScript",
        category="javascript",
        tags=["javascript", "programming", "tips"],
    )
    til_service.create_note(note_create_2)

    note_create_3 = TILNoteCreate(
        title="Productivity Note",
        content="About productivity",
        category="productivity",
        tags=["productivity", "tips"],
    )
    til_service.create_note(note_create_3)

    # Search for notes with "programming" tag
    programming_notes = til_service.get_notes_by_tag("programming")
    assert len(programming_notes) == 2

    # Search for notes with "tips" tag
    tips_notes = til_service.get_notes_by_tag("tips")
    assert len(tips_notes) == 3

    # Search for notes with "python" tag
    python_notes = til_service.get_notes_by_tag("python")
    assert len(python_notes) == 1
