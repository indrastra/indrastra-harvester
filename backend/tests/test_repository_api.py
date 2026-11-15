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
