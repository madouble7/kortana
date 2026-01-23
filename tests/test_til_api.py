"""Integration tests for TIL API endpoints."""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.kortana.core.models import TILNote
from src.kortana.main import app
from src.kortana.services.database import Base, get_db_sync


# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db_sync] = override_get_db

client = TestClient(app)


def test_create_til_note_api():
    """Test creating a TIL note via API."""
    response = client.post(
        "/til/notes",
        json={
            "title": "Test API Note",
            "content": "This is a test note created via API",
            "category": "testing",
            "tags": ["test", "api"],
            "source": "api_test",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test API Note"
    assert data["category"] == "testing"
    assert "test" in data["tags"]
    assert "id" in data
    assert "created_at" in data


def test_get_til_note_api():
    """Test retrieving a TIL note via API."""
    # Create a note first
    create_response = client.post(
        "/til/notes",
        json={
            "title": "Note to Retrieve",
            "content": "Content",
            "category": "test",
        },
    )
    note_id = create_response.json()["id"]
    
    # Retrieve it
    response = client.get(f"/til/notes/{note_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == note_id
    assert data["title"] == "Note to Retrieve"


def test_get_til_note_not_found():
    """Test retrieving non-existent note returns 404."""
    response = client.get("/til/notes/99999")
    assert response.status_code == 404


def test_list_til_notes_api():
    """Test listing TIL notes via API."""
    # Create some notes
    for i in range(3):
        client.post(
            "/til/notes",
            json={
                "title": f"List Test Note {i}",
                "content": f"Content {i}",
                "category": "test",
            },
        )
    
    # List notes
    response = client.get("/til/notes")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3


def test_list_til_notes_with_category_filter():
    """Test listing notes with category filter."""
    # Create notes in different categories
    client.post(
        "/til/notes",
        json={
            "title": "Python Note",
            "content": "About Python",
            "category": "python",
        },
    )
    client.post(
        "/til/notes",
        json={
            "title": "JavaScript Note",
            "content": "About JS",
            "category": "javascript",
        },
    )
    
    # Filter by python category
    response = client.get("/til/notes?category=python")
    
    assert response.status_code == 200
    data = response.json()
    # Check at least one python note exists
    python_notes = [n for n in data if n["category"] == "python"]
    assert len(python_notes) >= 1


def test_search_til_notes_api():
    """Test searching TIL notes via API."""
    # Create searchable notes
    client.post(
        "/til/notes",
        json={
            "title": "Search Test",
            "content": "This note contains unique_search_term",
            "category": "test",
        },
    )
    
    # Search for it
    response = client.get("/til/search?q=unique_search_term")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "unique_search_term" in data[0]["content"]


def test_update_til_note_api():
    """Test updating a TIL note via API."""
    # Create a note
    create_response = client.post(
        "/til/notes",
        json={
            "title": "Original Title",
            "content": "Original content",
            "category": "test",
        },
    )
    note_id = create_response.json()["id"]
    
    # Update it
    response = client.put(
        f"/til/notes/{note_id}",
        json={
            "title": "Updated Title",
            "content": "Updated content",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["content"] == "Updated content"


def test_delete_til_note_api():
    """Test deleting a TIL note via API."""
    # Create a note
    create_response = client.post(
        "/til/notes",
        json={
            "title": "To Delete",
            "content": "Will be deleted",
            "category": "test",
        },
    )
    note_id = create_response.json()["id"]
    
    # Delete it
    response = client.delete(f"/til/notes/{note_id}")
    
    assert response.status_code == 204
    
    # Verify it's gone
    get_response = client.get(f"/til/notes/{note_id}")
    assert get_response.status_code == 404


def test_get_categories_api():
    """Test getting categories via API."""
    # Create notes in different categories
    client.post(
        "/til/notes",
        json={"title": "Note 1", "content": "Content", "category": "cat1"},
    )
    client.post(
        "/til/notes",
        json={"title": "Note 2", "content": "Content", "category": "cat2"},
    )
    
    response = client.get("/til/categories")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_get_notes_by_tag_api():
    """Test getting notes by tag via API."""
    # Create notes with tags
    client.post(
        "/til/notes",
        json={
            "title": "Tagged Note",
            "content": "Content",
            "category": "test",
            "tags": ["test_tag", "other"],
        },
    )
    
    response = client.get("/til/tags/test_tag")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "test_tag" in data[0]["tags"]
