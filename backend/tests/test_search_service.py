from datetime import UTC, datetime
from unittest.mock import MagicMock

from backend.app.metadata.models import NormalizedRecord
from backend.app.search.service import build_search_document, search_records


def test_search_document_maps_canonical_metadata():
    record = NormalizedRecord(
        source_record_id=77,
        repository_id=4,
        oai_identifier="oai:repo:77",
        metadata_prefix="oai_dc",
        schema="oai_dc",
        normalization_version="1.0.0",
        data={
            "title": ["Research on Open Repositories"],
            "creators": ["Jane Doe"],
            "contributors": [],
            "subjects": ["Open science"],
            "descriptions": ["An abstract"],
            "publishers": ["Example Press"],
            "publication_dates": ["2024-03-10"],
            "resource_types": ["Article"],
            "formats": [],
            "identifiers": ["https://doi.org/10.1234/example"],
            "languages": ["en"],
            "relations": [],
            "rights": [],
            "coverages": [],
        },
        normalized_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    document = build_search_document(record)
    assert document["title"] == ["Research on Open Repositories"]
    assert document["repository_id"] == 4
    assert document["publication_year"] == 2024
    assert document["identifiers"] == ["https://doi.org/10.1234/example"]


def test_search_query_uses_filters_and_bounded_pagination():
    client = MagicMock()
    client.indices.exists.return_value = True
    client.search.return_value = {
        "hits": {
            "total": {"value": 1},
            "hits": [{
                "_id": "77",
                "_score": 4.2,
                "_source": {
                    "title": ["Research article"],
                    "creators": ["Jane Doe"],
                    "subjects": ["Open science"],
                    "publication_dates": ["2024"],
                    "resource_types": ["Article"],
                    "identifiers": ["doi:10.1/example"],
                    "repository_id": 4,
                    "oai_identifier": "oai:repo:77",
                },
            }],
        }
    }
    result = search_records(
        client,
        query="open repositories",
        page=2,
        page_size=10,
        repository_id=4,
        resource_type="Article",
        from_year=2020,
        until_year=2025,
        sort="newest",
    )
    body = client.search.call_args.kwargs["body"]
    assert body["from"] == 10
    assert body["size"] == 10
    assert {"term": {"repository_id": 4}} in body["query"]["bool"]["filter"]
    assert {"term": {"resource_types": "Article"}} in body["query"]["bool"]["filter"]
    assert {"range": {"publication_year": {"gte": 2020, "lte": 2025}}} in body["query"]["bool"]["filter"]
    assert result["total"] == 1
    assert result["results"][0]["id"] == "77"
