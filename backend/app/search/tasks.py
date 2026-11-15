from datetime import UTC, datetime

from celery.exceptions import MaxRetriesExceededError
from sqlalchemy import select

from backend.app.db.session import SessionLocal
from backend.app.metadata.models import NormalizedRecord
from backend.app.search.models import IndexOutbox
from backend.app.search.service import get_opensearch_client, index_normalized_record
from backend.app.worker import celery_app


@celery_app.task(
    bind=True, name="search.process_outbox", max_retries=5, acks_late=True,
    soft_time_limit=120, time_limit=180,
)
def process_index_outbox(self, outbox_id: int) -> dict[str, int | str]:
    db = SessionLocal()
    try:
        event = db.get(IndexOutbox, outbox_id)
        if event is None:
            return {"outbox_id": outbox_id, "status": "missing"}
        if event.status == "completed":
            return {"outbox_id": outbox_id, "status": "completed"}
        event.status = "processing"
        event.attempts += 1
        db.commit()
        try:
            record = db.scalar(select(NormalizedRecord).where(
                NormalizedRecord.source_record_id == event.source_record_id
            ))
            if record is None or record.is_deleted:
                client = get_opensearch_client()
                from backend.app.search.service import INDEX_NAME, ensure_index
                ensure_index(client)
                client.delete(index=INDEX_NAME, id=str(event.source_record_id), ignore=[404])
            else:
                index_normalized_record(get_opensearch_client(), record)
            event.status = "completed"
            event.last_error = None
            event.processed_at = datetime.now(UTC)
            db.commit()
            return {"outbox_id": outbox_id, "status": "completed"}
        except Exception as exc:
            event.last_error = str(exc)[:4000]
            if self.request.retries >= self.max_retries:
                event.status = "failed"
                event.processed_at = datetime.now(UTC)
                db.commit()
                raise
            event.status = "pending"
            db.commit()
            try:
                raise self.retry(
                    exc=exc,
                    countdown=min(15 * (2 ** self.request.retries), 300),
                    max_retries=5,
                )
            except MaxRetriesExceededError:
                event.status = "failed"
                db.commit()
                raise
    finally:
        db.close()
