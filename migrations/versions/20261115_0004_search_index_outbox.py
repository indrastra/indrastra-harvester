"""Add transactional OpenSearch indexing outbox.

Revision ID: 20261115_0004
Revises: 20261115_0003
"""
from alembic import op
import sqlalchemy as sa

revision = "20261115_0004"
down_revision = "20261115_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "index_outbox",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_record_id", sa.Integer(), sa.ForeignKey("source_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(24), nullable=False, server_default="upsert"),
        sa.Column("status", sa.String(24), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_index_outbox_source_record_id", "index_outbox", ["source_record_id"])
    op.create_index("ix_index_outbox_status", "index_outbox", ["status"])
    op.create_index("ix_index_outbox_status_created", "index_outbox", ["status", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_index_outbox_status_created", table_name="index_outbox")
    op.drop_index("ix_index_outbox_status", table_name="index_outbox")
    op.drop_index("ix_index_outbox_source_record_id", table_name="index_outbox")
    op.drop_table("index_outbox")
