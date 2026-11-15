from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.harvest.models import SourceRecord
from backend.app.metadata.models import NormalizedRecord
from backend.app.repositories.models import Repository

router = APIRouter(prefix="/records", tags=["records"])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/{source_record_id}")
def get_public_record(source_record_id: int, db: DatabaseSession):
    row = db.execute(
        select(NormalizedRecord, SourceRecord, Repository)
        .join(SourceRecord, SourceRecord.id == NormalizedRecord.source_record_id)
        .join(Repository, Repository.id == SourceRecord.repository_id)
        .where(
            NormalizedRecord.source_record_id == source_record_id,
            NormalizedRecord.is_deleted.is_(False),
            SourceRecord.is_deleted.is_(False),
            Repository.is_enabled.is_(True),
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Record not found.")
    normalized, source, repository = row
    return {
        "id": normalized.source_record_id,
        "repository": {
            "id": repository.id,
            "name": repository.name,
            "organization": repository.organization,
            "country": repository.country,
            "endpoint": repository.endpoint,
        },
        "oai_identifier": source.oai_identifier,
        "metadata_prefix": source.metadata_prefix,
        "datestamp": source.datestamp,
        "set_specs": source.set_specs.split("\n") if source.set_specs else [],
        "metadata": normalized.data,
        "normalization_version": normalized.normalization_version,
        "first_harvested_at": source.first_harvested_at,
        "last_harvested_at": source.last_harvested_at,
        "source_status": source.source_status,
    }
