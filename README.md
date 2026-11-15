# IndraStra Harvester

**IndraStra Harvester** is an open-source scholarly metadata harvesting and discovery platform developed by IndraStra Global Publishing Solutions Inc.

The project collects, preserves, normalizes, indexes, and exposes scholarly metadata from OAI-PMH-compliant repositories and other supported scholarly sources.

- **License:** GNU Affero General Public License v3.0 (AGPL-3.0)
- **Deployment:** Self-hosted; Docker-first
- **Initial protocol:** OAI-PMH 2.0
- **Status:** Active development — not production-ready

## Project capabilities

1. Register and validate scholarly repositories.
2. Harvest metadata using OAI-PMH 2.0.
3. Run persistent asynchronous harvest jobs using Celery.
4. Resume interrupted harvests using OAI-PMH resumption-token checkpoints.
5. Store original source XML and preserve repository provenance.
6. Track updates and deleted-record tombstones without physically deleting source records.
7. Normalize OAI Dublin Core and DataCite metadata into a versioned canonical schema.
8. Preserve unknown XML fields and immutable source-record versions.
9. Index normalized records asynchronously in OpenSearch using a durable outbox.
10. Expose public search and administrative APIs for repositories, harvest jobs, and indexing.\n11. Provide a responsive Next.js public discovery portal and record detail pages.

## Planned platform capabilities

- Additional metadata crosswalks (Qualified Dublin Core, MODS, MARCXML, JATS).
- Advanced discovery features including facets, saved searches, and discovery analytics.
- Repository and user administration with role-based access.
- Scheduled incremental harvesting.
- Export to JSON, CSV, XML, and Dublin Core.
- Analytics, monitoring, and public REST API.

## Technology stack

| Component | Technology |
|---|---|
| API | Python, FastAPI, Pydantic |
| Frontend | Next.js, React, TypeScript |
| Database | PostgreSQL |
| Search | OpenSearch |
| Background jobs | Celery |
| Queue/cache | Redis |
| XML | defusedxml / lxml |
| Deployment | Docker Compose |
| CI | GitHub Actions |

## Repository layout

```text
backend/       API, harvesting engine, metadata and tests
migrations/    Alembic database migrations
docs/          Technical specification, architecture and roadmap
frontend/      Next.js public discovery portal
deploy/        Deployment guidance
.github/       CI workflows
```

## API

All administrative endpoints require an HTTP bearer token configured as `ADMIN_API_TOKEN` (minimum 32 characters). If the token is not configured, administrative operations fail closed with HTTP 503. A complete user and role management system is planned for a later milestone.

### Repository registry

Base path: `/api/v1/repositories`

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/repositories` | Register a repository |
| GET | `/api/v1/repositories` | List repositories |
| GET | `/api/v1/repositories/{id}` | View repository |
| PATCH | `/api/v1/repositories/{id}` | Update repository details |
| POST | `/api/v1/repositories/{id}/validate` | Recheck OAI-PMH endpoint and capabilities |
| DELETE | `/api/v1/repositories/{id}` | Disable repository (soft delete) |

### Search and indexing

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/search` | Public search with filters and pagination |\n| GET | `/api/v1/records/{id}` | Public normalized record detail and provenance |
| POST | `/api/v1/index/dispatch` | Dispatch pending indexing events (admin only) |

See [Search indexing](docs/SEARCH_INDEXING.md) for query parameters, mapping, and outbox behaviour.

### Harvest jobs

Base path: `/api/v1/harvests`

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/harvests` | Queue a ListRecords harvest |
| GET | `/api/v1/harvests` | List persistent harvest jobs |
| GET | `/api/v1/harvests/{id}` | View job status, counters, and logs |
| POST | `/api/v1/harvests/{id}/resume` | Resume a failed or paused job |

Example harvest request:

```json
{
  "repository_id": 1,
  "metadata_prefix": "oai_dc",
  "set_spec": null,
  "from_date": "2026-01-01",
  "until_date": "2026-11-15"
}
```

Source-record identity is the pair `repository_id + oai_identifier`. Each page's record writes and next resumption-token checkpoint are committed together. When a resumption token is present, the next OAI-PMH request contains only the verb and token. Deleted headers are stored as tombstones; historical source data is not physically deleted.

## Local development

Copy `.env.example` to `.env`, replace all development secrets, and start the stack:

```bash
docker compose up --build -d
```

Docker Compose runs Alembic migrations before starting the API and worker. Check the API:

```bash
curl http://localhost:8000/health
```

Interactive API documentation is available at `http://localhost:8000/docs`.

The Compose environment is intended for local development. Review [SECURITY.md](SECURITY.md) before exposing any service to a network. Application-level DNS validation cannot alone eliminate DNS rebinding; production deployments must enforce outbound restrictions using a firewall or egress proxy.

## Development status

The repository contains the OAI-PMH client, repository registry, persistent harvesting engine, immutable source-record history, OAI Dublin Core/DataCite normalization, OpenSearch-backed search API with durable indexing outbox, and a Next.js public discovery portal with record detail pages. Administrative UI, index rebuild tooling, user administration, scheduled harvest policies, and production security/operational validation remain under development.

See [Technical specification](docs/TECHNICAL_SPECIFICATION.md), [Architecture](docs/ARCHITECTURE.md), [Roadmap](docs/ROADMAP.md), [Security policy](SECURITY.md), and [Contributing guide](CONTRIBUTING.md).

## License

Licensed under the GNU Affero General Public License v3.0. See [LICENSE](LICENSE).
