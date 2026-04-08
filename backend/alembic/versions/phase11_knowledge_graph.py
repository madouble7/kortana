"""Phase 11: long-term cognitive knowledge graph tables.

Three tables for kor'tana's structured semantic memory:
  - knowledge_entities: nodes (people, projects, tools, concepts, etc.)
  - knowledge_relations: directed edges between entities
  - knowledge_facts: temporal assertions with confidence decay

Revision ID: phase11_knowledge_graph
Revises: v23a1b2c3d4e5
Create Date: 2026-04-08
"""

import sqlalchemy as sa
from alembic import op

revision = "phase11_knowledge_graph"
down_revision = "v23a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_entities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False, index=True),
        sa.Column("entity_type", sa.String(64), nullable=False, index=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("attributes", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("mention_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("embedding", sa.JSON(), nullable=True),
        sa.Column("first_seen", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_seen", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "knowledge_relations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "source_id",
            sa.String(36),
            sa.ForeignKey("knowledge_entities.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "target_id",
            sa.String(36),
            sa.ForeignKey("knowledge_entities.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("relation_type", sa.String(64), nullable=False, index=True),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("first_seen", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_seen", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "knowledge_facts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "entity_id",
            sa.String(36),
            sa.ForeignKey("knowledge_entities.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("fact_text", sa.Text(), nullable=False),
        sa.Column(
            "source", sa.String(64), nullable=False, server_default="'conversation'"
        ),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("valid_from", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("invalidated_at", sa.DateTime(), nullable=True),
        sa.Column(
            "superseded_by",
            sa.String(36),
            sa.ForeignKey("knowledge_facts.id"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("knowledge_facts")
    op.drop_table("knowledge_relations")
    op.drop_table("knowledge_entities")
