from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.harvest.models import HarvestJob, HarvestJobLog, SourceRecord


def log_job(db: Session, job_id: int, message: str, level: str = "INFO") -> None:
    db.add(HarvestJobLog(job_id=job_id, level=level, message=message))


def upsert_source_record(
    db: Session, *, repository_id: int, identifier: str, datestamp: str | None,
    set_specs: list[str], metadata_prefix: str, original_xml: str, deleted: bool,
) -> str:
    """Idempotently store a source record using repository + OAI identifier identity."""
    record = db.scalar(select(SourceRecord).where(
        SourceRecord.repository_id == repository_id,
        SourceRecord.oai_identifier == identifier,
    ))
    now = datetime.now(UTC)
    if record is None:
        db.add(SourceRecord(
            repository_id=repository_id, oai_identifier=identifier, datestamp=datestamp,
            set_specs="\n".join(set_specs), metadata_prefix=metadata_prefix,
            original_xml=original_xml, is_deleted=deleted,
            source_status="deleted" if deleted else "active",
            last_harvested_at=now, updated_at=now,
        ))
        return "created"
    changed = (
        record.original_xml != original_xml or record.is_deleted != deleted
        or record.datestamp != datestamp or record.metadata_prefix != metadata_prefix
    )
    record.datestamp = datestamp
    record.set_specs = "\n".join(set_specs)
    record.metadata_prefix = metadata_prefix
    record.original_xml = original_xml
    record.is_deleted = deleted
    record.source_status = "deleted" if deleted else "active"
    record.last_harvested_at = now
    record.updated_at = now
    if changed:
        return "updated"
    return "unchanged"


def get_job_or_none(db: Session, job_id: int) -> HarvestJob | None:
    return db.get(HarvestJob, job_id)
