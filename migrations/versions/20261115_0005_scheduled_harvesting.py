"""Add persisted recurring harvest schedules.

Revision ID: 20261115_0005
Revises: 20261115_0004
"""
from alembic import op
import sqlalchemy as sa

revision = "20261115_0005"
down_revision = "20261115_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "harvest_schedules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("repository_id", sa.Integer(), sa.ForeignKey("repositories.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("metadata_prefix", sa.String(128), nullable=False),
        sa.Column("set_spec", sa.String(255)),
        sa.Column("frequency", sa.String(16), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True)),
        sa.Column("last_success_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_harvest_schedules_repository_id", "harvest_schedules", ["repository_id"])
    op.create_index("ix_harvest_schedules_enabled", "harvest_schedules", ["enabled"])
    op.create_index("ix_harvest_schedules_next_run_at", "harvest_schedules", ["next_run_at"])
    op.create_index("ix_harvest_schedules_due", "harvest_schedules", ["enabled", "next_run_at"])

    op.add_column(
        "harvest_jobs",
        sa.Column("schedule_id", sa.Integer(), sa.ForeignKey("harvest_schedules.id", ondelete="SET NULL")),
    )
    op.create_index("ix_harvest_jobs_schedule_id", "harvest_jobs", ["schedule_id"])


def downgrade() -> None:
    op.drop_index("ix_harvest_jobs_schedule_id", table_name="harvest_jobs")
    op.drop_column("harvest_jobs", "schedule_id")
    op.drop_index("ix_harvest_schedules_due", table_name="harvest_schedules")
    op.drop_index("ix_harvest_schedules_next_run_at", table_name="harvest_schedules")
    op.drop_index("ix_harvest_schedules_enabled", table_name="harvest_schedules")
    op.drop_index("ix_harvest_schedules_repository_id", table_name="harvest_schedules")
    op.drop_table("harvest_schedules")
