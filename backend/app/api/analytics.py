from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.api.dependencies import require_admin
from backend.app.db.session import get_db
from backend.app.harvest.models import HarvestJob, HarvestSchedule, SourceRecord
from backend.app.metadata.models import NormalizedRecord
from backend.app.repositories.models import Repository
from backend.app.search.models import IndexOutbox

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(require_admin)],
)
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/summary")
def analytics_summary(db: DatabaseSession):
    cutoff = datetime.now(UTC) - timedelta(days=30)

    repository_total = db.scalar(select(func.count(Repository.id))) or 0
    repository_enabled = db.scalar(
        select(func.count(Repository.id)).where(Repository.is_enabled.is_(True))
    ) or 0
    source_total = db.scalar(select(func.count(SourceRecord.id))) or 0
    source_active = db.scalar(
        select(func.count(SourceRecord.id)).where(SourceRecord.is_deleted.is_(False))
    ) or 0
    source_deleted = db.scalar(
        select(func.count(SourceRecord.id)).where(SourceRecord.is_deleted.is_(True))
    ) or 0
    normalized_total = db.scalar(
        select(func.count(NormalizedRecord.id)).where(NormalizedRecord.is_deleted.is_(False))
    ) or 0
    recently_harvested = db.scalar(
        select(func.count(SourceRecord.id)).where(SourceRecord.last_harvested_at >= cutoff)
    ) or 0
    schedules_enabled = db.scalar(
        select(func.count(HarvestSchedule.id)).where(HarvestSchedule.enabled.is_(True))
    ) or 0
    outbox_pending = db.scalar(
        select(func.count(IndexOutbox.id)).where(IndexOutbox.status == "pending")
    ) or 0
    outbox_failed = db.scalar(
        select(func.count(IndexOutbox.id)).where(IndexOutbox.status == "failed")
    ) or 0

    job_statuses = db.execute(
        select(HarvestJob.status, func.count(HarvestJob.id)).group_by(HarvestJob.status)
    ).all()
    job_counts = {status: count for status, count in job_statuses}

    repository_rows = db.execute(
        select(Repository.id, Repository.name, func.count(SourceRecord.id))
        .outerjoin(SourceRecord, SourceRecord.repository_id == Repository.id)
        .where(Repository.is_enabled.is_(True))
        .group_by(Repository.id, Repository.name)
        .order_by(func.count(SourceRecord.id).desc())
        .limit(10)
    ).all()

    return {
        "generated_at": datetime.now(UTC),
        "repositories": {
            "total": repository_total,
            "enabled": repository_enabled,
            "disabled": repository_total - repository_enabled,
        },
        "records": {
            "source_total": source_total,
            "active": source_active,
            "deleted": source_deleted,
            "normalized_active": normalized_total,
            "harvested_last_30_days": recently_harvested,
        },
        "harvest_jobs": job_counts,
        "schedules_enabled": schedules_enabled,
        "index_outbox": {
            "pending": outbox_pending,
            "failed": outbox_failed,
        },
        "top_repositories": [
            {"id": repository_id, "name": name, "source_records": count}
            for repository_id, name, count in repository_rows
        ],
    }
