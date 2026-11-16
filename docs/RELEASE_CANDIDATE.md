# IndraStra Harvester v0.1.0-rc.1

**Status:** Release candidate for controlled deployment validation  
**Release date:** 2026-11-16  
**Source commit:** `015dd0a4ccfa06a168c7a4936bdfe29ea63a41bd`  
**Validation PR:** [#15](https://github.com/indrastra/indrastra-harvester/pull/15)

## Release summary

This candidate consolidates the Milestone 1–11 platform baseline and supplementary deployment safeguards. It is intended for staging and controlled evaluation, not an assertion of production readiness.

### Included capabilities

- OAI-PMH 2.0 harvesting across all six verbs, persistent harvest jobs, checkpoints, and recurring schedules.
- Repository registry, metadata normalization, immutable source versions, provenance retention, and tombstones.
- Transactional indexing outbox and OpenSearch-backed discovery.
- Public search and record detail APIs, metadata exports, and analytics.
- Administrative console, JWT authentication, Argon2 password hashing, role-based access, and audit-event listing.
- Non-root application containers, health/readiness endpoints, request IDs, security headers, and safer default port bindings.
- PostgreSQL backup/restore scripts, deployment guidance, CodeQL, Dependabot, and integration acceptance coverage.

## Validation evidence

The following checks passed on PR #15 head `19a20a15f8ae6837243b994e701d818924e6b967` before squash merge:

| Check | Result |
|---|---|
| Backend Ruff lint | Passed |
| Backend pytest suite | Passed |
| Alembic migration verification | Passed |
| PostgreSQL + Redis + OpenSearch integration acceptance | Passed |
| End-to-end harvest → normalize → index → public search/record | Passed |
| Frontend production build | Passed |
| Docker Compose validation | Passed |
| Backend container build | Passed |
| Frontend container build | Passed |
| CodeQL JavaScript/TypeScript | Passed |
| CodeQL Python | Passed |

CI run: [#69](https://github.com/indrastra/indrastra-harvester/actions/runs/43800080738)  
CodeQL run: [#16](https://github.com/indrastra/indrastra-harvester/actions/runs/43800080725)

The integrated acceptance test uses a deterministic OAI-PMH fixture and real PostgreSQL, Redis, and OpenSearch services. It does not validate arbitrary external repositories, production network policy, production-scale throughput, or disaster recovery in a live environment.

## Deployment prerequisites

1. Use a dedicated staging host with Docker Engine and Docker Compose v2.
2. Configure a TLS reverse proxy; do not expose application, database, Redis, or OpenSearch ports directly to the public internet.
3. Generate independent secrets for PostgreSQL, JWT signing, application secret, and bootstrap administration.
4. Enable OpenSearch authentication, TLS, and least-privilege roles. The security-plugin-disabled OpenSearch configuration is for development/CI only.
5. Enforce outbound network restrictions or an egress proxy that blocks loopback, private, link-local, multicast, reserved, unspecified, and cloud metadata destinations. Application DNS validation alone does not fully prevent DNS rebinding.
6. Encrypt PostgreSQL backups before off-host storage, restrict access, and test restores.
7. Configure monitoring and alerting for PostgreSQL, Redis, OpenSearch, API readiness, Celery workers, scheduler, and indexing outbox.

See [Deployment and operations](DEPLOYMENT.md) and [Administration console](ADMINISTRATION.md).

## Staging smoke test

- [ ] Apply migrations from a clean database.
- [ ] Verify `/health` and `/ready`.
- [ ] Bootstrap an administrator and verify role restrictions.
- [ ] Register a controlled OAI-PMH fixture repository and validate its endpoint.
- [ ] Run a harvest and verify job state, logs, checkpoints, source records, and normalized metadata.
- [ ] Verify indexing outbox completion and OpenSearch discovery.
- [ ] Open a public record detail page and verify provenance/source identity.
- [ ] Test schedule creation, disable/enable, and run-now.
- [ ] Test JSON, CSV, and XML export paths.
- [ ] Verify audit-event visibility is restricted to administrators.
- [ ] Run PostgreSQL backup and restore in an isolated staging environment.
- [ ] Exercise worker, Redis, OpenSearch, and database interruption/recovery.
- [ ] Verify outbound egress controls using prohibited destination test cases.

## Known limitations and explicit non-claims

- This release candidate is **not production-certified**.
- MFA, SSO, password reset, refresh-token rotation, token revocation, and fine-grained permission management remain future hardening items.
- Application-level URL/DNS validation must be backed by network-level egress restrictions.
- Production OpenSearch must be secured independently; CI's disabled security plugin is not a production configuration.
- Load, penetration, accessibility, multi-tenant isolation, and full disaster-recovery testing remain outside the CI acceptance run.
- Backup scripts do not encrypt backup files themselves.
- Search indexes are rebuildable projections; PostgreSQL remains authoritative.

## Rollback guidance

Before upgrading any environment, take and verify a PostgreSQL backup. If a migration has changed the schema, do not simply roll back application containers against the migrated database. Follow a tested database restore procedure and deploy the previously approved application revision. Treat OpenSearch as rebuildable from PostgreSQL after recovery.

## Candidate acceptance

Promote this candidate beyond staging only after the deployment checklist in `DEPLOYMENT.md` is completed and the operator has documented the remaining security, load, and recovery test results.
