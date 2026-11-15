from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.harvest.models import SourceRecord
from backend.app.main import app
from backend.app.metadata.models import NormalizedRecord
from backend.app.repositories.models import Repository


def test_public_record_detail_exposes_metadata_and_provenance_but_hides_deleted_records():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        repository = Repository(
            name="Public Repository",
            endpoint="https://example.org/oai",
            organization="Example University",
            country="US",
        )
        db.add(repository)
        db.flush()
        source = SourceRecord(
            repository_id=repository.id,
            oai_identifier="oai:example:1",
            datestamp="2026-01-01",
            metadata_prefix="oai_dc",
            original_xml="<record/>",
            is_deleted=False,
        )
        db.add(source)
        db.flush()
        normalized = NormalizedRecord(
            source_record_id=source.id,
            repository_id=repository.id,
            oai_identifier=source.oai_identifier,
            metadata_prefix="oai_dc",
            schema="oai_dc",
            normalization_version="1.0.0",
            data={"title": ["Example scholarly article"], "creators": ["Jane Doe"]},
            title=["Example scholarly article"],
            creators=["Jane Doe"],
            subjects=[],
            is_deleted=False,
            normalized_at=datetime.now(UTC),
        )
        db.add(normalized)
        db.commit()
        source_id = source.id

    def override_get_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)
        response = client.get(f"/api/v1/records/{source_id}")
        assert response.status_code == 200
        payload = response.json()
        assert payload["metadata"]["title"] == ["Example scholarly article"]
        assert payload["repository"]["name"] == "Public Repository"
        assert payload["oai_identifier"] == "oai:example:1"

        with Session(engine) as db:
            source = db.get(SourceRecord, source_id)
            source.is_deleted = True
            db.commit()

        hidden = client.get(f"/api/v1/records/{source_id}")
        assert hidden.status_code == 404
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
