# Administration console

## Scope

The administration console at `/admin` provides a lightweight operator interface for repository registration, endpoint validation, one-off and recurring harvest scheduling, job monitoring, resuming failed/paused jobs, and dispatching pending search-index outbox events.

## Authentication model

The backend supports short-lived JWT access tokens, Argon2 password hashes, and admin/harvester/viewer roles. The `ADMIN_API_TOKEN` remains available as a bootstrap and emergency administrator credential. See [Authentication and RBAC](AUTHENTICATION.md) for role boundaries and limitations.

Administrators can sign in with email/password to obtain a short-lived JWT, or use the bootstrap bearer token. The credential remains in React component memory only and is not written to localStorage, sessionStorage, cookies, or browser persistence. Requests go to a same-origin Next.js route handler, which forwards the bearer token to a strict allowlist of administrative API paths. The browser does not connect directly to the internal API hostname and credentials are not embedded in the frontend build.

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
- Configure JWT_SECRET_KEY separately from APP_SECRET_KEY and protect the bootstrap token in a secret manager.
- Enable MFA/SSO and password recovery before broad multi-operator production use.
