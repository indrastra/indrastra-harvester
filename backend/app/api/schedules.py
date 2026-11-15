from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.dependencies import require_admin
from backend.app.db.session import get_db
from backend.app.harvest.models import HarvestSchedule
from backend.app.repositories.models import Repository

router = APIRouter(
    prefix="/schedules",
    tags=["harvest schedules"],
    dependencies=[Depends(require_admin)],
)
DatabaseSession = Annotated[Session, Depends(get_db)]


class ScheduleCreate(BaseModel):
    repository_id: int
    metadata_prefix: str = Field(min_length=1, max_length=128)
    set_spec: str | None = Field(default=None, max_length=255)
    frequency: Literal["hourly", "daily", "weekly"]
    start_at: datetime | None = None

    @field_validator("start_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("start_at must include a timezone offset.")
        return value


class ScheduleUpdate(BaseModel):
    enabled: bool


def schedule_payload(schedule: HarvestSchedule) -> dict:
    return {
        "id": schedule.id,
        "repository_id": schedule.repository_id,
        "metadata_prefix": schedule.metadata_prefix,
        "set_spec": schedule.set_spec,
        "frequency": schedule.frequency,
        "enabled": schedule.enabled,
        "next_run_at": schedule.next_run_at,
        "last_run_at": schedule.last_run_at,
        "last_success_at": schedule.last_success_at,
        "last_error": schedule.last_error,
        "created_at": schedule.created_at,
        "updated_at": schedule.updated_at,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_schedule(payload: ScheduleCreate, db: DatabaseSession):
    repository = db.get(Repository, payload.repository_id)
    if repository is None or not repository.is_enabled:
        raise HTTPException(status_code=404, detail="Enabled repository not found.")
    available_formats = {
        item.get("metadata_prefix")
        for item in repository.metadata_formats
        if isinstance(item, dict)
    }
    if available_formats and payload.metadata_prefix not in available_formats:
        raise HTTPException(status_code=422, detail="Metadata prefix is not supported by this repository.")

    schedule = HarvestSchedule(
        repository_id=repository.id,
        metadata_prefix=payload.metadata_prefix,
        set_spec=payload.set_spec,
        frequency=payload.frequency,
        enabled=True,
        next_run_at=payload.start_at or datetime.now(UTC),
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule_payload(schedule)


@router.get("")
def list_schedules(
    db: DatabaseSession,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    schedules = db.scalars(
        select(HarvestSchedule)
        .order_by(HarvestSchedule.next_run_at, HarvestSchedule.id)
        .offset(offset)
        .limit(limit)
    ).all()
    return [schedule_payload(schedule) for schedule in schedules]


@router.patch("/{schedule_id}")
def update_schedule(schedule_id: int, payload: ScheduleUpdate, db: DatabaseSession):
    schedule = db.get(HarvestSchedule, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Harvest schedule not found.")
    schedule.enabled = payload.enabled
    db.commit()
    db.refresh(schedule)
    return schedule_payload(schedule)


@router.post("/{schedule_id}/run-now")
def run_schedule_now(schedule_id: int, db: DatabaseSession):
    schedule = db.get(HarvestSchedule, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Harvest schedule not found.")
    if not schedule.enabled:
        raise HTTPException(status_code=409, detail="Enable this schedule before running it.")
    schedule.next_run_at = datetime.now(UTC)
    db.commit()
    db.refresh(schedule)
    return schedule_payload(schedule)


@router.delete("/{schedule_id}")
def disable_schedule(schedule_id: int, db: DatabaseSession):
    schedule = db.get(HarvestSchedule, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Harvest schedule not found.")
    schedule.enabled = False
    db.commit()
    return {"id": schedule.id, "enabled": schedule.enabled}
