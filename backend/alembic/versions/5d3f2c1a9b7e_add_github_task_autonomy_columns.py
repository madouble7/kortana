"""
Add missing autonomy columns to github_tasks

Revision ID: 5d3f2c1a9b7e
Revises: 004_add_metrics_table
Create Date: 2026-03-25 22:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5d3f2c1a9b7e"
down_revision: Union[str, None] = "004_add_metrics_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Add autonomy fields that the current GitHubTask model expects."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    column_names = {column["name"] for column in inspector.get_columns("github_tasks")}
    index_names = {index["name"] for index in inspector.get_indexes("github_tasks")}

    if "classification" not in column_names:
        op.add_column(
            "github_tasks",
            sa.Column("classification", sa.String(length=32), nullable=True),
        )
    if "ho_scaffold" not in column_names:
        op.add_column(
            "github_tasks",
            sa.Column("ho_scaffold", sa.Text(), nullable=True),
        )
    if "code_changes" not in column_names:
        op.add_column(
            "github_tasks",
            sa.Column("code_changes", sa.JSON(), nullable=True),
        )

    if "ix_github_tasks_classification" not in index_names:
        op.create_index(
            "ix_github_tasks_classification",
            "github_tasks",
            ["classification"],
        )


def downgrade():
    """Remove autonomy fields from github_tasks."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    column_names = {column["name"] for column in inspector.get_columns("github_tasks")}
    index_names = {index["name"] for index in inspector.get_indexes("github_tasks")}

    if "ix_github_tasks_classification" in index_names:
        op.drop_index("ix_github_tasks_classification", table_name="github_tasks")

    if "code_changes" in column_names:
        op.drop_column("github_tasks", "code_changes")
    if "ho_scaffold" in column_names:
        op.drop_column("github_tasks", "ho_scaffold")
    if "classification" in column_names:
        op.drop_column("github_tasks", "classification")
