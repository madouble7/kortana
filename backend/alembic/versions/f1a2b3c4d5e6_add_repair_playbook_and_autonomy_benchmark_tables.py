"""Add repair_playbook and autonomy_benchmark tables

Revision ID: f1a2b3c4d5e6
Revises: ea428b0c4e2a
Create Date: 2026-05-01 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "ea428b0c4e2a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "repair_playbook",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("incident_type", sa.String(length=128), nullable=False, index=True),
        sa.Column("incident_pattern", sa.Text(), nullable=False),
        sa.Column("chosen_strategy", sa.Text(), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False, index=True),
        sa.Column("confidence_delta", sa.Float(), nullable=True),
        sa.Column("times_used", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_repair_playbook_incident_type", "repair_playbook", ["incident_type"]
    )
    op.create_index("ix_repair_playbook_outcome", "repair_playbook", ["outcome"])

    op.create_table(
        "autonomy_benchmark",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("suite_name", sa.String(length=128), nullable=False, index=True),
        sa.Column("incident_type", sa.String(length=128), nullable=False, index=True),
        sa.Column("detected", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("patch_succeeded", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column(
            "validation_succeeded", sa.Boolean(), nullable=False, server_default="0"
        ),
        sa.Column("time_to_recovery_seconds", sa.Float(), nullable=True),
        sa.Column("autonomy_index_at_run", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "run_at",
            sa.DateTime(),
            nullable=False,
            index=True,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_autonomy_benchmark_suite_name", "autonomy_benchmark", ["suite_name"]
    )
    op.create_index(
        "ix_autonomy_benchmark_incident_type", "autonomy_benchmark", ["incident_type"]
    )
    op.create_index("ix_autonomy_benchmark_run_at", "autonomy_benchmark", ["run_at"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_autonomy_benchmark_run_at", table_name="autonomy_benchmark")
    op.drop_index(
        "ix_autonomy_benchmark_incident_type", table_name="autonomy_benchmark"
    )
    op.drop_index("ix_autonomy_benchmark_suite_name", table_name="autonomy_benchmark")
    op.drop_table("autonomy_benchmark")

    op.drop_index("ix_repair_playbook_outcome", table_name="repair_playbook")
    op.drop_index("ix_repair_playbook_incident_type", table_name="repair_playbook")
    op.drop_table("repair_playbook")
