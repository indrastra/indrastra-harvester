import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.repositories.models import Repository

os.environ["ADMIN_API_TOKEN"] = "test-admin-token-that-is-at-least-32-chars"

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_database():
    with TestingSessionLocal.begin() as db:
        db.execute(delete(Repository))


def admin_headers():
    return {"Authorization": "Bearer test-admin-token-that-is-at-least-32-chars"}


def test_repository_reads_require_admin_token():
    assert client.get("/api/v1/repositories").status_code == 401


def test_repository_write_requires_admin_token():
    response = client.post(
        "/api/v1/repositories",
        json={"name": "Example", "endpoint": "https://1.1.1.1/oai", "validate_endpoint": False},
    )
    assert response.status_code == 401


def test_repository_can_be_registered_without_live_probe():
    response = client.post(
        "/api/v1/repositories",
        headers=admin_headers(),
        json={
            "name": "Example Repository",
            "endpoint": "https://1.1.1.1/oai",
            "validate_endpoint": False,
        },
    )
    assert response.status_code == 201
    assert response.json()["validation_status"] == "pending"
    assert response.json()["is_enabled"] is True


def test_repository_endpoint_duplicate_returns_conflict():
    payload = {
        "name": "Example Repository",
        "endpoint": "https://1.1.1.1/oai",
        "validate_endpoint": False,
    }
    first = client.post("/api/v1/repositories", headers=admin_headers(), json=payload)
    second = client.post("/api/v1/repositories", headers=admin_headers(), json=payload)
    assert first.status_code == 201
    assert second.status_code == 409


def test_harvest_schedule_can_be_created_listed_and_disabled():
    repository_response = client.post(
        "/api/v1/repositories",
        headers=admin_headers(),
        json={
            "name": "Scheduled Repository",
            "endpoint": "https://1.1.1.1/scheduled-oai",
            "validate_endpoint": False,
        },
    )
    assert repository_response.status_code == 201
    repository_id = repository_response.json()["id"]

    schedule_response = client.post(
        "/api/v1/schedules",
        headers=admin_headers(),
        json={
            "repository_id": repository_id,
            "metadata_prefix": "oai_dc",
            "frequency": "daily",
            "start_at": "2026-11-15T12:00:00Z",
        },
    )
    assert schedule_response.status_code == 201
    schedule = schedule_response.json()
    assert schedule["enabled"] is True
    assert schedule["frequency"] == "daily"

    listed = client.get("/api/v1/schedules", headers=admin_headers())
    assert listed.status_code == 200
    assert any(item["id"] == schedule["id"] for item in listed.json())

    disabled = client.patch(
        f"/api/v1/schedules/{schedule['id']}",
        headers=admin_headers(),
        json={"enabled": False},
    )
    assert disabled.status_code == 200
    assert disabled.json()["enabled"] is False


def test_analytics_summary_requires_admin_and_returns_collection_metrics():
    unauthorized = client.get("/api/v1/analytics/summary")
    assert unauthorized.status_code == 401
    response = client.get("/api/v1/analytics/summary", headers=admin_headers())
    assert response.status_code == 200
    payload = response.json()
    assert "repositories" in payload
    assert "records" in payload
    assert "harvest_jobs" in payload
    assert "index_outbox" in payload


def test_public_csv_export_returns_download_response(monkeypatch):
    from unittest.mock import MagicMock

    fake_client = MagicMock()
    fake_client.indices.exists.return_value = True
    fake_client.search.return_value = {
        "hits": {"total": {"value": 0}, "hits": []}
    }
    monkeypatch.setattr(
        "backend.app.api.exports.get_opensearch_client",
        lambda: fake_client,
    )
    response = client.get("/api/v1/exports?format=csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert response.headers["x-exported-records"] == "0"
    assert "attachment" in response.headers["content-disposition"]
