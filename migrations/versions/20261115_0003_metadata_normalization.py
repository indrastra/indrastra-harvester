"""Add normalized metadata projections and immutable source versions.

Revision ID: 20261115_0003
Revises: 20261115_0002
"""
from alembic import op
import sqlalchemy as sa

revision = "20261115_0003"
down_revision = "20261115_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "source_record_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_record_id", sa.Integer(), sa.ForeignKey("source_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("datestamp", sa.String(64)),
        sa.Column("metadata_prefix", sa.String(128), nullable=False),
        sa.Column("original_xml", sa.Text(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source_record_id", "version_number", name="uq_source_record_version"),
    )
    op.create_index("ix_source_record_versions_source_record_id", "source_record_versions", ["source_record_id"])

    op.create_table(
        "normalized_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_record_id", sa.Integer(), sa.ForeignKey("source_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("repository_id", sa.Integer(), sa.ForeignKey("repositories.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("oai_identifier", sa.String(1024), nullable=False),
        sa.Column("metadata_prefix", sa.String(128), nullable=False),
        sa.Column("schema", sa.String(128), nullable=False),
        sa.Column("normalization_version", sa.String(32), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("title", sa.JSON(), nullable=False),
        sa.Column("creators", sa.JSON(), nullable=False),
        sa.Column("subjects", sa.JSON(), nullable=False),
        sa.Column("publication_date", sa.String(64)),
        sa.Column("resource_type", sa.String(255)),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("normalized_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source_record_id", name="uq_normalized_source_record"),
    )
    op.create_index("ix_normalized_records_repository", "normalized_records", ["repository_id"])
    op.create_index("ix_normalized_records_deleted", "normalized_records", ["is_deleted"])


def downgrade() -> None:
    op.drop_index("ix_normalized_records_deleted", table_name="normalized_records")
    op.drop_index("ix_normalized_records_repository", table_name="normalized_records")
    op.drop_table("normalized_records")
    op.drop_index("ix_source_record_versions_source_record_id", table_name="source_record_versions")
    op.drop_table("source_record_versions")
