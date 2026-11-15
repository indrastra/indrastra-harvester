"""Add persistent harvesting jobs, logs, and source records.

Revision ID: 20261115_0002
Revises: 20261115_0001
"""
from alembic import op
import sqlalchemy as sa

revision = "20261115_0002"
down_revision = "20261115_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "harvest_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("repository_id", sa.Integer(), sa.ForeignKey("repositories.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="queued"),
        sa.Column("metadata_prefix", sa.String(128), nullable=False),
        sa.Column("set_spec", sa.String(255)),
        sa.Column("from_date", sa.String(64)),
        sa.Column("until_date", sa.String(64)),
        sa.Column("resumption_token", sa.Text()),
        sa.Column("records_seen", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_deleted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pages_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text()),
        sa.Column("celery_task_id", sa.String(255)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_harvest_jobs_repository_id", "harvest_jobs", ["repository_id"])
    op.create_index("ix_harvest_jobs_status", "harvest_jobs", ["status"])
    op.create_index("ix_harvest_jobs_celery_task_id", "harvest_jobs", ["celery_task_id"])
    op.create_table(
        "harvest_job_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("harvest_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("level", sa.String(16), nullable=False, server_default="INFO"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_harvest_job_logs_job_id", "harvest_job_logs", ["job_id"])
    op.create_table(
        "source_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("repository_id", sa.Integer(), sa.ForeignKey("repositories.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("oai_identifier", sa.String(1024), nullable=False),
        sa.Column("datestamp", sa.String(64)),
        sa.Column("set_specs", sa.Text()),
        sa.Column("metadata_prefix", sa.String(128), nullable=False),
        sa.Column("original_xml", sa.Text(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source_status", sa.String(24), nullable=False, server_default="active"),
        sa.Column("first_harvested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_harvested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("repository_id", "oai_identifier", name="uq_source_record_repository_identifier"),
    )
    op.create_index("ix_source_records_datestamp", "source_records", ["repository_id", "datestamp"])
    op.create_index("ix_source_records_is_deleted", "source_records", ["is_deleted"])


def downgrade() -> None:
    op.drop_index("ix_source_records_is_deleted", table_name="source_records")
    op.drop_index("ix_source_records_datestamp", table_name="source_records")
    op.drop_table("source_records")
    op.drop_index("ix_harvest_job_logs_job_id", table_name="harvest_job_logs")
    op.drop_table("harvest_job_logs")
    op.drop_index("ix_harvest_jobs_celery_task_id", table_name="harvest_jobs")
    op.drop_index("ix_harvest_jobs_status", table_name="harvest_jobs")
    op.drop_index("ix_harvest_jobs_repository_id", table_name="harvest_jobs")
    op.drop_table("harvest_jobs")
