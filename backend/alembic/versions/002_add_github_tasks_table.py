"""
Add GitHub Tasks table for Phase 2 autonomous features

Revision ID: 002_add_github_tasks
Revises: 001_initial_schema
Create Date: 2026-01-18 13:58:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_github_tasks'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Create github_tasks table"""

    op.create_table(
        "github_tasks",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("github_issue_number", sa.Integer(), nullable=False),
        sa.Column("github_repo", sa.String(255), nullable=False),
        sa.Column("github_pr_number", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("priority", sa.String(16), server_default="medium"),
        sa.Column("analysis", sa.Text(), nullable=True),
        sa.Column("plan", sa.Text(), nullable=True),
        sa.Column("branch_name", sa.String(255), nullable=True),
        sa.Column("commit_sha", sa.String(40), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_count", sa.Integer(), server_default="0"),
        sa.Column("max_retries", sa.Integer(), server_default="3"),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column("estimated_effort", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(), nullable=True),
        sa.Column("executed_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("branch_name"),
    )

    # Create indexes for commonly queried columns
    op.create_index("ix_github_tasks_github_issue_number", "github_tasks", ["github_issue_number"])
    op.create_index("ix_github_tasks_status", "github_tasks", ["status"])
    op.create_index("ix_github_tasks_github_pr_number", "github_tasks", ["github_pr_number"])
    op.create_index("ix_github_tasks_created_at", "github_tasks", ["created_at"])


def downgrade():
    """Drop github_tasks table"""
    op.drop_index("ix_github_tasks_created_at", table_name="github_tasks")
    op.drop_index("ix_github_tasks_github_pr_number", table_name="github_tasks")
    op.drop_index("ix_github_tasks_status", table_name="github_tasks")
    op.drop_index("ix_github_tasks_github_issue_number", table_name="github_tasks")
    op.drop_table("github_tasks")
