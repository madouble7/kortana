"""add_validation_report_to_github_tasks

Revision ID: 9f1b7c4a2d10
Revises: 5d3f2c1a9b7e
Create Date: 2026-03-27 15:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9f1b7c4a2d10"
down_revision: str | Sequence[str] | None = "5d3f2c1a9b7e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add task-level validation evidence for autonomous execution."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    column_names = {column["name"] for column in inspector.get_columns("github_tasks")}

    if "validation_report" not in column_names:
        op.add_column(
            "github_tasks",
            sa.Column("validation_report", sa.JSON(), nullable=True),
        )


def downgrade() -> None:
    """Remove task-level validation evidence."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    column_names = {column["name"] for column in inspector.get_columns("github_tasks")}

    if "validation_report" in column_names:
        op.drop_column("github_tasks", "validation_report")
