# Security Policy

## Supported versions

During the pre-release phase, security fixes are applied to the active development branch.

## Reporting a vulnerability

Please report vulnerabilities privately to the project maintainers using a designated security contact published in the repository. Do not include secrets, personal data, or exploit details in public issues.

## Security-sensitive areas

- User-supplied repository URLs and SSRF.
- XML parsing and XXE.
- Archive and decompression handling.
- Authentication and authorization.
- Secrets and configuration.
- Search query handling.
- Background job permissions.
- Dependency and container images.

## Baseline controls

- Disable XML external entities and external DTD loading.
- Restrict outbound requests and revalidate redirects.
- Enforce timeouts and response-size limits.
- Hash passwords with a modern password hashing scheme.
- Keep secrets out of source control and logs.
- Apply least privilege to database and service accounts.
