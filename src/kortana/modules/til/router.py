"""API router for TIL (Today I Learned) endpoints."""

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.kortana.modules.til import schemas
from src.kortana.modules.til.services import TILService
from src.kortana.services.database import get_db_sync

router = APIRouter(
    prefix="/til",
    tags=["TIL - Today I Learned"],
    responses={404: {"description": "Not found"}},
)


def _convert_tags(note):
    """Convert tags from JSON string to list for display."""
    if note.tags:
        try:
            note.tags = json.loads(note.tags)
        except json.JSONDecodeError:
            note.tags = []
    else:
        note.tags = []
    return note


@router.post("/notes", response_model=schemas.TILNoteDisplay, status_code=status.HTTP_201_CREATED)
def create_til_note(
    note_in: schemas.TILNoteCreate, db: Session = Depends(get_db_sync)
):
    """
    Create a new TIL (Today I Learned) note.

    Args:
        note_in: TIL note data
        db: Database session

    Returns:
        Created TIL note
    """
    service = TILService(db)
    db_note = service.create_note(note_create=note_in)
    return _convert_tags(db_note)


@router.get("/notes/{note_id}", response_model=schemas.TILNoteDisplay)
def get_til_note(note_id: int, db: Session = Depends(get_db_sync)):
    """
    Retrieve a specific TIL note by its ID.

    Args:
        note_id: ID of the note
        db: Database session

    Returns:
        TIL note
    """
    service = TILService(db)
    db_note = service.get_note_by_id(note_id=note_id)
    if db_note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="TIL note not found"
        )
    return _convert_tags(db_note)


@router.get("/notes", response_model=List[schemas.TILNoteDisplay])
def list_til_notes(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db_sync),
):
    """
    Retrieve a list of TIL notes with optional filtering.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        category: Optional category filter
        db: Database session

    Returns:
        List of TIL notes
    """
    service = TILService(db)
    notes = service.get_all_notes(skip=skip, limit=limit, category=category)
    return [_convert_tags(note) for note in notes]


@router.get("/search", response_model=List[schemas.TILNoteDisplay])
def search_til_notes(
    q: str = Query(..., min_length=1, description="Search term"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    db: Session = Depends(get_db_sync),
):
    """
    Search TIL notes by title or content.

    Args:
        q: Search term
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of matching TIL notes
    """
    service = TILService(db)
    notes = service.search_notes(search_term=q, skip=skip, limit=limit)
    return [_convert_tags(note) for note in notes]


@router.put("/notes/{note_id}", response_model=schemas.TILNoteDisplay)
def update_til_note(
    note_id: int,
    note_in: schemas.TILNoteUpdate,
    db: Session = Depends(get_db_sync),
):
    """
    Update a TIL note.

    Args:
        note_id: ID of the note
        note_in: Updated note data
        db: Database session

    Returns:
        Updated TIL note
    """
    service = TILService(db)
    db_note = service.update_note(note_id=note_id, note_update=note_in)
    if db_note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="TIL note not found"
        )
    return _convert_tags(db_note)


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_til_note(note_id: int, db: Session = Depends(get_db_sync)):
    """
    Delete a TIL note.

    Args:
        note_id: ID of the note
        db: Database session

    Returns:
        None (204 No Content on success)
    """
    service = TILService(db)
    success = service.delete_note(note_id=note_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="TIL note not found"
        )
    return None


@router.get("/categories", response_model=List[schemas.TILCategoryInfo])
def list_categories(db: Session = Depends(get_db_sync)):
    """
    Get all categories with note counts.

    Args:
        db: Database session

    Returns:
        List of categories with counts
    """
    service = TILService(db)
    return service.get_categories()


@router.get("/tags/{tag}", response_model=List[schemas.TILNoteDisplay])
def get_notes_by_tag(
    tag: str,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    db: Session = Depends(get_db_sync),
):
    """
    Get notes that contain a specific tag.

    Args:
        tag: Tag to search for
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of TIL notes with the tag
    """
    service = TILService(db)
    notes = service.get_notes_by_tag(tag=tag, skip=skip, limit=limit)
    return [_convert_tags(note) for note in notes]
