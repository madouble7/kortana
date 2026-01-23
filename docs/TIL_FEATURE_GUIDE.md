# TIL (Today I Learned) Feature Guide

## Overview

The TIL (Today I Learned) feature in Kor'tana provides a structured note-taking system for capturing quick knowledge snippets, tips, and insights. Inspired by the [raivivek/til](https://github.com/raivivek/til) repository, this system allows you to organize and retrieve your learnings efficiently.

## Key Features

- **Categorized Notes**: Organize notes by category (e.g., python, productivity, algorithms)
- **Tagging System**: Add multiple tags to notes for flexible organization
- **Full-Text Search**: Search notes by title or content
- **REST API**: Full CRUD operations via HTTP endpoints
- **CLI Tool**: Quick note creation from the command line
- **Memory Integration**: Connect notes with Kor'tana's memory system

## Quick Start

### Creating a Note via CLI

The fastest way to create a TIL note is using the CLI tool:

```bash
# Create a note with category
python til_cli.py -c python -t "tips,performance"

# List existing categories
python til_cli.py --list-categories

# Create a note and select category interactively
python til_cli.py
```

The CLI will open your default editor (set via `EDITOR` environment variable, defaults to `vim`) where you can write your note in Markdown format:

```markdown
## Using list comprehensions for better performance

List comprehensions in Python are not only more readable but also significantly faster than traditional for loops...
```

### Creating a Note via API

You can also create notes programmatically via the REST API:

```bash
curl -X POST "http://localhost:8000/til/notes" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Python List Comprehensions",
    "content": "List comprehensions are faster than loops...",
    "category": "python",
    "tags": ["python", "performance", "tips"],
    "source": "manual"
  }'
```

## API Endpoints

### Create Note
- **POST** `/til/notes`
- Body: `TILNoteCreate` schema
- Returns: Created note with ID and timestamps

### Get Note by ID
- **GET** `/til/notes/{note_id}`
- Returns: Single note or 404

### List Notes
- **GET** `/til/notes?category={category}&skip={skip}&limit={limit}`
- Query params:
  - `category` (optional): Filter by category
  - `skip` (default: 0): Pagination offset
  - `limit` (default: 100): Max results
- Returns: List of notes

### Search Notes
- **GET** `/til/search?q={query}&skip={skip}&limit={limit}`
- Query params:
  - `q` (required): Search term
  - `skip`, `limit`: Pagination
- Returns: List of matching notes

### Update Note
- **PUT** `/til/notes/{note_id}`
- Body: `TILNoteUpdate` schema (partial updates allowed)
- Returns: Updated note

### Delete Note
- **DELETE** `/til/notes/{note_id}`
- Returns: 204 No Content on success

### List Categories
- **GET** `/til/categories`
- Returns: List of categories with note counts

### Get Notes by Tag
- **GET** `/til/tags/{tag}?skip={skip}&limit={limit}`
- Returns: List of notes containing the tag

## Data Schema

### TILNoteCreate
```json
{
  "title": "string (required, max 255 chars)",
  "content": "string (required)",
  "category": "string (required, max 100 chars)",
  "tags": ["string", "..."] (optional),
  "source": "string (default: 'manual')"
}
```

### TILNoteDisplay
```json
{
  "id": "integer",
  "title": "string",
  "content": "string",
  "category": "string",
  "tags": ["string", "..."],
  "source": "string",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)"
}
```

## Usage Examples

### Python Client Example

```python
import requests

API_BASE = "http://localhost:8000"

# Create a note
response = requests.post(
    f"{API_BASE}/til/notes",
    json={
        "title": "Docker Multi-Stage Builds",
        "content": "Use multi-stage builds to reduce image size...",
        "category": "devops",
        "tags": ["docker", "optimization"],
    }
)
note = response.json()
print(f"Created note ID: {note['id']}")

# Search for notes
response = requests.get(f"{API_BASE}/til/search?q=docker")
notes = response.json()
print(f"Found {len(notes)} notes about docker")

# List categories
response = requests.get(f"{API_BASE}/til/categories")
categories = response.json()
for cat in categories:
    print(f"Category: {cat['category']} ({cat['count']} notes)")
```

### JavaScript/TypeScript Example

```typescript
const API_BASE = 'http://localhost:8000';

// Create a note
const createNote = async () => {
  const response = await fetch(`${API_BASE}/til/notes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: 'TypeScript Tips',
      content: 'Use type guards for safer type narrowing...',
      category: 'typescript',
      tags: ['typescript', 'tips'],
    }),
  });
  const note = await response.json();
  console.log('Created note:', note);
};

// Get notes by category
const getNotesByCategory = async (category: string) => {
  const response = await fetch(
    `${API_BASE}/til/notes?category=${category}`
  );
  const notes = await response.json();
  return notes;
};
```

## Best Practices

1. **Use Descriptive Titles**: Make titles searchable and self-explanatory
2. **Keep Content Concise**: TIL notes should be brief and focused
3. **Consistent Categories**: Establish a set of standard categories
4. **Tag Generously**: Use multiple tags for better discoverability
5. **Document Sources**: Use the `source` field to track where you learned something
6. **Regular Reviews**: Periodically review your TIL notes to reinforce learning

## Category Suggestions

Here are some suggested categories to get started:

- **Programming Languages**: `python`, `javascript`, `typescript`, `go`, `rust`
- **Tools & Frameworks**: `docker`, `kubernetes`, `react`, `fastapi`, `django`
- **Concepts**: `algorithms`, `design-patterns`, `architecture`, `security`
- **Productivity**: `productivity`, `workflow`, `tools`, `automation`
- **Other**: `devops`, `databases`, `testing`, `documentation`, `misc`

## Integration with Memory System

TIL notes can be automatically created from:
- Conversation insights
- Memory retrievals
- Autonomous learning processes

Set the `source` field to indicate the origin:
- `manual`: User-created notes
- `conversation`: Generated from chat interactions
- `insight`: Extracted from learning processes
- `cli`: Created via command-line tool

## Database Migration

The TIL feature requires a database migration. Run:

```bash
alembic upgrade head
```

This will create the `til_notes` table with appropriate indexes.

## Troubleshooting

### "Table til_notes doesn't exist"
Run the database migration: `alembic upgrade head`

### CLI tool doesn't open editor
Set your `EDITOR` environment variable:
```bash
export EDITOR=nano  # or vim, code, etc.
```

### API returns 500 error
Check that:
1. Database is initialized and accessible
2. Required dependencies are installed
3. API server is running on correct port

## Future Enhancements

Planned features:
- [ ] Export notes as Markdown files
- [ ] Import notes from Markdown directory
- [ ] Automatic TIL creation from conversations
- [ ] Note sharing and collaboration
- [ ] Rich text/Markdown preview
- [ ] Note versioning/history
