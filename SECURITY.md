# Security Policy

## Supported versions

During the pre-release phase, security fixes are applied to the active development branch.

## Reporting a vulnerability

Please report vulnerabilities privately to the project maintainers using a designated security contact published in the repository. Do not include secrets, personal data, or exploit details in public issues.

## Security-sensitive areas

- User-supplied repository URLs and server-side request forgery (SSRF).
- DNS rebinding and outbound network access.
- XML parsing and external entity expansion.
- Archive and decompression handling.
- Authentication and authorization.
- Secrets and configuration.
- Search query handling.
- Background job permissions.
- Dependency and container images.

## Current repository-endpoint controls

- Only HTTP and HTTPS endpoints on standard ports are accepted.
- URL credentials, fragments, localhost, and non-public IP destinations are rejected.
- DNS answers are checked and all returned addresses must be globally routable.
- Redirects are not followed automatically by the OAI-PMH client.
- OAI response bodies are bounded while streaming and XML DTD/entity declarations are rejected.
- Administrative endpoints accept the bootstrap `ADMIN_API_TOKEN` or a short-lived JWT for a user with the required role.
- User passwords are hashed with Argon2id; five failed login attempts trigger a 15-minute account lockout.
- JWT signing requires a secret of at least 32 characters; use a separate `JWT_SECRET_KEY` in production.
- Account deactivation is checked on every authenticated request, invalidating existing tokens for that account.
- API responses include request IDs and baseline browser security headers; the frontend also emits security headers.
- Backend and frontend runtime containers run as non-root users.
- The readiness endpoint verifies PostgreSQL, Redis, and OpenSearch connectivity.

**Important deployment limitation:** application-level DNS validation alone cannot completely eliminate DNS rebinding because the HTTP client's connection-time DNS lookup may differ from the validation lookup. Production deployments must enforce outbound network restrictions through a firewall or egress proxy that blocks private, loopback, link-local, multicast, reserved, and cloud metadata destinations. Do not expose the development stack directly to the public internet.

## Baseline controls

- Enforce request timeouts and response-size limits.
- Hash user passwords with Argon2id and enforce account lockout for repeated failed logins.
- Keep secrets out of source control and logs.
- Apply least privilege to database and service accounts.
- Keep dependencies and container images patched.
- Encrypt database backups and store them off-host; test restores regularly.

## Remaining authentication limitations

MFA, SSO, password reset, refresh-token rotation, a token revocation list, fine-grained per-resource permissions, and individual audit attribution for bootstrap-token actions are not implemented. Keep the admin console behind HTTPS and an identity-aware access layer. The platform is not production-ready until these gaps and the deployment release gates are reviewed.
