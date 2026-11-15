# Architecture and Engineering Decisions

## Decision 1 — Modular monolith first

Keep domain logic in one backend codebase with clear module boundaries. Run asynchronous workers as separate processes. Avoid microservices until measured scale or independent deployment requirements justify them.

## Decision 2 — Source record versus scholarly work

A repository's OAI identifier identifies a source record within that repository. It does not necessarily identify a globally unique scholarly work. Preserve source records independently. Add a future work-clustering layer without destructive merges.

## Decision 3 — PostgreSQL is authoritative

All source and normalized records are persisted in PostgreSQL. OpenSearch is a rebuildable projection. A search-index outage must not cause harvested metadata loss.

## Decision 4 — Preserve original XML

Store the original metadata payload, metadata prefix, source identifier, harvest timestamp, and provenance. This enables reprocessing when normalization rules change.

## Decision 5 — Asynchronous harvesting

Long-running network operations must not block API requests. API endpoints enqueue work; Celery workers execute harvesting and indexing tasks.

## Decision 6 — Safe outbound networking

Repository URLs are untrusted input. Enforce HTTP/HTTPS only, DNS and IP validation, redirect revalidation, private/link-local/loopback address blocking, bounded response sizes, and timeouts. Consider DNS rebinding protections.

## Decision 7 — Observability

Every harvest has a correlation ID, repository ID, timestamps, counters, and structured error events. Never log secrets or entire untrusted payloads by default.

## Logical components

Next.js UI
    |
    v
FastAPI REST API ---- PostgreSQL
    |                     |
    v                     v
Redis broker          Source records
    |
    v
Celery workers
    |
    +---- OAI-PMH repositories
    |
    +---- Metadata normalization
    |
    +---- OpenSearch indexing

## Backend module boundaries

- api: HTTP routes and request/response schemas.
- core: settings, logging, security, shared exceptions.
- db: engine, sessions, migrations, repositories.
- repositories: repository registry and endpoint validation.
- harvest: OAI-PMH client, orchestration, checkpoints, retries.
- metadata: parsers, crosswalks, normalization, validation.
- search: OpenSearch client, mappings, indexing, query service.
