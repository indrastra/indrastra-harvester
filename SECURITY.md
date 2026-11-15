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
- Administrative write endpoints require a configured bearer token.

**Important deployment limitation:** application-level DNS validation alone cannot completely eliminate DNS rebinding because the HTTP client's connection-time DNS lookup may differ from the validation lookup. Production deployments must enforce outbound network restrictions through a firewall or egress proxy that blocks private, loopback, link-local, multicast, reserved, and cloud metadata destinations. Do not expose the development stack directly to the public internet.

## Baseline controls

- Enforce request timeouts and response-size limits.
- Hash user passwords with a modern password hashing scheme when user accounts are introduced.
- Keep secrets out of source control and logs.
- Apply least privilege to database and service accounts.
- Keep dependencies and container images patched.
