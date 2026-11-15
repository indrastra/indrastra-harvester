# IndraStra Harvester — Technical Specification

**Version:** 1.0  
**Date:** 15 November 2026  
**Project owner:** IndraStra Global Publishing Solutions Inc.  
**License:** AGPL-3.0  
**Deployment model:** Independent, self-hosted deployment

## 1. Purpose

IndraStra Harvester is a modular scholarly metadata harvesting, aggregation, and discovery platform. It is intended for universities, institutional repositories, scholarly publishers, digital libraries, preprint servers, and research networks.

The system will independently implement its own software architecture and codebase. It may interoperate with existing repository platforms through documented protocols and APIs.

## 2. Product objectives

- Register and monitor multiple scholarly repositories.
- Harvest metadata using OAI-PMH 2.0.
- Support scheduled, manual, and incremental harvesting.
- Preserve original source metadata and normalized records.
- Validate, map, and enrich metadata.
- Track updates, deletions, failures, and harvesting checkpoints.
- Index records for public search and discovery.
- Expose documented APIs and metadata exports.
- Support independent Docker-based deployment.

## 3. Users and roles

| Role | Permissions |
|---|---|
| System administrator | System configuration, users, all repositories |
| Repository manager | Register and manage assigned repositories |
| Harvest operator | Run jobs, inspect logs, retry failures |
| Metadata editor | Review and correct permitted metadata |
| Analyst | View dashboards and reports |
| Public user | Search and view public records |

Authorization must be enforced server-side. Public search must not expose private administrative data or secrets.

## 4. Functional requirements

### 4.1 Repository registry

Each repository record should support name, description, OAI-PMH endpoint, organization, country, contact information, enabled state, metadata formats, sets, last successful harvest, health-check result, request timeout, and rate limit.

Validate endpoints before enabling harvesting. URL validation and outbound request controls must protect against SSRF, private-network access, redirects to prohibited destinations, and unsafe protocols.

### 4.2 OAI-PMH client

Implement all six OAI-PMH 2.0 verbs: Identify, ListMetadataFormats, ListSets, ListIdentifiers, ListRecords, and GetRecord.

Requirements:
- Parse protocol-level errors and HTTP errors distinctly.
- Support resumptionToken pagination.
- Support from, until, set, and metadataPrefix where applicable.
- Respect date granularity returned by Identify.
- Handle UTC timestamps and repository-declared granularity.
- Persist checkpoints and job state.
- Retry transient network and server failures with bounded exponential backoff.
- Avoid retry loops for permanent protocol errors.
- Apply per-repository concurrency and rate limits.
- Record request timing, response status, and error details without logging secrets or sensitive headers.

### 4.3 Metadata ingestion and normalization

Initial formats: OAI Dublin Core (oai_dc), Qualified Dublin Core, MODS, MARCXML, DataCite XML, and JATS XML where exposed through a configured adapter.

A normalized record should include, where available: source repository ID, source OAI identifier, title and alternative titles, creators and contributors, abstract or description, subjects, publication date, publisher, resource type, language, DOI and other identifiers, rights and licence statements, landing-page URL, full-text URL, relations and references, original metadata format, original XML payload, and first-seen/last-seen timestamps.

Store the original payload alongside normalized fields. Record provenance for every source field and transformation.

### 4.4 Identity and deduplication

The authoritative source identity is the combination of repository identity and source identifier. DOI, ISBN, other identifiers, title similarity, and creator/date combinations may be used as matching signals.

Do not merge source records destructively. A single scholarly work may have multiple source manifestations. Preserve source-level records and represent potential work-level relationships separately.

### 4.5 Deletions and updates

Process OAI-PMH deleted headers, preserve tombstones and deletion timestamps, avoid silent erasure of source history, update records idempotently, track record versions or change events, and make re-harvesting safe to repeat.

### 4.6 Scheduling and job management

Support manual and scheduled harvests, incremental harvest using checkpoints and date ranges, full resynchronization, retry of failed jobs, safe pause/cancel, per-repository job concurrency, job statuses (queued, running, succeeded, partially_succeeded, failed, cancelled), and job/record metrics.

### 4.7 Search and discovery

Search fields include title, creator, DOI/identifiers, abstract/description, subject, institution/repository, publication year, resource type, and language. Support full-text and fielded search, facets, filters, relevance/date sorting, pagination, record detail pages, source attribution, original record links, and reindex operations.

PostgreSQL is authoritative. OpenSearch is a derived index and must be rebuildable.

### 4.8 Administration and analytics

Provide role-based access control, repository health and protocol capability display, job history and logs, harvest volume and error statistics, metadata validation reports, export/reindex controls, and administrative audit events.

### 4.9 APIs and exports

Provide a versioned REST API, initially /api/v1, for repository management, jobs, records, and search. Initial exports: JSON, CSV, XML, and Dublin Core XML. Document authentication, pagination, rate limits, and error formats.

## 5. Non-functional requirements

### Reliability
- Idempotent ingestion and durable job state.
- Recoverable worker failures.
- Database backup and restore documentation.

### Security
- Secure password hashing and session/token handling.
- Least-privilege service accounts.
- Secrets supplied through environment or secret management.
- SSRF protection for repository URLs.
- XXE protections; disable external entity resolution.
- Request size, timeout, and decompression limits.
- Dependency scanning and security updates.
- Audit logging for privileged actions.

### Performance and scale

Prioritize correctness and observability over premature optimization. Workers and search indexing must be independently scalable. Define throughput benchmarks after a representative repository test corpus exists.

### Accessibility and usability

The public portal and administration interface should target WCAG 2.2 AA where practicable, with keyboard navigation and responsive layouts.

### Internationalization

Store text as Unicode. Support multilingual metadata and Unicode search. Design the interface for future localization.

## 6. Proposed architecture

Use a modular monolith for the API and domain logic, with independent asynchronous workers:
- Next.js frontend: administration and public discovery.
- FastAPI backend: versioned REST API and domain services.
- PostgreSQL: authoritative relational and JSON metadata store.
- Celery workers: harvesting, normalization, and indexing tasks.
- Redis: broker and cache.
- OpenSearch: discovery index.
- Docker Compose: local and single-host deployment.

## 7. Initial database entities

users, roles, repositories, repository_metadata_formats, repository_sets, harvest_jobs, harvest_job_logs, harvest_checkpoints, source_records, record_identifiers, normalized_records, record_versions, audit_events.

Use migrations for all schema changes. Keep source identifiers unique within a repository, not globally.

## 8. OAI-PMH harvesting workflow

1. Validate the repository endpoint.
2. Call Identify and record protocol metadata.
3. Discover metadata formats and sets.
4. Select configured metadata prefix and optional set/date window.
5. Request ListRecords or ListIdentifiers.
6. Parse headers and metadata safely.
7. Follow resumption tokens until completion.
8. Normalize and validate each record.
9. Upsert the source record idempotently.
10. Update the search index asynchronously.
11. Persist job metrics, errors, and checkpoints.
12. Mark job completion or partial failure.

## 9. Acceptance criteria for first functional release

- An administrator can register and validate an OAI-PMH endpoint.
- The application can execute Identify and ListMetadataFormats.
- A harvest can retrieve ListRecords pages, including resumption-token pages.
- Records are persisted with source identifiers and original XML.
- Re-running the same harvest does not create duplicate source records.
- Deleted headers are represented as tombstones.
- Job status and errors are visible to an administrator.
- A public user can search indexed records.
- A deployment can be started using documented Docker Compose instructions.
- Automated tests cover protocol parsing, pagination, retries, normalization, and idempotency.

## 10. Out of scope for the first release

Full-text crawling of arbitrary publisher websites, paywalled content acquisition, citation graph construction, AI-generated abstracts/metadata, automatic merging of scholarly works across repositories, and replacing repository software such as DSpace or OJS are out of scope.

## 11. Compatibility and interoperability

OAI-PMH 2.0 is the first required ingestion protocol. Additional adapters may be introduced for repository APIs and other metadata exchange mechanisms after the core harvester is stable.

## 12. Licensing

The project is intended to be distributed under AGPL-3.0. Review dependencies for licence compatibility and include attribution and notices where required. Complete legal review before the first production release.
