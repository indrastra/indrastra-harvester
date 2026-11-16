#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || ! -f "$1" ]]; then
  echo "Usage: $0 path/to/backup.dump" >&2
  exit 2
fi

BACKUP_FILE="$1"
echo "WARNING: This will replace the current PostgreSQL database."
read -r -p "Type RESTORE to continue: " CONFIRM
if [[ "$CONFIRM" != "RESTORE" ]]; then
  echo "Restore cancelled."
  exit 1
fi

docker compose stop api worker scheduler frontend
restart_services() {
  docker compose up -d api worker scheduler frontend
}
trap restart_services EXIT

echo "Restoring database from $BACKUP_FILE"
docker compose exec -T db sh -c 'pg_restore --clean --if-exists --no-owner -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < "$BACKUP_FILE"
echo "Database restore completed. Application services will be restarted."
