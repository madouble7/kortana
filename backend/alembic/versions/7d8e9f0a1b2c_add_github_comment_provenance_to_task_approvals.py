"""Add GitHub comment provenance to task_approvals

Revision ID: 7d8e9f0a1b2c
Revises: 1a2b3c4d5e6f
Create Date: 2026-03-29 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7d8e9f0a1b2c"
down_revision: str | Sequence[str] | None = "1a2b3c4d5e6f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Persist GitHub approval comment provenance and polling high-water marks."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    column_names = {column["name"] for column in inspector.get_columns("task_approvals")}

    if "github_comment_id" not in column_names:
        op.add_column(
            "task_approvals",
            sa.Column("github_comment_id", sa.String(length=64), nullable=True),
        )
    if "github_comment_url" not in column_names:
        op.add_column(
            "task_approvals",
            sa.Column("github_comment_url", sa.String(length=512), nullable=True),
        )
    if "last_processed_github_comment_id" not in column_names:
        op.add_column(
            "task_approvals",
            sa.Column(
                "last_processed_github_comment_id", sa.String(length=64), nullable=True
            ),
        )
    if "last_processed_github_comment_url" not in column_names:
        op.add_column(
            "task_approvals",
            sa.Column(
                "last_processed_github_comment_url",
                sa.String(length=512),
                nullable=True,
            ),
        )


def downgrade() -> None:
    """Remove GitHub approval comment provenance columns."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    column_names = {column["name"] for column in inspector.get_columns("task_approvals")}

    if "last_processed_github_comment_url" in column_names:
        op.drop_column("task_approvals", "last_processed_github_comment_url")
    if "last_processed_github_comment_id" in column_names:
        op.drop_column("task_approvals", "last_processed_github_comment_id")
    if "github_comment_url" in column_names:
        op.drop_column("task_approvals", "github_comment_url")
    if "github_comment_id" in column_names:
        op.drop_column("task_approvals", "github_comment_id")
