# OAI-PMH harvesting module

oai_client.py contains the first protocol client implementation.

Current scope:
- All six OAI-PMH verbs.
- Namespace-aware XML parsing.
- Protocol error detection.
- HTTP timeout and response-size limits.
- No automatic redirect following.
- ListRecords resumption-token iteration.

Not yet implemented:
- Persisted job orchestration and checkpoints.
- DNS/IP-based SSRF protection for repository URLs.
- Retry/backoff policy.
- Metadata normalization and database persistence.
- Full OAI-PMH conformance test suite.

Do not deploy this module as a public service until the remaining security and
operational controls are implemented.
