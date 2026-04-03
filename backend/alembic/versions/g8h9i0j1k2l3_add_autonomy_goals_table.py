"""add autonomy_goals table for persistent goal graph

Revision ID: g8h9i0j1k2l3
Revises: e67be5504862
Create Date: 2026-04-03

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "g8h9i0j1k2l3"
down_revision: Union[str, Sequence[str], None] = "e67be5504862"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "autonomy_goals",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("tier", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("success_criteria", sa.Text(), nullable=False),
        sa.Column("progress", sa.Float(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.String(length=36), nullable=True),
        sa.Column("depends_on", sa.JSON(), nullable=True),
        sa.Column("linked_tasks", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["autonomy_goals.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_autonomy_goals_tier", "autonomy_goals", ["tier"], unique=False)
    op.create_index("ix_autonomy_goals_status", "autonomy_goals", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_autonomy_goals_status", table_name="autonomy_goals")
    op.drop_index("ix_autonomy_goals_tier", table_name="autonomy_goals")
    op.drop_table("autonomy_goals")
