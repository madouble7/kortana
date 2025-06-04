# Database Schema Documentation

## 🗄️ Current Schema State

**Last Updated**: June 4, 2025
**Migration Head**: df8dc2b048ef
**Database Engine**: SQLite (development) / PostgreSQL (production-ready)
**ORM**: SQLAlchemy 2.0.41

## 📊 Schema Overview

### Core Tables

#### `core_memories`
Primary storage for memory core functionality.

```sql
CREATE TABLE core_memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX ix_core_memories_id ON core_memories (id);
CREATE INDEX ix_core_memories_title ON core_memories (title);
```

#### Table Details
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier |
| `title` | VARCHAR(255) | NOT NULL, INDEXED | Memory title/name |
| `content` | TEXT | NOT NULL | Memory content/data |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP, ON UPDATE | Last modification timestamp |

## 🔧 ORM Models

### CoreMemory Model
**Location**: `src/kortana/modules/memory_core/models.py`

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from kortana.services.database import Base

class CoreMemory(Base):
    __tablename__ = "core_memories"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

## 📈 Migration History

### Applied Migrations

1. **f2284b72eb0f** - `create_core_memories_table`
   - Initial migration base
   - Created core database structure

2. **df8dc2b048ef** - `add_core_memories_table` (HEAD)
   - Added CoreMemory table with full schema
   - Implemented proper indexing
   - Added timestamp management

### Migration Files Location
```
src/kortana/migrations/versions/
├── f2284b72eb0f_create_core_memories_table.py
└── df8dc2b048ef_add_core_memories_table.py
```

## 🔄 Database Operations

### CRUD Operations via MemoryCoreService

#### Create Memory
```python
from kortana.modules.memory_core.services import MemoryCoreService

service = MemoryCoreService(db_session)
memory = service.store_memory(
    title="Example Memory",
    content="This is example content for the memory."
)
```

#### Read Memory
```python
# By ID
memory = service.retrieve_memory_by_id(memory_id=1)

# Direct query
memories = db_session.query(CoreMemory).filter(
    CoreMemory.title.contains("search_term")
).all()
```

#### Update Memory
```python
memory = db_session.query(CoreMemory).filter(CoreMemory.id == 1).first()
memory.content = "Updated content"
memory.updated_at = func.now()
db_session.commit()
```

#### Delete Memory
```python
db_session.query(CoreMemory).filter(CoreMemory.id == 1).delete()
db_session.commit()
```

## 🚀 Future Schema Expansions

### Planned Tables

#### `ethical_evaluations`
For storing ethical discernment results.
```sql
-- Planned schema
CREATE TABLE ethical_evaluations (
    id INTEGER PRIMARY KEY,
    memory_id INTEGER REFERENCES core_memories(id),
    evaluation_type VARCHAR(100),
    score DECIMAL(3,2),
    reasoning TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### `memory_categories`
For organizing memories by category.
```sql
-- Planned schema
CREATE TABLE memory_categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    color VARCHAR(7), -- Hex color code
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE memory_category_mappings (
    memory_id INTEGER REFERENCES core_memories(id),
    category_id INTEGER REFERENCES memory_categories(id),
    PRIMARY KEY (memory_id, category_id)
);
```

#### `api_access_logs`
For tracking API usage and access patterns.
```sql
-- Planned schema
CREATE TABLE api_access_logs (
    id INTEGER PRIMARY KEY,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    user_id VARCHAR(255),
    request_data TEXT,
    response_status INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 🔧 Development Guidelines

### Adding New Tables
1. Create ORM model in appropriate module
2. Import model in `src/kortana/migrations/env.py`
3. Generate migration: `alembic revision --autogenerate -m "add_new_table"`
4. Review and apply: `alembic upgrade head`

### Schema Modifications
1. Modify existing ORM model
2. Generate migration: `alembic revision --autogenerate -m "modify_table_description"`
3. **Always review** auto-generated migration before applying
4. Test migration in development environment
5. Apply: `alembic upgrade head`

### Data Migrations
For data transformations or complex schema changes:
```python
# In migration file
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Schema changes
    op.add_column('core_memories', sa.Column('new_field', sa.String(100)))

    # Data migration
    connection = op.get_bind()
    connection.execute("""
        UPDATE core_memories
        SET new_field = 'default_value'
        WHERE new_field IS NULL
    """)
```

## 📊 Performance Considerations

### Current Indexes
- `ix_core_memories_id` - Primary key lookup
- `ix_core_memories_title` - Title-based searches

### Recommended Future Indexes
```sql
-- For content search (if implementing full-text search)
CREATE INDEX ix_core_memories_content_fts ON core_memories
USING GIN (to_tsvector('english', content));

-- For timestamp queries
CREATE INDEX ix_core_memories_created_at ON core_memories (created_at);
CREATE INDEX ix_core_memories_updated_at ON core_memories (updated_at);
```

### Query Optimization Tips
1. Always use indexes for filter conditions
2. Limit result sets with `LIMIT` clauses
3. Use `select_related()` for foreign key relationships
4. Consider read replicas for heavy read workloads

## 🔒 Security Considerations

### Data Protection
- All timestamps use timezone-aware datetime
- Content is stored as TEXT (supports encryption at application layer)
- No sensitive data stored in plain text

### Access Control
- Database access controlled through service layer
- No direct database access from API endpoints
- Session management through dependency injection

---

**🔍 For migration troubleshooting, see `docs/GETTING_STARTED.md` Database Migrations section.**
