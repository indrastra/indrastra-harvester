# Milestone 12 — Staging deployment and operational acceptance

**Purpose:** Execute and record a controlled staging deployment of IndraStra Harvester v0.1.0-rc.1.

**Status:** Runbook prepared; live deployment and operator evidence are pending.
**Candidate application baseline:** `015dd0a4ccfa06a168c7a4936bdfe29ea63a41bd`
**Release packaging merge:** `5f8d03cc6f73afbaf849d80a3a2fa6144b5fdee8`

This document is an execution record template, not evidence that a staging environment has already been deployed. Do not mark a check complete without attaching the corresponding evidence.

## 1. Entry criteria

Before provisioning or deploying, the release operator must record:

| Item | Required value |
|---|---|
| Staging provider/account | Record provider and account/project identifier (never credentials) |
| Host identifier | Hostname or instance identifier |
| Operating system | Distribution and supported version |
| CPU / RAM / disk | Provisioned capacity and available disk |
| Public DNS name | Staging FQDN |
| TLS termination | Reverse proxy and certificate issuer |
| Egress enforcement | Firewall or egress-proxy policy reference |
| OpenSearch security | Authentication/TLS configuration reference |
| Secret manager | Secret-store name/path (never secret values) |
| Backup destination | Encrypted off-host destination |
| Operator | Named accountable operator |
| Change window | Approved UTC start/end |

Do not place passwords, private keys, access tokens, connection strings, or secret values in this file, GitHub issues, CI logs, or commit messages.

## 2. Infrastructure safety gates

All of the following are mandatory before the stack is exposed beyond loopback:

- [ ] Dedicated staging environment; no production data copied without an approved data-handling plan.
- [ ] Supported Docker Engine and Docker Compose v2 installed and patched.
- [ ] Host firewall denies unsolicited inbound traffic; only required TLS ingress is allowed.
- [ ] Public traffic terminates at a TLS reverse proxy.
- [ ] Administrative UI and administrative API routes are access-restricted at the proxy/network layer.
- [ ] PostgreSQL and Redis have no public listener.
- [ ] OpenSearch security is enabled with TLS, authentication, and least-privilege credentials.
- [ ] OpenSearch certificates and trust configuration are provisioned and verified.
- [ ] Outbound egress policy blocks loopback, private, link-local, multicast, reserved, unspecified, internal control-plane, and cloud metadata destinations.
- [ ] DNS rebinding is addressed at the network/egress layer; application DNS checks alone are insufficient.
- [ ] Independent high-entropy secrets are stored in a secret manager and injected at runtime.
- [ ] Host time synchronization, log rotation, disk alerts, and resource monitoring are enabled.
- [ ] Backup storage is encrypted, off-host, access-controlled, and in a separate failure domain.

**Stop condition:** Do not start a public staging deployment if any mandatory safety gate above is unverified. The repository's default Compose file is a development/evaluation stack: it disables the OpenSearch security plugin and uses development-oriented settings. It is not a production Compose profile.

## 3. Pre-deployment checks

On the staging host, from a clean checkout of the approved candidate:

1. Verify the checked-out commit and record it:
   ```bash
   git rev-parse HEAD
   git status --short
   ```
2. Verify Docker and Compose versions:
   ```bash
   docker version
   docker compose version
   ```
3. Confirm the deployment-specific configuration is supplied from the approved secret/configuration store. Never copy a developer's local `.env`.
4. Render and inspect the final Compose configuration without publishing it to logs if it contains interpolated secrets:
   ```bash
   docker compose config --quiet
   ```
5. Confirm the final runtime configuration does not enable the OpenSearch security-plugin bypass and that the application is configured for the secured OpenSearch endpoint.
6. Confirm only the reverse proxy has public ingress. Verify the published API, frontend, database, Redis, and OpenSearch bindings against the approved network design.
7. Record image references/digests and the exact source commit before starting services.

Do not run the unmodified development Compose file as a public production deployment. The OpenSearch security-disabled configuration is explicitly unsuitable for that purpose.

## 4. Deployment and health verification

After all infrastructure gates are approved:

```bash
docker compose up --build -d
docker compose ps
docker compose logs --since=10m api worker scheduler
```

Record command output with secrets and personal data redacted.

Verify through the approved staging hostname:

- [ ] TLS certificate is valid and HTTP redirects to HTTPS.
- [ ] `GET /health` returns the expected liveness response.
- [ ] `GET /ready` returns success only when required dependencies are available.
- [ ] API, frontend, worker, scheduler, PostgreSQL, Redis, and secured OpenSearch are healthy.
- [ ] No database, Redis, or OpenSearch administrative port is publicly reachable.
- [ ] Request IDs appear in application responses and corresponding logs.
- [ ] Security headers are present at the public edge.
- [ ] No bootstrap/default credentials remain active beyond the controlled bootstrap procedure.

## 5. Functional acceptance

Use a controlled OAI-PMH fixture or a repository whose operator has approved staging traffic. Respect the source repository's rate limits and terms.

- [ ] Bootstrap the first administrator through the documented one-time procedure.
- [ ] Verify administrator, harvester, and viewer role boundaries.
- [ ] Verify an unauthenticated user cannot invoke administrative operations.
- [ ] Register a controlled OAI-PMH repository and validate its endpoint.
- [ ] Inspect Identify and ListMetadataFormats capability results.
- [ ] Run a bounded ListRecords harvest.
- [ ] Verify persistent job state, counters, logs, and resumption-token checkpoints.
- [ ] Verify raw XML, source identity, provenance, normalized metadata, and record version history.
- [ ] Verify deleted records are represented as tombstones and historical source data is retained.
- [ ] Verify indexing outbox events are processed and records become searchable.
- [ ] Verify public search results and record detail pages.
- [ ] Verify JSON, CSV, canonical XML, and Dublin Core XML exports.
- [ ] Create, disable, re-enable, and manually dispatch a test schedule.
- [ ] Verify audit events are visible only to authorized administrators.
- [ ] Verify a viewer cannot access repository, harvest, schedule, or user-management operations.

Record test repository name, endpoint, test window, and operator approval. Do not include credentials or private source data in evidence.

## 6. Failure, recovery, and security acceptance

- [ ] Interrupt a worker during a controlled harvest and verify safe resume from the persisted checkpoint.
- [ ] Interrupt Redis in staging and verify services recover without corrupting authoritative PostgreSQL records.
- [ ] Interrupt OpenSearch and verify outbox work remains recoverable.
- [ ] Restore OpenSearch discovery from PostgreSQL-backed records using the documented rebuild procedure.
- [ ] Run a PostgreSQL backup and verify the resulting archive.
- [ ] Encrypt the backup and transfer it to the approved off-host destination.
- [ ] Restore the backup into an isolated disposable database/environment.
- [ ] Verify restored record counts, repository/job state, and representative provenance.
- [ ] Exercise the egress policy with controlled deny tests and retain firewall/proxy evidence. Do not probe cloud metadata services or internal production addresses.
- [ ] Verify TLS, authentication, access restrictions, dependency exposure, and security headers.
- [ ] Conduct approved load, failure-recovery, and security tests; record scope, tooling, limits, and findings.

A successful backup command is not a successful restore test. A successful application-level URL validation is not proof of SSRF containment.

## 7. Acceptance evidence register

Attach links to restricted evidence in the approved internal evidence store. Do not upload secrets, raw environment files, private keys, or unredacted logs.

| Evidence ID | Evidence | Result | Evidence reference | Operator / UTC |
|---|---|---|---|---|
| INF-01 | Host and network baseline | Pending | | |
| SEC-01 | TLS and ingress review | Pending | | |
| SEC-02 | Egress deny-policy tests | Pending | | |
| SEC-03 | OpenSearch TLS/auth review | Pending | | |
| APP-01 | Deployment commit and image digests | Pending | | |
| APP-02 | Health/readiness checks | Pending | | |
| APP-03 | OAI-PMH harvest and checkpoint | Pending | | |
| APP-04 | Normalization, provenance, and tombstones | Pending | | |
| APP-05 | Indexing and public discovery | Pending | | |
| APP-06 | Exports and role-boundary tests | Pending | | |
| OPS-01 | Worker/scheduler recovery | Pending | | |
| OPS-02 | Encrypted backup verification | Pending | | |
| OPS-03 | Isolated restore verification | Pending | | |
| OPS-04 | Monitoring and alert delivery | Pending | | |
| NFR-01 | Load and performance test | Pending | | |
| NFR-02 | Security/accessibility review | Pending | | |

## 8. Go / no-go decision

A staging acceptance decision requires:

1. All infrastructure safety gates passed.
2. Functional acceptance passed with repeatable evidence.
3. Backup and isolated restore verified.
4. Egress restrictions and OpenSearch security independently verified.
5. No unresolved critical/high-severity security or data-integrity findings.
6. Monitoring and incident/rollback ownership assigned.
7. Operator and technical approver sign-off recorded.

| Decision | Value |
|---|---|
| Staging result | Pending |
| Open critical/high findings | Pending |
| Accepted exceptions | Pending |
| Technical approver | Pending |
| Operations approver | Pending |
| Decision timestamp (UTC) | Pending |

A staging pass does not automatically authorize production. Production requires a separate change approval and production-specific security, resilience, capacity, and recovery evidence.

## 9. Rollback

1. Stop further deployments and scheduled harvest dispatch if integrity is in question.
2. Preserve logs, job state, and incident evidence.
3. Take a current database snapshot if safe and useful for forensic review.
4. Restore the last verified PostgreSQL backup into the approved recovery environment when schema rollback is required.
5. Deploy the previously approved application revision compatible with the restored schema.
6. Rebuild OpenSearch from authoritative PostgreSQL data.
7. Verify readiness, representative records, search, and worker/scheduler state before reopening traffic.
8. Record the incident, recovery point, recovery time, data-loss assessment, and corrective actions.

Never run an older application against a newer migrated schema unless compatibility has been explicitly verified.

## 10. Current blockers

The GitHub repository connection does not provide access to the staging host, cloud provider, DNS control plane, firewall, secret manager, or deployment credentials. Live deployment and the checks requiring those systems therefore remain unexecuted.

To move from this runbook to an actual staging deployment, the release operator must provide or provision:
- A staging host/provider and approved access path.
- A staging DNS name and TLS/reverse-proxy plan.
- Network/egress enforcement and secured OpenSearch configuration.
- A secret manager and deployment-specific secrets.
- An encrypted off-host backup destination.
- An accountable operator for the deployment window.

Do not send credentials or private keys in this repository or chat. Use an approved secret manager and scoped access mechanism.
