"""V25: constitutional transparency tables.

Revision ID: v25a1b2c3d4e5
Revises: v24a1b2c3d4e5
Create Date: 2026-04-08
"""

from alembic import op
import sqlalchemy as sa

revision = "v25a1b2c3d4e5"
down_revision = "v24a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # V25A: docket entries
    op.create_table(
        "docket_entry",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("case_number", sa.String, unique=True, nullable=False, index=True),
        sa.Column("case_type", sa.String, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("parties_json", sa.Text, server_default="[]"),
        sa.Column("policy_area", sa.String, nullable=True, index=True),
        sa.Column("status", sa.String, nullable=False, server_default="opened"),
        sa.Column("reference_id", sa.String, nullable=True, index=True),
        sa.Column("opened_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("closed_at", sa.DateTime, nullable=True),
        sa.Column("outcome", sa.Text, nullable=True),
        sa.Column("docket_hash", sa.String, nullable=True),
    )

    # V25B: timeline events
    op.create_table(
        "timeline_event",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.String, unique=True, nullable=False, index=True),
        sa.Column("case_number", sa.String, nullable=False, index=True),
        sa.Column("event_type", sa.String, nullable=False),
        sa.Column("actor", sa.String, nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("extra_data_json", sa.Text, server_default="{}"),
        sa.Column("timestamp", sa.DateTime, server_default=sa.func.now()),
        sa.Column("event_hash", sa.String, nullable=True),
    )

    # V25C: procedural notices
    op.create_table(
        "procedural_notice",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("notice_id", sa.String, unique=True, nullable=False, index=True),
        sa.Column("case_number", sa.String, nullable=False, index=True),
        sa.Column("notice_type", sa.String, nullable=False),
        sa.Column("recipient", sa.String, nullable=False, index=True),
        sa.Column("subject", sa.Text, nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("delivery_status", sa.String, nullable=False, server_default="pending"),
        sa.Column("sent_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("delivered_at", sa.DateTime, nullable=True),
        sa.Column("acknowledged_at", sa.DateTime, nullable=True),
        sa.Column("notice_hash", sa.String, nullable=True),
    )

    # V25D: decision registry
    op.create_table(
        "decision_registry",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("decision_id", sa.String, unique=True, nullable=False, index=True),
        sa.Column("case_number", sa.String, nullable=False, index=True),
        sa.Column("decision_type", sa.String, nullable=False, index=True),
        sa.Column("outcome", sa.String, nullable=False),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("policy_area", sa.String, nullable=True, index=True),
        sa.Column("parties_json", sa.Text, server_default="[]"),
        sa.Column("reasoning_id", sa.String, nullable=True),
        sa.Column("cited_articles_json", sa.Text, server_default="[]"),
        sa.Column("cited_precedents_json", sa.Text, server_default="[]"),
        sa.Column("decided_by", sa.String, nullable=True),
        sa.Column("decided_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("tags_json", sa.Text, server_default="[]"),
        sa.Column("decision_hash", sa.String, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("decision_registry")
    op.drop_table("procedural_notice")
    op.drop_table("timeline_event")
    op.drop_table("docket_entry")
