from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.dependencies import require_admin
from backend.app.db.session import get_db
from backend.app.search.models import IndexOutbox
from backend.app.search.tasks import process_index_outbox

router = APIRouter(
    prefix="/index",
    tags=["indexing"],
    dependencies=[Depends(require_admin)],
)
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post("/dispatch")
def dispatch_pending_index_events(
    db: DatabaseSession,
    limit: int = Query(default=100, ge=1, le=1000),
):
    events = db.scalars(
        select(IndexOutbox)
        .where(IndexOutbox.status == "pending")
        .order_by(IndexOutbox.created_at, IndexOutbox.id)
        .limit(limit)
    ).all()
    queued = 0
    for event in events:
        try:
            process_index_outbox.delay(event.id)
            queued += 1
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Index queue unavailable after queuing {queued} events.",
            ) from exc
    return {"queued": queued, "remaining_pending": max(0, len(events) - queued)}
