#!/usr/bin/env bash
set -euo pipefail
umask 077

BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_FILE="${BACKUP_DIR}/indrastra-harvester-${TIMESTAMP}.dump"

mkdir -p "$BACKUP_DIR"
echo "Creating PostgreSQL backup: $BACKUP_FILE"
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$BACKUP_FILE"

if [[ ! -s "$BACKUP_FILE" ]]; then
  echo "Backup file is empty; removing failed backup." >&2
  rm -f "$BACKUP_FILE"
  exit 1
fi

echo "Verifying archive structure..."
docker compose exec -T db pg_restore --list < "$BACKUP_FILE" >/dev/null
find "$BACKUP_DIR" -type f -name 'indrastra-harvester-*.dump' -mtime "+$RETENTION_DAYS" -delete

echo "Backup completed: $BACKUP_FILE"
