"""enhance_tasks_for_autonomy

Revision ID: b4df3eb06f8e
Revises: 002_add_github_tasks
Create Date: 2026-01-18 15:17:34.090243

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4df3eb06f8e'
down_revision: Union[str, Sequence[str], None] = '002_add_github_tasks'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add autonomy fields to tasks table."""
    # Add new columns as nullable first
    op.add_column("tasks", sa.Column("classification", sa.String(32), nullable=True))
    op.add_column("tasks", sa.Column("command", sa.Text(), nullable=True))
    op.add_column("tasks", sa.Column("ho_scaffold", sa.Text(), nullable=True))
    op.add_column("tasks", sa.Column("result", sa.Text(), nullable=True))
    op.add_column("tasks", sa.Column("error", sa.Text(), nullable=True))
    op.add_column("tasks", sa.Column("metadata", sa.JSON(), nullable=True))
    op.add_column("tasks", sa.Column("parent_id", sa.String(36), sa.ForeignKey("tasks.id"), nullable=True))

    # Make agent_id nullable
    op.alter_column("tasks", "agent_id", existing_type=sa.String(36), nullable=True)


def downgrade() -> None:
    """Downgrade schema - remove autonomy fields."""
    op.alter_column("tasks", "agent_id", existing_type=sa.String(36), nullable=False)
    op.drop_column("tasks", "parent_id")
    op.drop_column("tasks", "metadata")
    op.drop_column("tasks", "error")
    op.drop_column("tasks", "result")
    op.drop_column("tasks", "ho_scaffold")
    op.drop_column("tasks", "command")
    op.drop_column("tasks", "classification")
