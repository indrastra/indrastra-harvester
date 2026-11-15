from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["x-request-id"]
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_readiness_endpoint_when_dependencies_are_available(monkeypatch) -> None:
    database_context = MagicMock()
    database_session = database_context.__enter__.return_value
    redis_client = MagicMock()
    search_client = MagicMock()

    monkeypatch.setattr("backend.app.main.SessionLocal", lambda: database_context)
    monkeypatch.setattr("backend.app.main.Redis.from_url", lambda *args, **kwargs: redis_client)
    monkeypatch.setattr("backend.app.main.get_opensearch_client", lambda: search_client)

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"database": "ok", "redis": "ok", "opensearch": "ok"},
    }
    database_session.execute.assert_called_once()
    redis_client.ping.assert_called_once()
    search_client.cluster.health.assert_called_once_with(request_timeout=3)
    redis_client.close.assert_called_once()
    search_client.close.assert_called_once()


def test_readiness_endpoint_returns_503_when_dependency_is_unavailable(monkeypatch) -> None:
    database_context = MagicMock()
    redis_client = MagicMock()
    redis_client.ping.side_effect = OSError("Redis unavailable")
    search_client = MagicMock()

    monkeypatch.setattr("backend.app.main.SessionLocal", lambda: database_context)
    monkeypatch.setattr("backend.app.main.Redis.from_url", lambda *args, **kwargs: redis_client)
    monkeypatch.setattr("backend.app.main.get_opensearch_client", lambda: search_client)

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "status": "not_ready",
        "checks": {"database": "ok", "redis": "unavailable", "opensearch": "ok"},
    }
    redis_client.close.assert_called_once()
    search_client.close.assert_called_once()
