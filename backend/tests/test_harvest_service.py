from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.harvest.models import SourceRecord
from backend.app.harvest.service import upsert_source_record
from backend.app.repositories.models import Repository


def test_source_record_upsert_is_idempotent_and_repository_scoped():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        repo = Repository(name="Test", endpoint="https://example.org/oai")
        db.add(repo)
        db.commit()
        args = {
            "repository_id": repo.id, "identifier": "oai:test:1", "datestamp": "2026-01-01",
            "set_specs": ["articles"], "metadata_prefix": "oai_dc",
            "original_xml": "<record/>", "deleted": False,
        }
        assert upsert_source_record(db, **args) == "created"
        db.commit()
        assert upsert_source_record(db, **args) == "unchanged"
        db.commit()
        args["deleted"] = True
        args["original_xml"] = '<record status="deleted"/>'
        assert upsert_source_record(db, **args) == "updated"
        db.commit()
        record = db.query(SourceRecord).one()
        assert record.is_deleted is True
        assert record.source_status == "deleted"
        assert record.oai_identifier == "oai:test:1"
    engine.dispose()
