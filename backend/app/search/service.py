import os
from typing import Any
from urllib.parse import urlsplit

from opensearchpy import OpenSearch
from sqlalchemy.orm import Session

from backend.app.metadata.models import NormalizedRecord

INDEX_NAME = os.getenv("OPENSEARCH_INDEX", "scholarly-records")
INDEX_MAPPING: dict[str, Any] = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "scholarly_text": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"],
                }
            }
        },
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "source_record_id": {"type": "long"},
            "repository_id": {"type": "long"},
            "oai_identifier": {"type": "keyword"},
            "metadata_prefix": {"type": "keyword"},
            "schema": {"type": "keyword"},
            "title": {"type": "text", "analyzer": "scholarly_text", "fields": {"keyword": {"type": "keyword", "ignore_above": 512}}},
            "creators": {"type": "text", "analyzer": "scholarly_text"},
            "contributors": {"type": "text", "analyzer": "scholarly_text"},
            "subjects": {"type": "text", "analyzer": "scholarly_text"},
            "descriptions": {"type": "text", "analyzer": "scholarly_text"},
            "publishers": {"type": "text", "analyzer": "scholarly_text"},
            "publication_dates": {"type": "keyword"},
            "publication_year": {"type": "integer"},
            "resource_types": {"type": "keyword"},
            "formats": {"type": "keyword"},
            "identifiers": {"type": "keyword"},
            "languages": {"type": "keyword"},
            "relations": {"type": "keyword"},
            "rights": {"type": "text", "analyzer": "scholarly_text"},
            "coverages": {"type": "text", "analyzer": "scholarly_text"},
            "normalization_version": {"type": "keyword"},
            "normalized_at": {"type": "date"},
        },
    },
}


def get_opensearch_client() -> OpenSearch:
    parsed = urlsplit(os.getenv("OPENSEARCH_URL", "http://localhost:9200"))
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("OPENSEARCH_URL must be a valid HTTP or HTTPS URL.")
    username = os.getenv("OPENSEARCH_USERNAME")
    password = os.getenv("OPENSEARCH_PASSWORD")
    auth = (username, password) if username and password else None
    return OpenSearch(
        hosts=[{"host": parsed.hostname, "port": parsed.port or (443 if parsed.scheme == "https" else 9200)}],
        http_auth=auth,
        use_ssl=parsed.scheme == "https",
        verify_certs=parsed.scheme == "https",
        timeout=10,
        max_retries=2,
        retry_on_timeout=True,
        http_compress=True,
    )


def ensure_index(client: OpenSearch) -> None:
    if not client.indices.exists(index=INDEX_NAME):
        client.indices.create(index=INDEX_NAME, body=INDEX_MAPPING)


def build_search_document(record: NormalizedRecord) -> dict[str, Any]:
    data = record.data
    dates = data.get("publication_dates", [])
    first_date = dates[0] if dates else None
    year = None
    if isinstance(first_date, str) and len(first_date) >= 4 and first_date[:4].isdigit():
        year = int(first_date[:4])
    return {
        "source_record_id": record.source_record_id,
        "repository_id": record.repository_id,
        "oai_identifier": record.oai_identifier,
        "metadata_prefix": record.metadata_prefix,
        "schema": record.schema,
        "title": data.get("title", []),
        "creators": data.get("creators", []),
        "contributors": data.get("contributors", []),
        "subjects": data.get("subjects", []),
        "descriptions": data.get("descriptions", []),
        "publishers": data.get("publishers", []),
        "publication_dates": dates,
        "publication_year": year,
        "resource_types": data.get("resource_types", []),
        "formats": data.get("formats", []),
        "identifiers": data.get("identifiers", []),
        "languages": data.get("languages", []),
        "relations": data.get("relations", []),
        "rights": data.get("rights", []),
        "coverages": data.get("coverages", []),
        "normalization_version": record.normalization_version,
        "normalized_at": record.normalized_at.isoformat(),
    }


def index_normalized_record(client: OpenSearch, record: NormalizedRecord) -> None:
    ensure_index(client)
    if record.is_deleted:
        client.delete(index=INDEX_NAME, id=str(record.source_record_id), ignore=[404])
        return
    client.index(
        index=INDEX_NAME,
        id=str(record.source_record_id),
        body=build_search_document(record),
        refresh=False,
    )


def search_records(
    client: OpenSearch, *, query: str, page: int, page_size: int,
    repository_id: int | None = None, resource_type: str | None = None,
    from_year: int | None = None, until_year: int | None = None, sort: str = "relevance",
) -> dict[str, Any]:
    ensure_index(client)
    filters: list[dict[str, Any]] = []
    if repository_id is not None:
        filters.append({"term": {"repository_id": repository_id}})
    if resource_type:
        filters.append({"term": {"resource_types": resource_type}})
    year_range: dict[str, int] = {}
    if from_year is not None:
        year_range["gte"] = from_year
    if until_year is not None:
        year_range["lte"] = until_year
    if year_range:
        filters.append({"range": {"publication_year": year_range}})

    must = []
    if query.strip():
        must.append({
            "simple_query_string": {
                "query": query,
                "fields": [
                    "title^5", "creators^3", "subjects^2", "descriptions",
                    "identifiers", "publishers",
                ],
                "default_operator": "and",
                "flags": "OR|AND|PREFIX|PHRASE",
            }
        })
    else:
        must.append({"match_all": {}})

    sort_options: list[dict[str, Any]]
    if sort == "newest":
        sort_options = [{"publication_year": {"order": "desc", "missing": "_last"}}, {"_score": "desc"}]
    elif sort == "oldest":
        sort_options = [{"publication_year": {"order": "asc", "missing": "_last"}}, {"_score": "desc"}]
    else:
        sort_options = ["_score", {"publication_year": {"order": "desc", "missing": "_last"}}]

    response = client.search(
        index=INDEX_NAME,
        body={
            "query": {"bool": {"must": must, "filter": filters}},
            "from": (page - 1) * page_size,
            "size": page_size,
            "sort": sort_options,
            "highlight": {"fields": {"title": {}, "descriptions": {}}},
        },
    )
    hits = response.get("hits", {})
    total = hits.get("total", 0)
    total_value = total.get("value", 0) if isinstance(total, dict) else total
    results = []
    for hit in hits.get("hits", []):
        source = hit.get("_source", {})
        results.append({
            "id": hit.get("_id"),
            "score": hit.get("_score"),
            "title": source.get("title", []),
            "creators": source.get("creators", []),
            "subjects": source.get("subjects", []),
            "publication_dates": source.get("publication_dates", []),
            "resource_types": source.get("resource_types", []),
            "identifiers": source.get("identifiers", []),
            "repository_id": source.get("repository_id"),
            "oai_identifier": source.get("oai_identifier"),
            "highlight": hit.get("highlight", {}),
        })
    return {"total": total_value, "page": page, "page_size": page_size, "results": results}


def queue_reindex(db: Session, source_record_id: int) -> None:
    from backend.app.search.models import IndexOutbox

    db.add(IndexOutbox(
        source_record_id=source_record_id,
        event_type="upsert",
        status="pending",
    ))
