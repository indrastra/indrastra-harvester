# Deployment and operations

## Deployment status

The supplied Docker Compose stack is a development and small-scale evaluation environment. It is not a hardened production deployment. Production operators must provide TLS termination, firewall/egress controls, secure OpenSearch configuration, secret management, monitoring, and tested backups.

## Prerequisites

- Docker Engine and Docker Compose v2.
- A host with sufficient memory for PostgreSQL, Redis, OpenSearch, API, worker, scheduler, and Next.js.
- A DNS name and TLS reverse proxy for public access.
- A firewall or egress proxy capable of restricting outbound destinations.

## Configuration

Copy `.env.example` to `.env` and replace every placeholder. Generate independent secrets, for example:

```bash
openssl rand -hex 32
```

Set at least:

- `POSTGRES_PASSWORD`: unique database password.
- `ADMIN_API_TOKEN`: bootstrap/emergency administrator bearer token, at least 32 characters.
- `JWT_SECRET_KEY`: independent JWT signing key, at least 32 characters.
- `APP_SECRET_KEY`: application secret, at least 32 characters.
- `ACCESS_TOKEN_EXPIRE_MINUTES`: short access-token lifetime.
- `DATABASE_URL`, `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`.
- `OPENSEARCH_URL`, `OPENSEARCH_USERNAME`, and `OPENSEARCH_PASSWORD` when using secured OpenSearch.

Do not commit `.env` or place secrets in frontend build arguments. The frontend receives only the internal API base URL; the admin token is entered at runtime.

The default published ports bind to loopback (`127.0.0.1`). Place a TLS reverse proxy in front of the frontend and API. Do not change these bindings to `0.0.0.0` without an explicit firewall and network design.

## Start the stack

```bash
docker compose up --build -d
docker compose ps
docker compose logs -f api worker scheduler
```

The migration service runs Alembic before the API, worker, and scheduler start. The API readiness probe checks PostgreSQL, Redis, and OpenSearch:

- `GET /health`: liveness only.
- `GET /ready`: dependency readiness; returns HTTP 503 if a required dependency is unavailable.

Open the discovery portal at `http://127.0.0.1:3000` and the operator console at `http://127.0.0.1:3000/admin`.

## Bootstrap the first administrator

Use the bootstrap token to create the first account. Replace the example values and use a securely delivered initial password:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/users \
  -H "Authorization: Bearer $ADMIN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.org","full_name":"Platform Administrator","password":"replace-with-a-long-initial-password","roles":["admin"]}'
```

Sign in through the admin console using the new account. Keep the bootstrap token in a secret manager for emergency access and rotate it when required.

## Network and SSRF controls

Repository endpoint validation is defense in depth, not a complete egress security boundary. Application DNS checks cannot fully prevent DNS rebinding because the HTTP client may resolve the hostname again at connection time.

Production network policy must block outbound access to:
- Loopback, private, link-local, multicast, reserved, and unspecified address ranges.
- Cloud metadata endpoints and platform control-plane addresses.
- Internal databases, Redis, OpenSearch, container control sockets, and management networks.

Allow only required outbound HTTP/HTTPS destinations through a controlled egress proxy where possible. Do not expose PostgreSQL or Redis ports. The development Compose file binds OpenSearch to loopback and disables its security plugin; production must enable OpenSearch authentication, TLS, and least-privilege roles before network exposure.

## Background processing

- Run one active Celery Beat scheduler unless leader election or a distributed scheduler is configured.
- Scale Celery workers independently according to CPU, memory, repository rate limits, and queue depth.
- Monitor worker failures, schedule `last_error`, harvest checkpoints, and indexing outbox failures.
- Do not assume a queued job has completed until its persistent job state reports completion.

## Backups and recovery

Create a verified PostgreSQL custom-format backup:

```bash
bash scripts/backup-postgres.sh
```

Restore a backup (destructive; stops application services and asks for confirmation):

```bash
bash scripts/restore-postgres.sh ./backups/indrastra-harvester-YYYYMMDDTHHMMSSZ.dump
```

Backups are not encrypted by the script. Encrypt them before off-host storage, restrict access, define retention, and test restore procedures regularly. Store backups in a separate failure domain. OpenSearch is a rebuildable projection; the PostgreSQL source records and normalized records are authoritative. Rebuild the search index after recovery using the indexing operations.

## Upgrades

1. Take and verify a database backup.
2. Review release notes and migration revisions.
3. Pull the approved release and rebuild images.
4. Run `docker compose up --build -d`; the migration service applies database upgrades.
5. Verify `/health`, `/ready`, API documentation, public search, record details, harvest execution, schedule dispatch, and export endpoints.
6. Monitor worker and scheduler logs after upgrade.

Do not run multiple migration services concurrently.

## Production acceptance checklist

- [ ] TLS enabled for every public endpoint.
- [ ] Reverse proxy restricts access to `/admin` and administrative API paths.
- [ ] Unique production secrets stored outside source control.
- [ ] OpenSearch security plugin enabled with authentication, TLS, and least privilege.
- [ ] Database and Redis not publicly reachable.
- [ ] Egress firewall/proxy blocks private, link-local, loopback, reserved, and metadata destinations.
- [ ] PostgreSQL backups encrypted, off-host, and restore-tested.
- [ ] Monitoring and alerting cover database, Redis, OpenSearch, API readiness, Celery workers, Beat scheduler, and indexing outbox.
- [ ] Single Beat instance or distributed leader election.
- [ ] Authentication gaps reviewed: MFA, SSO, password reset, refresh-token rotation, token revocation, and fine-grained permissions.
- [ ] Load, failure-recovery, accessibility, and security testing completed.

Do not label the platform production-ready until every applicable gate is complete.
