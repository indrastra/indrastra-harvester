from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.dependencies import require_admin
from backend.app.db.session import get_db
from backend.app.harvest.models import HarvestJob, HarvestJobLog
from backend.app.harvest.tasks import run_harvest
from backend.app.repositories.models import Repository

router = APIRouter(prefix="/harvests", tags=["harvesting"], dependencies=[Depends(require_admin)])
DatabaseSession = Annotated[Session, Depends(get_db)]


class HarvestCreate(BaseModel):
    repository_id: int
    metadata_prefix: str = Field(min_length=1, max_length=128)
    set_spec: str | None = Field(default=None, max_length=255)
    from_date: date | None = None
    until_date: date | None = None

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.from_date and self.until_date and self.from_date > self.until_date:
            raise ValueError("from_date must not be later than until_date")
        return self


def job_payload(job: HarvestJob) -> dict:
    return {
        "id": job.id, "repository_id": job.repository_id, "schedule_id": job.schedule_id,
        "status": job.status,
        "metadata_prefix": job.metadata_prefix, "set_spec": job.set_spec,
        "from_date": job.from_date, "until_date": job.until_date,
        "records_seen": job.records_seen, "records_created": job.records_created,
        "records_updated": job.records_updated, "records_deleted": job.records_deleted,
        "pages_completed": job.pages_completed, "error_message": job.error_message,
        "created_at": job.created_at, "started_at": job.started_at, "finished_at": job.finished_at,
    }


def enqueue_job(job: HarvestJob, db: Session) -> None:
    try:
        task = run_harvest.delay(job.id)
        job.celery_task_id = task.id
        db.commit()
    except Exception as exc:
        job.status = "failed"
        job.error_message = f"Could not enqueue harvest task: {exc}"[:4000]
        db.commit()
        raise HTTPException(status_code=503, detail="Harvest queue is unavailable.") from exc


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def create_harvest(payload: HarvestCreate, db: DatabaseSession):
    repository = db.get(Repository, payload.repository_id)
    if repository is None or not repository.is_enabled:
        raise HTTPException(status_code=404, detail="Enabled repository not found.")
    job = HarvestJob(
        repository_id=repository.id, metadata_prefix=payload.metadata_prefix,
        set_spec=payload.set_spec,
        from_date=payload.from_date.isoformat() if payload.from_date else None,
        until_date=payload.until_date.isoformat() if payload.until_date else None,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    enqueue_job(job, db)
    return job_payload(job)


@router.get("")
def list_harvests(
    db: DatabaseSession,
    offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
):
    jobs = db.scalars(select(HarvestJob).order_by(HarvestJob.created_at.desc()).offset(offset).limit(limit)).all()
    return [job_payload(job) for job in jobs]


@router.get("/{job_id}")
def get_harvest(job_id: int, db: DatabaseSession):
    job = db.get(HarvestJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Harvest job not found.")
    payload = job_payload(job)
    payload["logs"] = [
        {"level": log.level, "message": log.message, "created_at": log.created_at}
        for log in db.scalars(select(HarvestJobLog).where(HarvestJobLog.job_id == job_id).order_by(HarvestJobLog.id)).all()
    ]
    return payload


@router.post("/{job_id}/resume", status_code=status.HTTP_202_ACCEPTED)
def resume_harvest(job_id: int, db: DatabaseSession):
    job = db.get(HarvestJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Harvest job not found.")
    if job.status not in {"failed", "paused"}:
        raise HTTPException(status_code=409, detail="Only failed or paused jobs can be resumed.")
    job.status = "queued"
    job.error_message = None
    job.finished_at = None
    db.commit()
    enqueue_job(job, db)
    return job_payload(job)
