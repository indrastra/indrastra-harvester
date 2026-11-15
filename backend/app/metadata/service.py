from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.harvest.models import SourceRecord
from backend.app.metadata.models import NormalizedRecord
from backend.app.metadata.normalizers import normalize_metadata


def normalize_source_record(db: Session, source_record: SourceRecord) -> NormalizedRecord | None:
    """Upsert the normalized projection; source XML remains the authoritative record."""
    if source_record.is_deleted:
        normalized = db.scalar(select(NormalizedRecord).where(
            NormalizedRecord.source_record_id == source_record.id
        ))
        if normalized is not None:
            normalized.is_deleted = True
            normalized.normalized_at = datetime.now(UTC)
        return normalized

    result = normalize_metadata(source_record.original_xml, source_record.metadata_prefix)
    normalized = db.scalar(select(NormalizedRecord).where(
        NormalizedRecord.source_record_id == source_record.id
    ))
    now = datetime.now(UTC)
    if normalized is None:
        normalized = NormalizedRecord(
            source_record_id=source_record.id,
            repository_id=source_record.repository_id,
            oai_identifier=source_record.oai_identifier,
            metadata_prefix=source_record.metadata_prefix,
            schema=result.schema,
            normalization_version=result.normalization_version,
            data=result.to_dict(),
            title=result.title,
            creators=result.creators,
            subjects=result.subjects,
            publication_date=result.publication_dates[0] if result.publication_dates else None,
            resource_type=result.resource_types[0] if result.resource_types else None,
            is_deleted=False,
            normalized_at=now,
        )
        db.add(normalized)
    else:
        normalized.metadata_prefix = source_record.metadata_prefix
        normalized.schema = result.schema
        normalized.normalization_version = result.normalization_version
        normalized.data = result.to_dict()
        normalized.title = result.title
        normalized.creators = result.creators
        normalized.subjects = result.subjects
        normalized.publication_date = result.publication_dates[0] if result.publication_dates else None
        normalized.resource_type = result.resource_types[0] if result.resource_types else None
        normalized.is_deleted = False
        normalized.normalized_at = now
    return normalized
