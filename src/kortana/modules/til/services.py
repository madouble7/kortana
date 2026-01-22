"""Service layer for TIL (Today I Learned) operations."""

import json
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.kortana.core.models import TILNote
from src.kortana.modules.til.schemas import TILNoteCreate, TILNoteUpdate


class TILService:
    """Service for managing TIL notes."""

    def __init__(self, db: Session):
        """Initialize the TIL service.

        Args:
            db: Database session
        """
        self.db = db

    def create_note(self, note_create: TILNoteCreate) -> TILNote:
        """Create a new TIL note.

        Args:
            note_create: Data for creating the note

        Returns:
            Created TIL note
        """
        # Convert tags list to JSON string for storage
        tags_json = json.dumps(note_create.tags) if note_create.tags else None

        db_note = TILNote(
            title=note_create.title,
            content=note_create.content,
            category=note_create.category,
            tags=tags_json,
            source=note_create.source,
        )
        self.db.add(db_note)
        self.db.commit()
        self.db.refresh(db_note)
        return db_note

    def get_note_by_id(self, note_id: int) -> Optional[TILNote]:
        """Get a TIL note by ID.

        Args:
            note_id: ID of the note to retrieve

        Returns:
            TIL note if found, None otherwise
        """
        return self.db.query(TILNote).filter(TILNote.id == note_id).first()

    def get_all_notes(
        self, skip: int = 0, limit: int = 100, category: Optional[str] = None
    ) -> List[TILNote]:
        """Get all TIL notes with optional filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            category: Optional category filter

        Returns:
            List of TIL notes
        """
        query = self.db.query(TILNote)
        if category:
            query = query.filter(TILNote.category == category)
        return query.order_by(TILNote.created_at.desc()).offset(skip).limit(limit).all()

    def search_notes(self, search_term: str, skip: int = 0, limit: int = 100) -> List[TILNote]:
        """Search TIL notes by title or content.

        Args:
            search_term: Term to search for
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching TIL notes
        """
        search_pattern = f"%{search_term}%"
        query = self.db.query(TILNote).filter(
            (TILNote.title.ilike(search_pattern)) | (TILNote.content.ilike(search_pattern))
        )
        return query.order_by(TILNote.created_at.desc()).offset(skip).limit(limit).all()

    def update_note(self, note_id: int, note_update: TILNoteUpdate) -> Optional[TILNote]:
        """Update a TIL note.

        Args:
            note_id: ID of the note to update
            note_update: Data to update

        Returns:
            Updated TIL note if found, None otherwise
        """
        db_note = self.get_note_by_id(note_id)
        if not db_note:
            return None

        update_data = note_update.model_dump(exclude_unset=True)

        # Convert tags list to JSON string if present
        if "tags" in update_data and update_data["tags"] is not None:
            update_data["tags"] = json.dumps(update_data["tags"])

        for field, value in update_data.items():
            setattr(db_note, field, value)

        self.db.commit()
        self.db.refresh(db_note)
        return db_note

    def delete_note(self, note_id: int) -> bool:
        """Delete a TIL note.

        Args:
            note_id: ID of the note to delete

        Returns:
            True if deleted, False if not found
        """
        db_note = self.get_note_by_id(note_id)
        if not db_note:
            return False

        self.db.delete(db_note)
        self.db.commit()
        return True

    def get_categories(self) -> List[dict]:
        """Get all categories with note counts.

        Returns:
            List of dictionaries with category and count
        """
        results = (
            self.db.query(TILNote.category, func.count(TILNote.id).label("count"))
            .group_by(TILNote.category)
            .order_by(TILNote.category)
            .all()
        )
        return [{"category": row.category, "count": row.count} for row in results]

    def get_notes_by_tag(self, tag: str, skip: int = 0, limit: int = 100) -> List[TILNote]:
        """Get notes that contain a specific tag.

        Args:
            tag: Tag to search for
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of TIL notes with the tag
        """
        # Search for tag in the JSON string
        tag_pattern = f'%"{tag}"%'
        query = self.db.query(TILNote).filter(TILNote.tags.ilike(tag_pattern))
        return query.order_by(TILNote.created_at.desc()).offset(skip).limit(limit).all()
