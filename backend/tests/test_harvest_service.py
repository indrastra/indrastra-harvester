from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.harvest.models import SourceRecord, SourceRecordVersion
from backend.app.harvest.service import upsert_source_record
from backend.app.metadata.models import NormalizedRecord
from backend.app.metadata.service import normalize_source_record
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
        versions = db.query(SourceRecordVersion).filter_by(source_record_id=record.id).order_by(
            SourceRecordVersion.version_number
        ).all()
        assert [version.version_number for version in versions] == [1, 2]
        assert versions[0].is_deleted is False
        assert versions[1].is_deleted is True
    engine.dispose()


def test_normalized_projection_updates_and_respects_deletion_tombstone():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    xml = """<record xmlns:dc="http://purl.org/dc/elements/1.1/">
    <header><identifier>oai:test:2</identifier></header>
    <metadata><dc><dc:title>Research record</dc:title><dc:creator>Researcher</dc:creator></dc></metadata>
    </record>"""
    with Session(engine) as db:
        repo = Repository(name="Normalization Test", endpoint="https://example.org/oai")
        db.add(repo)
        db.commit()
        args = {
            "repository_id": repo.id, "identifier": "oai:test:2", "datestamp": "2026-01-01",
            "set_specs": [], "metadata_prefix": "oai_dc", "original_xml": xml, "deleted": False,
        }
        upsert_source_record(db, **args)
        source = db.query(SourceRecord).filter_by(oai_identifier="oai:test:2").one()
        normalized = normalize_source_record(db, source)
        db.commit()
        assert normalized is not None
        assert normalized.title == ["Research record"]
        assert normalized.creators == ["Researcher"]
        args["original_xml"] = '<record><header status="deleted"/></record>'
        args["deleted"] = True
        upsert_source_record(db, **args)
        normalize_source_record(db, source)
        db.commit()
        assert db.query(NormalizedRecord).one().is_deleted is True
    engine.dispose()
