import os
import uuid
import xml.etree.ElementTree as ET
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from backend.app.db.session import SessionLocal, get_db
from backend.app.harvest.models import HarvestJob, SourceRecord, SourceRecordVersion
from backend.app.harvest.tasks import run_harvest
from backend.app.main import app
from backend.app.metadata.models import NormalizedRecord
from backend.app.repositories.models import Repository
from backend.app.search.models import IndexOutbox
from backend.app.search.service import INDEX_NAME, get_opensearch_client, search_records
from backend.app.search.tasks import process_index_outbox

pytestmark = pytest.mark.skipif(
    os.getenv("HARVESTER_INTEGRATION") != "1",
    reason="Requires PostgreSQL, Redis and OpenSearch integration services.",
)

OAI_XML = """<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
 xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
 xmlns:dc="http://purl.org/dc/elements/1.1/">
 <ListRecords>
  <record>
   <header><identifier>oai:integration:record-001</identifier><datestamp>2026-11-16</datestamp><setSpec>articles</setSpec></header>
   <metadata><oai_dc:dc>
    <dc:title>Integrated Harvester Acceptance Record</dc:title>
    <dc:creator>Integration Test Author</dc:creator>
    <dc:subject>repository harvesting</dc:subject>
    <dc:date>2026-11-16</dc:date>
    <dc:type>Article</dc:type>
    <dc:identifier>https://example.org/records/acceptance-001</dc:identifier>
   </oai_dc:dc></metadata>
  </record>
  <resumptionToken />
 </ListRecords>
</OAI-PMH>
"""


class FixtureOAIClient:
    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def request(self, verb: str, **params):
        assert verb == "ListRecords"
        return SimpleNamespace(root=ET.fromstring(OAI_XML))


def test_integrated_harvest_normalize_index_search_and_public_record(monkeypatch):
    """Exercise the persistent pipeline against real PostgreSQL and OpenSearch."""
    from backend.app.harvest import tasks as harvest_tasks

    suffix = uuid.uuid4().hex
    repository = Repository(
        name=f"Integration fixture {suffix}",
        endpoint=f"https://fixture-{suffix}.example/oai",
        validation_status="valid",
        is_enabled=True,
        metadata_formats=[{"metadata_prefix": "oai_dc"}],
        sets=[],
    )
    with SessionLocal.begin() as db:
        db.add(repository)
        db.flush()
        job = HarvestJob(repository_id=repository.id, metadata_prefix="oai_dc")
        db.add(job)
        db.flush()
        repository_id, job_id = repository.id, job.id

    monkeypatch.setattr(harvest_tasks, "OAIPMHClient", FixtureOAIClient)
    monkeypatch.setattr(process_index_outbox, "delay", lambda *_args, **_kwargs: None)

    try:
        result = run_harvest.apply(args=[job_id], throw=True).get()
        assert result["status"] == "completed"
        assert result["records_seen"] == 1

        with SessionLocal() as db:
            source = db.scalar(select(SourceRecord).where(
                SourceRecord.repository_id == repository_id,
                SourceRecord.oai_identifier == "oai:integration:record-001",
            ))
            assert source is not None
            source_id = source.id
            normalized = db.scalar(select(NormalizedRecord).where(
                NormalizedRecord.source_record_id == source_id
            ))
            assert normalized is not None
            assert normalized.data["title"] == ["Integrated Harvester Acceptance Record"]
            outbox = db.scalar(select(IndexOutbox).where(
                IndexOutbox.source_record_id == source_id,
                IndexOutbox.status == "pending",
            ))
            assert outbox is not None
            outbox_id = outbox.id

        indexed = process_index_outbox.apply(args=[outbox_id], throw=True).get()
        assert indexed["status"] == "completed"

        search_client = get_opensearch_client()
        try:
            search_client.indices.refresh(index=INDEX_NAME)
            results = search_records(
                search_client,
                query="Integrated Harvester Acceptance Record",
                page=1,
                page_size=10,
            )
            assert results["total"] == 1
            assert results["results"][0]["id"] == str(source_id)
        finally:
            search_client.close()

        def database_override():
            db = SessionLocal()
            try:
                yield db
            finally:
                db.close()

        monkeypatch.setitem(app.dependency_overrides, get_db, database_override)
        client = TestClient(app)
        public_record = client.get(f"/api/v1/records/{source_id}")
        assert public_record.status_code == 200
        assert public_record.json()["metadata"]["title"] == [
            "Integrated Harvester Acceptance Record"
        ]
        public_search = client.get(
            "/api/v1/search",
            params={"q": "Integrated Harvester Acceptance Record"},
        )
        assert public_search.status_code == 200
        assert public_search.json()["total"] == 1
    finally:
        with SessionLocal.begin() as db:
            source_ids = list(db.scalars(select(SourceRecord.id).where(
                SourceRecord.repository_id == repository_id
            )).all())
            if source_ids:
                db.execute(delete(IndexOutbox).where(IndexOutbox.source_record_id.in_(source_ids)))
                db.execute(delete(NormalizedRecord).where(NormalizedRecord.source_record_id.in_(source_ids)))
                db.execute(delete(SourceRecordVersion).where(SourceRecordVersion.source_record_id.in_(source_ids)))
                db.execute(delete(SourceRecord).where(SourceRecord.id.in_(source_ids)))
            db.execute(delete(HarvestJob).where(HarvestJob.id == job_id))
            db.execute(delete(Repository).where(Repository.id == repository_id))

        cleanup_client = get_opensearch_client()
        try:
            cleanup_client.delete_by_query(
                index=INDEX_NAME,
                body={"query": {"term": {"oai_identifier": "oai:integration:record-001"}}},
                ignore=[404],
                refresh=True,
            )
        finally:
            cleanup_client.close()
