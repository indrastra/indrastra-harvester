from datetime import UTC, datetime, timedelta

from celery.exceptions import OperationalError as CeleryOperationalError
from sqlalchemy import select

from backend.app.db.session import SessionLocal
from backend.app.harvest.models import HarvestJob, HarvestSchedule
from backend.app.harvest.tasks import run_harvest
from backend.app.repositories.models import Repository
from backend.app.worker import celery_app


def next_occurrence(frequency: str, now: datetime) -> datetime:
    if frequency == "hourly":
        return now + timedelta(hours=1)
    if frequency == "daily":
        return now + timedelta(days=1)
    if frequency == "weekly":
        return now + timedelta(days=7)
    raise ValueError("Unsupported harvest schedule frequency.")


@celery_app.task(name="harvest.dispatch_due_schedules", acks_late=True)
def dispatch_due_schedules() -> dict[str, int]:
    """Create durable jobs for due schedules, then enqueue them after commit."""
    db = SessionLocal()
    queued_jobs: list[HarvestJob] = []
    skipped = 0
    now = datetime.now(UTC)
    try:
        schedules = db.scalars(
            select(HarvestSchedule)
            .where(HarvestSchedule.enabled.is_(True), HarvestSchedule.next_run_at <= now)
            .order_by(HarvestSchedule.next_run_at, HarvestSchedule.id)
            .limit(100)
            .with_for_update(skip_locked=True)
        ).all()

        for schedule in schedules:
            repository = db.get(Repository, schedule.repository_id)
            schedule.last_run_at = now
            schedule.next_run_at = next_occurrence(schedule.frequency, now)
            if repository is None or not repository.is_enabled:
                schedule.last_error = "Repository is missing or disabled; scheduled run skipped."
                skipped += 1
                continue

            from_date = (
                schedule.last_success_at.date().isoformat()
                if schedule.last_success_at is not None
                else None
            )
            job = HarvestJob(
                repository_id=repository.id,
                schedule_id=schedule.id,
                metadata_prefix=schedule.metadata_prefix,
                set_spec=schedule.set_spec,
                from_date=from_date,
                until_date=now.date().isoformat(),
                status="queued",
            )
            db.add(job)
            queued_jobs.append(job)

        # Schedule advancement and job creation commit atomically.
        db.commit()

        queued = 0
        for job in queued_jobs:
            try:
                task = run_harvest.delay(job.id)
                job.celery_task_id = task.id
                queued += 1
            except CeleryOperationalError as exc:
                job.status = "failed"
                job.error_message = f"Could not enqueue scheduled harvest: {exc}"[:4000]
                job.finished_at = datetime.now(UTC)
                schedule = db.get(HarvestSchedule, job.schedule_id)
                if schedule is not None:
                    schedule.last_error = job.error_message
            db.commit()
        return {"due": len(schedules), "queued": queued, "skipped": skipped}
    finally:
        db.close()
