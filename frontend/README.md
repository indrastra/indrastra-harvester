# IndraStra Harvester — Web application

The public discovery portal uses Next.js App Router, React, and TypeScript.

## Features

- Server-rendered scholarly search results.
- Search across titles, creators, subjects, descriptions, identifiers, and publishers.
- Filters for repository ID, resource type, and publication year.
- Relevance, newest, and oldest sorting.
- Pagination.
- Public normalized-record detail pages with source provenance.

## Local development

From this directory, install dependencies and run the development server:

    npm install
    HARVESTER_API_URL=http://localhost:8000/api/v1 npm run dev

Open http://localhost:3000.

## Docker

The root Docker Compose file builds this frontend and passes HARVESTER_API_URL=http://api:8000/api/v1 for server-to-server API calls.

Administrators can sign in with email/password to obtain a short-lived JWT or use the bootstrap ADMIN_API_TOKEN. Credentials remain in page memory and are forwarded through an allowlisted same-origin Next.js route handler; they are not persisted. The console also supports user creation and activation/deactivation. See docs/ADMINISTRATION.md and docs/AUTHENTICATION.md.
