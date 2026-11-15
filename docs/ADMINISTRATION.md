# Administration console

## Scope

The administration console at `/admin` provides a lightweight operator interface for repository registration, endpoint validation, one-off and recurring harvest scheduling, job monitoring, resuming failed/paused jobs, and dispatching pending search-index outbox events.

## Authentication model

The current backend uses a single configured administrative bearer token (`ADMIN_API_TOKEN`). It is not a multi-user identity system and does not provide individual accounts, permissions, audit attribution, password reset, or SSO.

The operator enters the token into the page. It remains in React component memory only and is not written to localStorage, sessionStorage, cookies, or browser persistence. Requests go to a same-origin Next.js route handler, which forwards the bearer token to a strict allowlist of administrative API paths. The browser does not connect directly to the internal API hostname and the token is not embedded in the frontend build.

The proxy allowlist includes only:
- Repository list, registration, detail, update, disable, and endpoint validation.
- Harvest list, create, detail, and resume.
- Pending indexing event dispatch.

The backend remains the authority for token validation. The proxy is not a substitute for backend authorization.

## Security requirements

- Configure a unique random `ADMIN_API_TOKEN` of at least 32 characters.
- Use HTTPS for the public frontend and API in production.
- Restrict access to the admin page at the reverse proxy or identity-aware access layer.
- Do not expose the OpenSearch, PostgreSQL, or Redis ports publicly.
- Rotate the administrative token if an operator session or workstation is compromised.
- Replace the single-token model with individual users, role-based permissions, and auditable sessions before multi-operator production use.
