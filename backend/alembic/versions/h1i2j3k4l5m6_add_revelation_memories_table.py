"""add revelation_memories table for kor'tana insight synthesis

Revision ID: h1i2j3k4l5m6
Revises: 375bc7144c2d
Create Date: 2026-04-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "h1i2j3k4l5m6"
down_revision: Union[str, Sequence[str], None] = "375bc7144c2d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "revelation_memories",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.Column("revelation_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("surfaced", sa.Boolean(), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_revelation_memories_created_at",
        "revelation_memories",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_revelation_memories_surfaced",
        "revelation_memories",
        ["surfaced"],
        unique=False,
    )
    op.create_index(
        "ix_revelation_memories_revelation_type",
        "revelation_memories",
        ["revelation_type"],
        unique=False,
    )
    op.create_index(
        "ix_revelation_memories_source",
        "revelation_memories",
        ["source"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_revelation_memories_source", table_name="revelation_memories")
    op.drop_index(
        "ix_revelation_memories_revelation_type", table_name="revelation_memories"
    )
    op.drop_index("ix_revelation_memories_surfaced", table_name="revelation_memories")
    op.drop_index(
        "ix_revelation_memories_created_at", table_name="revelation_memories"
    )
    op.drop_table("revelation_memories")
