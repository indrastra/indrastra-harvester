# Milestone 13 — Production hardening

**Status:** In progress  
**Scope:** Repository-level security controls and release engineering. No staging deployment is included in this milestone slice.

Milestone 13 reduces avoidable software-supply-chain and deployment risk. Passing automated checks is necessary but does not establish that a live environment is secure or production-ready.

## Delivered in this change set

- Dependency review on pull requests; new dependencies with high or critical known vulnerabilities fail the review.
- Repository-history secret scanning with redacted findings.
- Filesystem scanning for vulnerabilities, insecure configuration, and secrets.
- Backend and frontend container image vulnerability scanning.
- Weekly scheduled security scans and manual workflow dispatch.
- Explicit least-privilege workflow permissions and concurrency cancellation.
- Python and JavaScript dependency audit steps in the normal CI pipeline.
- This milestone record, including remaining gates and evidence expectations.

## Acceptance criteria

- [ ] Dependency review completes on pull requests.
- [ ] Secret scan completes without exposed credentials.
- [ ] Filesystem scan completes without unresolved high/critical findings.
- [ ] Backend and frontend images build and scan without unresolved high/critical findings.
- [ ] Python dependency audit completes without unresolved high/critical advisories.
- [ ] Frontend dependency audit completes without unresolved high/critical advisories.
- [ ] Existing backend, integration, frontend, container, and CodeQL checks remain green.
- [ ] Findings are triaged; accepted exceptions have owner, rationale, expiry, and compensating control.

A scanner failure must not be converted into a pass by silently suppressing findings. Any allowlist or ignore rule must be narrow, documented, time-bounded, and reviewed.

## Operational hardening backlog

The following require additional implementation, operator decisions, or access to deployment infrastructure:

1. Replace mutable container tags with reviewed immutable digests for deployment.
2. Generate and publish an SBOM for each release; retain provenance and build attestations.
3. Sign release artifacts/images and verify signatures before deployment.
4. Enforce production OpenSearch TLS/authentication and least-privilege roles.
5. Enforce network egress restrictions outside the application to mitigate SSRF and DNS rebinding.
6. Implement MFA/SSO, password recovery, refresh-token rotation, revocation, and finer-grained authorization.
7. Establish encrypted off-host backup retention and recurring isolated restore tests.
8. Add service-level monitoring, alert routing, log retention, and incident response ownership.
9. Complete load, resilience, penetration, accessibility, and multi-tenant isolation testing.
10. Complete Milestone 12 staging acceptance and record evidence before any production approval.

## Security exception register

No scanner exceptions are approved by this document. Record any future exception in a dedicated reviewed change with:
- finding identifier and affected component;
- severity and exploitability assessment;
- owner and approver;
- rationale and compensating controls;
- expiry/review date; and
- remediation issue.

## Release gate

The GitHub pre-release v0.1.0-rc.1 remains an evaluation release. Milestone 13 CI results do not replace staging acceptance. Do not publish a stable release or label the platform production-ready until the operational gates above and the staging acceptance runbook have been completed with evidence.
