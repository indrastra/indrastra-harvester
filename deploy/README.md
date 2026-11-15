# Local deployment

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

2. Replace `APP_SECRET_KEY`, `ADMIN_API_TOKEN`, and database credentials with strong random values. Do not commit `.env`.

3. Start the stack:

   ```bash
   docker compose up --build -d
   ```

Docker Compose starts PostgreSQL and Redis, runs the Alembic migration service to completion, and then starts the API and Celery worker.

4. Check the API:

   ```bash
   curl http://localhost:8000/health
   ```

5. Open the API documentation at `http://localhost:8000/docs`.

## Development limitations

- OpenSearch security is disabled in this local development Compose configuration. Do not expose port 9200 to untrusted networks.
- The administrative API uses a shared bootstrap bearer token. A full user/role management system is planned for a later milestone.
- Repository endpoint validation must be backed by outbound firewall or egress-proxy restrictions in production.
- Configure backups, TLS termination, secrets management, monitoring, and network policies before production use.

## Database migrations

The `migrate` service applies migrations automatically on stack startup. For a manual migration:

```bash
docker compose run --rm migrate alembic upgrade head
```
