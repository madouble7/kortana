"""merge_multiple_heads

Revision ID: 375bc7144c2d
Revises: c2d3e4f5a6b7, g8h9i0j1k2l3
Create Date: 2026-04-04 15:48:27.393081

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '375bc7144c2d'
down_revision: Union[str, Sequence[str], None] = ('c2d3e4f5a6b7', 'g8h9i0j1k2l3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
