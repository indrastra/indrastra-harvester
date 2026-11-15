# Search indexing and discovery API

## Index architecture

PostgreSQL remains the authoritative record store. OpenSearch is a derived projection and can be rebuilt from normalized records. The index never stores original source XML.

The current index name is configured by `OPENSEARCH_INDEX` (default: `scholarly-records`). The index uses a versioned mapping with fields for title, creators, contributors, subjects, descriptions, publishers, publication dates/year, resource types, identifiers, languages, relations, rights, and coverage.

## Transactional outbox

Metadata normalization writes an `index_outbox` event in the same database transaction as the normalized record. After a harvest page commits, the worker dispatches pending outbox events to Celery. This avoids losing an indexing request when the database commit succeeds but a direct OpenSearch call fails.

Events have pending, processing, completed, or failed status, attempt counts, and last-error details. Repeated processing is idempotent because OpenSearch document IDs are stable source-record IDs. A deleted source tombstone removes its document from the search index without deleting the source history.

If Redis or the worker queue is unavailable, pending outbox events remain in PostgreSQL and an administrator can dispatch them later.

## Public search API

`GET /api/v1/search`

Query parameters:

| Parameter | Meaning |
|---|---|
| `q` | Search text; supports simple query syntax |
| `page` | 1-based page number |
| `page_size` | 1–100 results |
| `repository_id` | Filter to one repository |
| `resource_type` | Exact resource type filter |
| `from_year`, `until_year` | Publication-year range |
| `sort` | relevance, newest, or oldest |

Example:

```http
GET /api/v1/search?q=open%20repositories&page=1&page_size=20&sort=newest
```

The response includes a total hit count, pagination information, source repository ID, OAI identifier, normalized bibliographic fields, and highlights. Search returns 503 if OpenSearch is unavailable; it does not silently return stale or empty results as if the service succeeded.

## Administrative outbox dispatch

`POST /api/v1/index/dispatch?limit=100`

Requires the administrative bearer token. Queues up to the requested number of pending events. It does not mutate or delete source records.

## Operational notes

- Configure `OPENSEARCH_URL` to the private service URL. Optional basic authentication uses `OPENSEARCH_USERNAME` and `OPENSEARCH_PASSWORD`.
- HTTPS endpoints enable certificate verification.
- Keep OpenSearch private; do not expose its administrative port to the public internet.
- OpenSearch indexing is asynchronous. A successful harvest means source data and its outbox event committed, not necessarily that every document is already searchable.
- Monitor failed/pending outbox events and worker retries.
- Rebuild/reindex management and index mapping version migrations are future operational features.
