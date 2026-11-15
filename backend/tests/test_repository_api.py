import os

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app

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


def test_repository_write_requires_admin_token():
    response = client.post(
        "/api/v1/repositories",
        json={"name": "Example", "endpoint": "https://1.1.1.1/oai", "validate_endpoint": False},
    )
    assert response.status_code == 401


def test_repository_can_be_registered_without_live_probe():
    response = client.post(
        "/api/v1/repositories",
        headers={"Authorization": "Bearer test-admin-token-that-is-at-least-32-chars"},
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
    response = client.post(
        "/api/v1/repositories",
        headers={"Authorization": "Bearer test-admin-token-that-is-at-least-32-chars"},
        json={
            "name": "Duplicate Repository",
            "endpoint": "https://1.1.1.1/oai",
            "validate_endpoint": False,
        },
    )
    assert response.status_code == 409
