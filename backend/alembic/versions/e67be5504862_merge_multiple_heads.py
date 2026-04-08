"""merge_multiple_heads

Revision ID: e67be5504862
Revises: 4c27026a0fc0, f1a2b3c4d5e6
Create Date: 2026-04-02 04:09:39.613895

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "e67be5504862"
down_revision: Union[str, Sequence[str], None] = ("4c27026a0fc0", "f1a2b3c4d5e6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
