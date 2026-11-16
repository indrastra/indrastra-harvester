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
10. Expose public search and administrative APIs for repositories, harvest jobs, and indexing.
11. Provide a responsive Next.js public discovery portal and record detail pages.
12. Provide a token-protected operator console for repository and harvest management.
13. Schedule hourly, daily, and weekly incremental harvests using Celery Beat.
14. Export normalized metadata as JSON, CSV, XML, and Dublin Core XML.
15. Provide administrative collection and indexing analytics.
16. Support JWT authentication, Argon2 password hashing, audit events, and admin/harvester/viewer roles.
17. Provide readiness checks, non-root containers, database backup/restore scripts, and security headers.

## Planned platform capabilities

- Additional metadata crosswalks (Qualified Dublin Core, MODS, MARCXML, JATS).
- Advanced discovery features including facets, saved searches, and discovery analytics.
- MFA, SSO, password reset, token revocation, and fine-grained resource permissions.
- Advanced schedule calendars and timezone-specific scheduling.
- Advanced analytics dashboards, scheduled reports, and public REST API expansion.

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

Protected endpoints require an HTTP bearer token. Administrators can use the bootstrap `ADMIN_API_TOKEN` (minimum 32 characters) or sign in with a user account to obtain a short-lived JWT. Configure `JWT_SECRET_KEY` with at least 32 random characters. See [Authentication and RBAC](docs/AUTHENTICATION.md).

### Authentication and user administration

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/auth/token` | Exchange email/password for a JWT |
| GET | `/api/v1/auth/me` | Inspect current account |
| POST | `/api/v1/auth/users` | Create a user (admin) |
| GET | `/api/v1/auth/users` | List users (admin) |
| PATCH | `/api/v1/auth/users/{id}/roles` | Change roles (admin) |
| PATCH | `/api/v1/auth/users/{id}/active` | Activate/deactivate account (admin) |

See [Authentication and RBAC](docs/AUTHENTICATION.md) for role permissions and security limits.

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
| GET | `/api/v1/search` | Public search with filters and pagination |
| GET | `/api/v1/records/{id}` | Public normalized record detail and provenance |
| POST | `/api/v1/index/dispatch` | Dispatch pending indexing events (admin only) |

See [Search indexing](docs/SEARCH_INDEXING.md) for query parameters, mapping, and outbox behaviour.

### Audit events

Administrators can inspect recent authentication and user-administration events through `GET /api/v1/audit-events`.

### Exports and analytics

Public exports are available at `/api/v1/exports` in JSON, CSV, XML, and OAI Dublin Core XML formats. Administrative analytics are available at `/api/v1/analytics/summary`. See [Exports and analytics](docs/EXPORTS_ANALYTICS.md).

### Scheduled harvesting

See [Scheduled harvesting](docs/SCHEDULING.md) for recurring schedule configuration and UTC semantics. Schedule creation and management require an admin or harvester role.

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

The repository contains the OAI-PMH client, repository registry, persistent harvesting engine, immutable source-record history, OAI Dublin Core/DataCite normalization, OpenSearch-backed search API with durable indexing outbox, and a Next.js public discovery portal with record detail pages. MFA, SSO, password reset, fine-grained resource permissions, index rebuild tooling, advanced schedule calendars, richer analytics, and production security/operational validation remain under development.

See [Technical specification](docs/TECHNICAL_SPECIFICATION.md), [Architecture](docs/ARCHITECTURE.md), [Roadmap](docs/ROADMAP.md), [Search indexing](docs/SEARCH_INDEXING.md), [Frontend](docs/FRONTEND.md), [Administration](docs/ADMINISTRATION.md), [Authentication and RBAC](docs/AUTHENTICATION.md), [Deployment](docs/DEPLOYMENT.md), [Security policy](SECURITY.md), and [Contributing guide](CONTRIBUTING.md).

## License

Licensed under the GNU Affero General Public License v3.0. See [LICENSE](LICENSE).
