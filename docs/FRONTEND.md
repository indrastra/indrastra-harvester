# Public discovery frontend

## Overview

The public discovery application is a Next.js App Router application in `frontend/`. It consumes the FastAPI public search and record-detail endpoints through server-to-server requests. It does not receive or expose the administrative bearer token.

## Pages

- `/`: search page with free-text search, repository ID, resource type, publication-year filters, sorting, and pagination.
- `/records/{id}`: normalized metadata detail page with repository and OAI-PMH provenance.

## Configuration

Set `HARVESTER_API_URL` to the API base URL ending in `/api/v1`.

- Local development: `http://localhost:8000/api/v1`
- Docker Compose: `http://api:8000/api/v1`

The frontend server renders search and detail requests dynamically. The public search API returns HTTP 503 when OpenSearch is unavailable; the frontend displays an availability message rather than fabricating an empty result set.

## Local development

From `frontend/`:

```bash
npm install
HARVESTER_API_URL=http://localhost:8000/api/v1 npm run dev
```

The site listens on port 3000.

## Docker

The root Compose stack includes a frontend service built from `frontend/Dockerfile`. Run `docker compose up --build -d` from the repository root and open `http://localhost:3000`.

## Security boundary

The public frontend calls only public search and record detail endpoints. Administrative routes remain bearer-token protected and are not exposed through this application. OpenSearch and PostgreSQL must remain on private service networks in production.
