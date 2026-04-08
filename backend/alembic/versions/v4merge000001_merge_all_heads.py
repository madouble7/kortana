"""Merge all heads into single timeline

Revision ID: v4merge000001
Revises: h1i2j3k4l5m6, b4df3eb06f8e, 9f1b7c4a2d10, v4a1b2c3d4e5
Create Date: 2026-04-08 00:01:00.000000

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "v4merge000001"
down_revision: Union[str, Sequence[str], None] = (
    "h1i2j3k4l5m6",
    "b4df3eb06f8e",
    "9f1b7c4a2d10",
    "v4a1b2c3d4e5",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge — no schema changes."""
    pass


def downgrade() -> None:
    """Merge — no schema changes."""
    pass
