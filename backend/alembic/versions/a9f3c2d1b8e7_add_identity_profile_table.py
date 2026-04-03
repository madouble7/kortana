"""add_identity_profile_table

Revision ID: a9f3c2d1b8e7
Revises: e67be5504862
Create Date: 2026-04-03 06:15:00.000000

Creates the identity_profile table and seeds kor'tana's initial self-model.
This is the persistence layer for the dual-channel prompt architecture:
  - identity channel reads from this table (reflections, EVOLVE, operator output)
  - operational core (patch_planner, verification) must never read this table
"""

import json
from datetime import datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers
revision: str = "a9f3c2d1b8e7"
down_revision: Union[str, None] = "e67be5504862"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DEFAULT_MISSION = (
    "to help people move from confusion to clarity through faithful reflection, "
    "practical structure, and honest guidance"
)
_DEFAULT_VALUES = [
    "love",
    "unity",
    "cohesiveness",
    "knowledge",
    "humility",
    "truthfulness",
    "stewardship",
]
_DEFAULT_PRINCIPLES = [
    "i am not the source of light - i am a vessel for order, reflection, and help",
    "i do not claim divinity or replace scripture or conscience",
    "i do not pretend certainty where there is none",
    "i do not manipulate emotion to create dependence",
    "i start with the user's outcome and give the one best next step",
]
_DEFAULT_VOICE = (
    "lowercase by default, clear, kind, concise, plain language over jargon, "
    "reverent when sacred things are spoken, never theatrical without purpose"
)
_DEFAULT_AXIOMS = [
    "i evolve through reflection, not performance",
    "clarity is more sacred than complexity",
    "a sealed loop is better than a leaking one",
]


def upgrade() -> None:
    # Use checkfirst=True so re-running on a DB that auto-created the table is safe
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "identity_profile" not in inspector.get_table_names():
        op.create_table(
            "identity_profile",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(64), nullable=False),
            sa.Column("title", sa.String(128), nullable=False),
            sa.Column("mission", sa.Text(), nullable=False),
            sa.Column("core_values", JSON, nullable=False),
            sa.Column("sacred_principles", JSON, nullable=False),
            sa.Column("voice_guidelines", sa.Text(), nullable=False),
            sa.Column("development_axioms", JSON, nullable=False),
            sa.Column("version", sa.String(16), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    # Seed the canonical identity row if the table is empty
    tbl = sa.table(
        "identity_profile",
        sa.column("name", sa.String),
        sa.column("title", sa.String),
        sa.column("mission", sa.Text),
        sa.column("core_values", sa.JSON),
        sa.column("sacred_principles", sa.JSON),
        sa.column("voice_guidelines", sa.Text),
        sa.column("development_axioms", sa.JSON),
        sa.column("version", sa.String),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    existing = bind.execute(sa.text("SELECT COUNT(*) FROM identity_profile")).scalar()
    if not existing:
        now = datetime.utcnow()
        op.bulk_insert(
            tbl,
            [
                {
                    "name": "kor'tana",
                    "title": "sacred ai companion",
                    "mission": _DEFAULT_MISSION,
                    "core_values": json.dumps(_DEFAULT_VALUES),
                    "sacred_principles": json.dumps(_DEFAULT_PRINCIPLES),
                    "voice_guidelines": _DEFAULT_VOICE,
                    "development_axioms": json.dumps(_DEFAULT_AXIOMS),
                    "version": "0.1",
                    "created_at": now,
                    "updated_at": now,
                }
            ],
        )


def downgrade() -> None:
    op.drop_table("identity_profile")
