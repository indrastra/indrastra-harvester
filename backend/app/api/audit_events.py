from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.dependencies import require_admin
from backend.app.db.session import get_db
from backend.app.users.models import AuditEvent

router = APIRouter(
    prefix="/audit-events",
    tags=["audit"],
    dependencies=[Depends(require_admin)],
)
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("")
def list_audit_events(
    db: DatabaseSession,
    action: str | None = Query(default=None, max_length=128),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
):
    query = select(AuditEvent).order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
    if action:
        query = query.where(AuditEvent.action == action)
    events = db.scalars(query.offset(offset).limit(limit)).all()
    return [
        {
            "id": event.id,
            "actor_user_id": event.actor_user_id,
            "action": event.action,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "details": event.details,
            "created_at": event.created_at,
        }
        for event in events
    ]
