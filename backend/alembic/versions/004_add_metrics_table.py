"""
Add Metrics table for persistent metrics storage

Revision ID: 004_add_metrics_table
Revises: b4df3eb06f8e
Create Date: 2026-03-23 14:24:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_add_metrics_table'
down_revision: Union[str, None] = 'b4df3eb06f8e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Create metrics table"""

    op.create_table(
        "metrics",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("labels", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for commonly queried columns
    op.create_index("ix_metrics_name", "metrics", ["name"])
    op.create_index("ix_metrics_created_at", "metrics", ["created_at"])


def downgrade():
    """Drop metrics table"""
    op.drop_index("ix_metrics_created_at", table_name="metrics")
    op.drop_index("ix_metrics_name", table_name="metrics")
    op.drop_table("metrics")
