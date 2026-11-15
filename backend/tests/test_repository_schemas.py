import pytest
from pydantic import ValidationError

from backend.app.repositories.schemas import RepositoryCreate


def test_repository_create_normalizes_endpoint():
    item = RepositoryCreate(name="Example Repo", endpoint="HTTPS://1.1.1.1")
    assert item.endpoint == "https://1.1.1.1/"


def test_repository_create_rejects_localhost():
    with pytest.raises(ValidationError):
        RepositoryCreate(name="Local Repo", endpoint="http://127.0.0.1/oai")
