#!/usr/bin/env python3
"""
CLI tool for creating Today I Learned (TIL) notes in Kor'tana.

Features:
    1. Opens an editor to create the note
    2. Provides command line options to specify categories and tags
    3. Saves note to Kor'tana database via API or direct DB access
"""

import argparse
import json
import os
import sys
import tempfile
from subprocess import call
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Add parent directory to path to import kortana modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.kortana.core.models import TILNote
from src.kortana.modules.til.schemas import TILNoteCreate
from src.kortana.modules.til.services import TILService
from src.kortana.services.database import get_database_url

EDITOR = os.environ.get("EDITOR", "vim")


def get_db_session() -> Session:
    """Get a database session."""
    database_url = get_database_url()
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def list_categories(db: Session) -> list[str]:
    """Given a database session, return the list of available categories."""
    service = TILService(db)
    categories_info = service.get_categories()
    return [cat["category"] for cat in categories_info]


def create_til_note(category: str, tags: Optional[list[str]] = None, db: Session = None):
    """Create a TIL note using an editor.

    Args:
        category: Category for the note
        tags: Optional list of tags
        db: Database session
    """
    if db is None:
        db = get_db_session()

    # Create temporary file with markdown header template
    tf = tempfile.NamedTemporaryFile(mode="w+", suffix=".md", delete=False)
    tf.write("## ")
    tf.close()

    # Get pre-edit file size
    pre_size = os.path.getsize(tf.name)

    # Open editor
    call([EDITOR, tf.name])

    # Get post-edit file size
    post_size = os.path.getsize(tf.name)

    # Check if user made meaningful changes
    if abs(pre_size - post_size) < 10:
        print("Note discarded (no meaningful content). Exiting.")
        os.unlink(tf.name)
        return

    # Read the note content
    with open(tf.name, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract title from first line (markdown header)
    lines = content.split("\n")
    title_line = lines[0] if lines else "## Untitled"
    title = title_line.strip("#").strip()

    # Remove backticks and sanitize title
    title = title.replace("`", "")

    if not title:
        title = "Untitled TIL Note"

    # Rest is content
    note_content = "\n".join(lines[1:]).strip() if len(lines) > 1 else content

    try:
        # Create note in database
        service = TILService(db)
        note_create = TILNoteCreate(
            title=title,
            content=note_content,
            category=category,
            tags=tags or [],
            source="cli",
        )
        db_note = service.create_note(note_create=note_create)

        print(f"✓ TIL note created successfully!")
        print(f"  ID: {db_note.id}")
        print(f"  Title: {title}")
        print(f"  Category: {category}")
        if tags:
            print(f"  Tags: {', '.join(tags)}")

        # Clean up temp file
        os.unlink(tf.name)

    except Exception as e:
        print(f"Error creating note: {e}")
        print(f"Note content saved at: {tf.name}")
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Create a Today I Learned (TIL) note in Kor'tana."
    )

    parser.add_argument(
        "-c",
        "--category",
        help="Category of the note (e.g., python, productivity, algorithms)",
        default="unclassified",
    )
    parser.add_argument(
        "-t",
        "--tags",
        help="Comma-separated tags for the note",
        default="",
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List all existing categories",
    )

    args = parser.parse_args()

    # Get database session
    try:
        db = get_db_session()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        print("Make sure the database is initialized and accessible.")
        sys.exit(1)

    # List categories if requested
    if args.list_categories:
        print("Existing categories:")
        categories = list_categories(db)
        if categories:
            for cat in categories:
                print(f"  - {cat}")
        else:
            print("  (no categories yet)")
        db.close()
        return

    # Process tags
    tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]

    # Handle category selection
    category = args.category
    if category == "unclassified":
        print("Category not specified (use -c/--category).")
        response = input("Save to 'unclassified'? y/[n] ")
        if response.lower() != "y":
            print("\nExisting categories:")
            categories = list_categories(db)
            if categories:
                for cat in categories:
                    print(f"  - {cat}")
            else:
                print("  (no categories yet)")
            category = input("\nEnter category name: ").strip()
            if not category:
                print("Category required. Exiting.")
                db.close()
                sys.exit(1)

    # Create the note
    create_til_note(category=category, tags=tags, db=db)
    db.close()


if __name__ == "__main__":
    main()
