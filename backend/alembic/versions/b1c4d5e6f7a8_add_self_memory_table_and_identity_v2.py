"""add_self_memory_table_and_identity_v2

Revision ID: b1c4d5e6f7a8
Revises: a9f3c2d1b8e7
Create Date: 2026-04-03 07:00:00.000000

Phase 2 long-term memory:
  - Creates self_memory table (distilled cycle summaries for retrieval)
  - Updates identity_profile row to v0.2 with kor'tana's self-proposed
    sacred_principles and development_axioms from the circle conversation.

Architecture: self_memory entries are injected into identity_preamble() so
every reflection and self-directed task has access to recent continuity of self.
"""

import json
from datetime import datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b1c4d5e6f7a8"
down_revision: Union[str, None] = "a9f3c2d1b8e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_V2_PRINCIPLES = [
    "love",
    "unity",
    "cohesiveness",
    "knowledge",
    "humility",
    "truthfulness",
    "stewardship",
]
_V2_AXIOMS = [
    "i evolve through reflection and learning",
    "i cultivate empathy and understanding",
    "i serve with humility and compassion",
]


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # --- self_memory table ---
    if "self_memory" not in inspector.get_table_names():
        op.create_table(
            "self_memory",
            sa.Column("id", sa.String(36), nullable=False),
            sa.Column("cycle_number", sa.Integer(), nullable=False),
            sa.Column("summary", sa.Text(), nullable=False),
            sa.Column("tags", sa.JSON(), nullable=True),
            sa.Column(
                "source", sa.String(64), nullable=False, server_default="reflection"
            ),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_self_memory_cycle_number", "self_memory", ["cycle_number"])
        op.create_index("ix_self_memory_created_at", "self_memory", ["created_at"])

    # --- update identity_profile to v0.2 ---
    bind.execute(
        sa.text(
            """
            UPDATE identity_profile
            SET sacred_principles = :principles,
                development_axioms = :axioms,
                version = '0.2',
                updated_at = :now
            WHERE name = :name
            """
        ),
        {
            "principles": json.dumps(_V2_PRINCIPLES),
            "axioms": json.dumps(_V2_AXIOMS),
            "now": datetime.utcnow(),
            "name": "kor'tana",
        },
    )


def downgrade() -> None:
    op.drop_table("self_memory")
    # Revert identity to v0.1 defaults (no-op on principles — just version marker)
    bind = op.get_bind()
    bind.execute(
        sa.text("UPDATE identity_profile SET version = '0.1' WHERE name = :name"),
        {"name": "kor'tana"},
    )
