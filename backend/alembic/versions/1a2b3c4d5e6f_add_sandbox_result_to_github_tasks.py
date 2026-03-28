"""Add sandbox_result to github_tasks

Revision ID: 1a2b3c4d5e6f
Revises: 9f1b7c4a2d10
Create Date: 2026-03-29 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1a2b3c4d5e6f"
down_revision = "9f1b7c4a2d10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("github_tasks", sa.Column("sandbox_result", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("github_tasks", "sandbox_result")
