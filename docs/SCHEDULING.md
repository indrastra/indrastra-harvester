# Scheduled harvesting

Recurring harvest definitions are persisted in PostgreSQL. Celery Beat runs a dispatcher every 60 seconds. The dispatcher locks due schedule rows with `FOR UPDATE SKIP LOCKED`, creates durable harvest jobs, advances each schedule, commits, and only then sends jobs to Celery.

The schedule definition is authoritative in PostgreSQL. Celery Beat stores only the fixed one-minute dispatcher cadence, not individual schedule state.

## Supported frequencies

- `hourly`: next run one hour after dispatch.
- `daily`: next run 24 hours after dispatch.
- `weekly`: next run seven days after dispatch.

All schedule timestamps and cadence calculations use UTC. These are interval-based schedules, not local wall-clock calendar schedules.

## Incremental harvesting

For the first scheduled run, `from` is omitted and the repository is harvested from its available beginning. After a successful run, the next scheduled job uses the date of `last_success_at` as its inclusive OAI-PMH `from` date and the current UTC date as `until`. The overlap is intentional: source record upserts are idempotent and preserve versions.

A failed or paused job does not advance `last_success_at`. Operators can resume the job from the administration console or the harvest API.

## API

Schedule endpoints require an admin or harvester role.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/schedules` | Create an hourly, daily, or weekly schedule |
| GET | `/api/v1/schedules` | List schedules |
| PATCH | `/api/v1/schedules/{id}` | Enable or disable a schedule |
| POST | `/api/v1/schedules/{id}/run-now` | Mark an enabled schedule due immediately |
| DELETE | `/api/v1/schedules/{id}` | Soft-disable a schedule |

## Reliability

- Schedule advancement and job creation are committed in one database transaction.
- Row locking prevents two dispatcher instances from creating the same due job.
- The repository advisory lock prevents overlapping repository harvest execution.
- A broker outage leaves the durable job in failed state with an error; it can be resumed manually.
- Harvest records, source versions, normalized records, and indexing outbox events retain their normal transaction semantics.
- Monitor the scheduler service, Celery worker queue, and schedule `last_error` fields.

## Deployment

Docker Compose runs a dedicated `scheduler` service using Celery Beat. Run `docker compose up --build -d` to start it. In production, run only one active Beat instance unless a distributed scheduler/leader-election strategy is deployed.
