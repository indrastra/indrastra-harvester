# IndraStra Harvester

**IndraStra Harvester** is an open-source scholarly metadata harvesting and discovery platform developed by IndraStra Global Publishing Solutions Inc.

The project aims to collect, normalize, index, and expose scholarly metadata from OAI-PMH-compliant repositories and other supported scholarly sources.

- **License:** GNU Affero General Public License v3.0 (AGPL-3.0)
- **Deployment:** Self-hosted; Docker-first
- **Initial protocol:** OAI-PMH 2.0
- **Status:** Early development — not production-ready

## Project goals

1. Register and validate scholarly repositories.
2. Harvest metadata using all six OAI-PMH verbs.
3. Normalize and preserve source metadata.
4. Schedule incremental harvesting and resume interrupted jobs.
5. Index records for public discovery.
6. Provide administration, monitoring, export, and REST API capabilities.

## Planned technology stack

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
frontend/      Web application (planned)
deploy/        Deployment guidance
.github/       CI workflows
```

## Repository registry API

The repository-management API is available under `/api/v1/repositories`.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/repositories` | Register a repository |
| GET | `/api/v1/repositories` | List repositories |
| GET | `/api/v1/repositories/{id}` | View repository |
| PATCH | `/api/v1/repositories/{id}` | Update repository details |
| POST | `/api/v1/repositories/{id}/validate` | Recheck OAI-PMH endpoint and capabilities |
| DELETE | `/api/v1/repositories/{id}` | Disable repository (soft delete) |

**All repository registry operations require an HTTP bearer token** configured as `ADMIN_API_TOKEN` (minimum 32 characters). If the token is not configured, administrative operations fail closed with HTTP 503. A full user and role management system is planned for a later milestone.

## Database setup

Copy `.env.example` to `.env`, replace all development secrets, and start the stack:

```bash
docker compose up --build -d
```

Docker Compose runs the Alembic migration service before starting the API and worker. Check the API:

```bash
curl http://localhost:8000/health
```

The local API documentation is available at `http://localhost:8000/docs`.

The Docker Compose environment is intended for local development. Review `SECURITY.md` before exposing any service to a network. Application-level DNS validation must be complemented by outbound firewall or egress-proxy restrictions.

## Development status

The repository contains the initial OAI-PMH client and repository registry milestone. Persistent harvesting jobs, normalized record storage, the discovery interface, and production security controls remain under development.

See [Technical specification](docs/TECHNICAL_SPECIFICATION.md), [Architecture](docs/ARCHITECTURE.md), [Roadmap](docs/ROADMAP.md), [Security policy](SECURITY.md), and [Contributing guide](CONTRIBUTING.md).

## License

Licensed under the GNU Affero General Public License v3.0. See [LICENSE](LICENSE).
