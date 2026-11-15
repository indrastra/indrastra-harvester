# Development Roadmap

## Stage 0 — Foundation
- Repository scaffold and coding conventions.
- CI workflow, linting, formatting, and test setup.
- Docker Compose development environment.
- Configuration and structured logging.

## Stage 1 — Repository registry
- Database schema and migrations.
- Repository CRUD API.
- Endpoint validation and SSRF protections.
- Identify and ListMetadataFormats.

## Stage 2 — OAI-PMH engine
- ListSets, ListIdentifiers, ListRecords, GetRecord.
- Resumption-token pagination.
- Date-window handling and checkpoints.
- Retries, timeouts, rate limits, and job lifecycle.

## Stage 3 — Metadata pipeline
- OAI Dublin Core and initial DataCite crosswalks.
- Generic XML field preservation for unknown metadata prefixes.
- Versioned normalized schema and raw field map.
- Original XML preservation and immutable source record versions.
- Validation, provenance, and deletion propagation.
- Additional crosswalks: Qualified Dublin Core, MODS, MARCXML, and JATS.

## Stage 4 — Search and discovery
- Initial OpenSearch mapping and asynchronous indexing outbox.
- Public search API with text, repository, resource-type, and year filters.
- Relevance and publication-year sorting.
- Initial Next.js public search and record detail pages.
- Facets, advanced discovery, and index rebuild tooling.

## Stage 5 — Administration and operations
- Shared-token operator console for repository, harvest, schedule, and indexing operations.
- Persistent hourly/daily/weekly schedules with Celery Beat and incremental date windows.
- Administrative collection metrics and index-outbox monitoring.
- JWT user accounts, Argon2 password hashing, admin/harvester/viewer roles, account lockout, and audit events.

## Stage 6 — Exports and analytics
- Public JSON, CSV, canonical XML, and OAI Dublin Core XML metadata exports.
- Administrative operational summary for repository, record, job, schedule, and indexing status.
- Advanced facets, trend analytics, scheduled reports, and bibliometric analytics remain future work.

## Stage 7 — Release hardening
- Non-root backend/frontend containers, readiness probes, request IDs, and baseline security headers.
- PostgreSQL backup/restore scripts and deployment/upgrade documentation.
- CI validation for migrations, backend tests, frontend build, Compose configuration, and container images.
- Remaining: external security review, performance/load testing, accessibility review, production OpenSearch hardening, and operational monitoring.
- MFA, SSO, password reset, token revocation, and fine-grained permission policies remain future work.

## Release gates

Do not label the project production-ready until security, backup/restore, migration, observability, and end-to-end acceptance tests pass.
