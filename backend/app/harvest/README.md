# Persistent harvesting engine

The harvesting API is available under `/api/v1/harvests` and requires the administrative bearer token.

- `POST /api/v1/harvests`: enqueue a ListRecords harvest.
- `GET /api/v1/harvests`: list persistent jobs.
- `GET /api/v1/harvests/{id}`: inspect status, counters, and execution logs.
- `POST /api/v1/harvests/{id}/resume`: resume a paused or failed job from its saved checkpoint.

Each OAI record is keyed by repository ID + OAI identifier. Original record XML is retained. Deleted headers become tombstones rather than physical deletions. Resumption-token checkpoints are committed in the same transaction as each processed page. When a token is present, subsequent requests send only `verb=ListRecords` and `resumptionToken`.

Run the database migrations before starting workers. Configure production egress filtering as described in SECURITY.md; application DNS checks alone do not eliminate DNS rebinding risk.
