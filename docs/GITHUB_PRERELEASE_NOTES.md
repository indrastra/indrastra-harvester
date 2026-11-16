# IndraStra Harvester v0.1.0-rc.1

**Release type:** Published GitHub pre-release  
**Status:** Published on 2026-11-16; live staging deployment and operational acceptance remain pending  
**Application baseline commit:** `bdf0547404a5c271d5e0b90d8b6a8c33c280d48e`  
**Published release commit:** `1e15da42b3fd19913c5ae23d43adb08cb5dc2c99`  
**Git tag:** `v0.1.0-rc.1`  
**GitHub release:** https://github.com/indrastra/indrastra-harvester/releases/tag/v0.1.0-rc.1  
**License:** GNU Affero General Public License v3.0 (AGPL-3.0)

## Release summary

IndraStra Harvester is a self-hosted scholarly metadata harvesting and discovery platform. This release candidate consolidates the Milestone 1–11 application baseline and the Milestone 12 staging-acceptance runbook.

This is an early evaluation release. It is not production-certified, and publication does not imply that a live deployment or staging operational acceptance has taken place.

## Highlights

- OAI-PMH 2.0 client supporting all six protocol verbs.
- Repository registry and endpoint validation.
- Persistent asynchronous harvesting, resumption-token checkpoints, incremental harvesting, and recurring schedules.
- Raw XML retention, provenance, normalized metadata, record version history, and deleted-record tombstones.
- Durable indexing outbox and OpenSearch-backed discovery.
- Public search and record detail pages.
- Administrative console, JWT authentication, Argon2 password hashing, admin/harvester/viewer roles, and audit events.
- JSON, CSV, canonical XML, and Dublin Core XML exports, plus analytics.
- Docker-first deployment, non-root containers, health/readiness checks, PostgreSQL backup/restore scripts, CI, CodeQL, and Dependabot configuration.

## Validation evidence

### Application and integration baseline

The Milestone 11 integration run passed backend lint and tests, migration verification, PostgreSQL/Redis/OpenSearch integration acceptance, end-to-end harvest-to-discovery coverage, frontend production build, Docker Compose validation, backend/frontend container builds, and CodeQL analysis.

- CI run #69: https://github.com/indrastra/indrastra-harvester/actions/runs/43800080738
- CodeQL run #16: https://github.com/indrastra/indrastra-harvester/actions/runs/43800080725
- Baseline hardening PR #15: https://github.com/indrastra/indrastra-harvester/pull/15

### Staging acceptance documentation

PR #30 added the staging deployment and operational acceptance runbook. Its CI and CodeQL workflows passed:

- CI run #86: https://github.com/indrastra/indrastra-harvester/actions/runs/43801346404
- CodeQL run #33: https://github.com/indrastra/indrastra-harvester/actions/runs/43801346321
- PR #30: https://github.com/indrastra/indrastra-harvester/pull/30

PR #31 added the GitHub pre-release notes and passed its CI and CodeQL checks:

- CI run #88: https://github.com/indrastra/indrastra-harvester/actions/runs/43802240591
- CodeQL run #35: https://github.com/indrastra/indrastra-harvester/actions/runs/43802240555
- PR #31: https://github.com/indrastra/indrastra-harvester/pull/31

These PR checks are evidence for the tested pull-request revisions. They are not evidence of a live deployment, external-repository interoperability at scale, production network enforcement, production performance, or disaster recovery in a live environment.

## Installation and evaluation

1. Download the source archive for the release tag from GitHub.
2. Review the repository README and `docs/DEPLOYMENT.md`.
3. Configure the environment from `.env.example`; replace every development secret with independent high-entropy values.
4. Follow the deployment documentation and inspect the rendered Compose configuration before starting services.
5. Use only an isolated evaluation or staging environment until the security and operational acceptance gates have been completed.

The default Compose configuration is for development/evaluation. In particular, its OpenSearch security-plugin-disabled configuration must not be exposed publicly. A secure deployment requires OpenSearch TLS/authentication, private database and Redis networking, a TLS reverse proxy, and network-level outbound egress restrictions.

## Known limitations

- Not production-certified; staging deployment and operational acceptance remain pending.
- MFA, SSO, password reset, refresh-token rotation, token revocation, and fine-grained resource permissions remain future hardening items.
- Application DNS validation alone does not fully prevent DNS rebinding; network-level egress controls are required.
- Load, penetration, accessibility, multi-tenant isolation, and full disaster-recovery tests remain outstanding.
- Backup scripts do not encrypt backup files themselves; encrypt backups before off-host storage.
- PostgreSQL is authoritative; OpenSearch indexes are rebuildable projections.

## Release classification

**Published GitHub Pre-release — evaluation only; not production-ready or production-certified.**

The release is available for controlled evaluation and feedback. It is not marked as a stable production release.

## Publication record

- [x] Release notes merged into the repository.
- [x] Git tag `v0.1.0-rc.1` created at `1e15da42b3fd19913c5ae23d43adb08cb5dc2c99`.
- [x] GitHub release published.
- [x] Release marked as a pre-release.
- [x] Release metadata and tag target verified against the `main` commit.
- [ ] Deploy to an isolated staging environment.
- [ ] Complete the Milestone 12 staging acceptance runbook in `docs/STAGING_ACCEPTANCE.md`.
- [ ] Record operator evidence, unresolved findings, and the go/no-go decision.
- [ ] Complete production security, performance, backup/restore, and operational reviews before any stable release.
