"""merge all heads into single lineage

Revision ID: merge_all_heads
Revises: merge_phase11_v26, v28a1b2c3d4e5
Create Date: 2026-04-08

"""

# revision identifiers, used by Alembic.
revision = "merge_all_heads"
down_revision = ("merge_phase11_v26", "v28a1b2c3d4e5")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
