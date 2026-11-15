# Database migrations

Alembic manages schema changes.

## Local setup

1. Copy .env.example to .env and set DATABASE_URL.
2. Install the project and dependencies.
3. Apply the schema:

   ```bash
   alembic upgrade head
   ```

4. Create future revisions with:

   ```bash
   alembic revision --autogenerate -m "describe change"
   ```

Review generated migrations before applying them. Do not edit an already-released migration; create a new revision instead.
