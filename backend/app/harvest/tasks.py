from datetime import UTC, datetime
from xml.etree import ElementTree as ET

from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select, text

from backend.app.db.session import SessionLocal
from backend.app.harvest.exceptions import OAITransportError
from backend.app.harvest.models import HarvestJob, SourceRecord
from backend.app.harvest.oai_client import NS, OAIPMHClient
from backend.app.harvest.service import log_job, upsert_source_record
from backend.app.metadata.service import normalize_source_record
from backend.app.repositories.models import Repository
from backend.app.worker import celery_app


@celery_app.task(
    bind=True, name="harvest.run", max_retries=3, acks_late=True,
    soft_time_limit=3300, time_limit=3600,
)
def run_harvest(self, job_id: int) -> dict[str, int | str]:
    """Run ListRecords with durable page-level checkpoints and idempotent delivery."""
    db = SessionLocal()
    lock_key: int | None = None
    locked = False
    try:
        job = db.get(HarvestJob, job_id)
        if job is None:
            return {"job_id": job_id, "status": "missing"}
        if job.status == "completed":
            return {"job_id": job_id, "status": "completed", "records_seen": job.records_seen}
        repository = db.get(Repository, job.repository_id)
        if repository is None or not repository.is_enabled:
            job.status = "failed"
            job.error_message = "Repository is missing or disabled."
            job.finished_at = datetime.now(UTC)
            log_job(db, job.id, job.error_message, "ERROR")
            db.commit()
            return {"job_id": job_id, "status": "failed"}

        lock_key = int(repository.id)
        locked = bool(db.execute(
            text("SELECT pg_try_advisory_lock(:key)"), {"key": lock_key}
        ).scalar())
        if not locked:
            # Keep a distinct queued job alive until the repository lock is released.
            raise self.retry(countdown=15, max_retries=20)

        db.refresh(job)
        if job.status == "completed":
            return {"job_id": job_id, "status": "completed", "records_seen": job.records_seen}
        job.status = "running"
        job.started_at = job.started_at or datetime.now(UTC)
        job.celery_task_id = self.request.id
        log_job(db, job.id, "Harvest started or resumed.")
        db.commit()

        try:
            with OAIPMHClient(repository.endpoint) as client:
                token = job.resumption_token
                first_page = token is None
                while True:
                    if first_page:
                        params = {"metadataPrefix": job.metadata_prefix}
                        if job.from_date:
                            params["from"] = job.from_date
                        if job.until_date:
                            params["until"] = job.until_date
                        if job.set_spec:
                            params["set"] = job.set_spec
                        response = client.request("ListRecords", **params)
                    else:
                        response = client.request("ListRecords", resumptionToken=token)

                    container = response.root.find("oai:ListRecords", NS)
                    if container is None:
                        raise ValueError("OAI-PMH ListRecords response is missing ListRecords.")
                    counts = {"seen": 0, "created": 0, "updated": 0, "deleted": 0}
                    for item in container.findall("oai:record", NS):
                        header = item.find("oai:header", NS)
                        if header is None:
                            continue
                        identifier_node = header.find("oai:identifier", NS)
                        if identifier_node is None or not (identifier_node.text or "").strip():
                            continue
                        identifier = identifier_node.text.strip()
                        datestamp_node = header.find("oai:datestamp", NS)
                        datestamp = (datestamp_node.text or "").strip() if datestamp_node is not None else None
                        set_specs = [(n.text or "").strip() for n in header.findall("oai:setSpec", NS)]
                        deleted = header.attrib.get("status") == "deleted"
                        outcome = upsert_source_record(
                            db, repository_id=repository.id, identifier=identifier,
                            datestamp=datestamp, set_specs=set_specs,
                            metadata_prefix=job.metadata_prefix,
                            original_xml=ET.tostring(item, encoding="unicode"), deleted=deleted,
                        )
                        source_record = db.scalar(select(SourceRecord).where(
                            SourceRecord.repository_id == repository.id,
                            SourceRecord.oai_identifier == identifier,
                        ))
                        if source_record is not None:
                            normalize_source_record(db, source_record)
                        counts["seen"] += 1
                        if outcome == "created":
                            counts["created"] += 1
                        elif outcome == "updated":
                            counts["updated"] += 1
                        if deleted:
                            counts["deleted"] += 1

                    token_node = container.find("oai:resumptionToken", NS)
                    next_token = (token_node.text or "").strip() if token_node is not None else ""
                    job.records_seen += counts["seen"]
                    job.records_created += counts["created"]
                    job.records_updated += counts["updated"]
                    job.records_deleted += counts["deleted"]
                    job.pages_completed += 1
                    job.resumption_token = next_token or None
                    log_job(db, job.id, f"Page {job.pages_completed}: {counts['seen']} records processed.")
                    db.commit()
                    if not next_token:
                        break
                    token = next_token
                    first_page = False

            job.status = "completed"
            job.finished_at = datetime.now(UTC)
            job.resumption_token = None
            log_job(db, job.id, "Harvest completed.")
            db.commit()
            return {"job_id": job_id, "status": job.status, "records_seen": job.records_seen}
        except SoftTimeLimitExceeded:
            job.status = "paused"
            job.error_message = "Worker time limit reached; resume from saved checkpoint."
            log_job(db, job.id, job.error_message, "WARNING")
            db.commit()
            raise
        except OAITransportError as exc:
            job.error_message = str(exc)[:4000]
            if self.request.retries >= 3:
                job.status = "failed"
                job.finished_at = datetime.now(UTC)
                log_job(db, job.id, f"Transport retries exhausted: {exc}", "ERROR")
                db.commit()
                raise
            job.status = "queued"
            log_job(db, job.id, f"Transient transport failure; retry scheduled: {exc}", "WARNING")
            db.commit()
            raise self.retry(
                exc=exc,
                countdown=min(30 * (2 ** self.request.retries), 300),
                max_retries=3,
            )
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)[:4000]
            job.finished_at = datetime.now(UTC)
            log_job(db, job.id, f"Harvest failed: {job.error_message}", "ERROR")
            db.commit()
            raise
    finally:
        if locked and lock_key is not None:
            db.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": lock_key})
            db.commit()
        db.close()
