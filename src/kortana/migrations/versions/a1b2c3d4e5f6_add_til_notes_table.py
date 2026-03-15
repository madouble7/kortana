"""add_til_notes_table

Revision ID: a1b2c3d4e5f6
Revises: df8dc2b048ef
Create Date: 2026-01-22 06:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "df8dc2b048ef"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema to add TIL notes table."""
    op.create_table(
        "til_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_til_notes_id"), "til_notes", ["id"], unique=False)
    op.create_index(op.f("ix_til_notes_title"), "til_notes", ["title"], unique=False)
    op.create_index(op.f("ix_til_notes_category"), "til_notes", ["category"], unique=False)


def downgrade() -> None:
    """Downgrade schema to remove TIL notes table."""
    op.drop_index(op.f("ix_til_notes_category"), table_name="til_notes")
    op.drop_index(op.f("ix_til_notes_title"), table_name="til_notes")
    op.drop_index(op.f("ix_til_notes_id"), table_name="til_notes")
    op.drop_table("til_notes")
