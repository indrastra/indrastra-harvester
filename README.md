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
| XML | lxml |
| Deployment | Docker Compose |
| CI | GitHub Actions |

## Repository layout

```text
backend/       API, harvesting engine, metadata and tests
docs/          Technical specification, architecture and roadmap
frontend/      Web application (planned)
deploy/        Deployment guidance
.github/       CI workflows
```

## Development status

This repository contains an early project scaffold and an OAI-PMH client implementation. The complete harvesting workflow, persistent storage, authentication, discovery interface, and production security controls are not yet implemented.

See [Technical specification](docs/TECHNICAL_SPECIFICATION.md), [Architecture](docs/ARCHITECTURE.md), [Roadmap](docs/ROADMAP.md), [Security policy](SECURITY.md), and [Contributing guide](CONTRIBUTING.md).

## Quick start

The Docker Compose environment is intended for local development. Review `.env.example` and the deployment documentation before running it. Do not expose the development configuration to the public internet.

## License

Licensed under the GNU Affero General Public License v3.0. See [LICENSE](LICENSE).
