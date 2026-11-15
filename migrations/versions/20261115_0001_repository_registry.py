"""Create repository registry.

Revision ID: 20261115_0001
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "20261115_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "repositories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("endpoint", sa.String(length=2048), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("organization", sa.String(length=200), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=True),
        sa.Column("contact_email", sa.String(length=320), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("validation_status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("oai_repository_name", sa.String(length=500), nullable=True),
        sa.Column("admin_email", sa.String(length=320), nullable=True),
        sa.Column("earliest_datestamp", sa.String(length=64), nullable=True),
        sa.Column("deleted_record", sa.String(length=32), nullable=True),
        sa.Column("granularity", sa.String(length=64), nullable=True),
        sa.Column("metadata_formats", sa.JSON(), nullable=False),
        sa.Column("sets", sa.JSON(), nullable=False),
        sa.Column("last_validation_error", sa.Text(), nullable=True),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("endpoint", name="uq_repositories_endpoint"),
    )
    op.create_index("ix_repositories_id", "repositories", ["id"])
    op.create_index("ix_repositories_name", "repositories", ["name"])
    op.create_index("ix_repositories_validation_status", "repositories", ["validation_status"])


def downgrade() -> None:
    op.drop_index("ix_repositories_validation_status", table_name="repositories")
    op.drop_index("ix_repositories_name", table_name="repositories")
    op.drop_index("ix_repositories_id", table_name="repositories")
    op.drop_table("repositories")
