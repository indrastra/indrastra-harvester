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

## Stage 5 — Administration
- Authentication and RBAC.
- Repository and job dashboards.
- Logs, metrics, exports, and audit events.

## Stage 6 — Release hardening
- Security review and dependency audit.
- Backup/restore and upgrade documentation.
- Performance testing with representative repositories.
- Accessibility review.
- Release packaging and documentation.

## Release gates

Do not label the project production-ready until security, backup/restore, migration, observability, and end-to-end acceptance tests pass.
