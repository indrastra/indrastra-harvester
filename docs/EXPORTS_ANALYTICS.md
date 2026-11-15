# Exports and collection analytics

## Public exports

The export API is public and uses the same OpenSearch query/filter semantics as discovery search.

`GET /api/v1/exports`

| Parameter | Purpose |
|---|---|
| `format` | `json`, `csv`, `xml`, or `oai_dc` |
| `q` | Full-text query |
| `repository_id` | Restrict to one repository |
| `resource_type` | Exact resource type |
| `from_year`, `until_year` | Publication year range |
| `page`, `limit` | Pagination; maximum 1,000 records per request |
| `sort` | relevance, newest, oldest |

The API exports only records that still exist in PostgreSQL, are not tombstoned, and belong to enabled repositories. PostgreSQL remains authoritative; OpenSearch supplies the matching IDs and ordering.

### Formats

- JSON returns a structured payload with export count, total search hits, repository provenance, OAI identifier, and normalized metadata.
- CSV flattens repeated metadata fields into pipe-separated values and retains repository/OAI identity columns.
- XML exports the canonical normalized fields.
- OAI Dublin Core XML emits Dublin Core namespace elements inside an OAI-DC metadata wrapper. This is a metadata export document, not a complete OAI-PMH response envelope.

Exports are paginated and limited to the OpenSearch result window. For large collections, iterate through pages rather than requesting an unbounded export.

The public frontend provides CSV, JSON, and Dublin Core XML download links using a same-origin proxy; the proxy forwards only a fixed allowlist of export parameters.

## Administrative analytics

`GET /api/v1/analytics/summary`

Requires the administrative bearer token. The summary includes:
- Total, enabled, and disabled repositories.
- Total, active, deleted, and normalized source records.
- Records harvested in the last 30 days.
- Harvest job counts grouped by status.
- Enabled recurring schedules.
- Pending and failed search-index outbox events.
- The ten enabled repositories with the largest source-record counts.

Metrics are calculated from PostgreSQL and are intended for operational monitoring, not public benchmarking or bibliometric evaluation.
