"""add_embedding_column_to_self_memory

Stores a 768-dim float vector (JSON list) on each SelfMemory row so that
PromptAssemblyService can perform cosine-similarity semantic retrieval
without requiring a pgvector extension.  NULL means not yet embedded.

Revision ID: c2d3e4f5a6b7
Revises: b1c4d5e6f7a8
Create Date: 2026-04-03 11:50:04.478583
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, Sequence[str], None] = "b1c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add nullable embedding column to self_memory (idempotent via inspector)."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_cols = {c["name"] for c in inspector.get_columns("self_memory")}
    if "embedding" not in existing_cols:
        op.add_column(
            "self_memory",
            sa.Column("embedding", sa.JSON(), nullable=True),
        )


def downgrade() -> None:
    """Remove the embedding column from self_memory."""
    op.drop_column("self_memory", "embedding")
