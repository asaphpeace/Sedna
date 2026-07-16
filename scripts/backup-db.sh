#!/usr/bin/env bash
# Dumps the production Postgres database to a timestamped, gzipped file.
# Intended to run via cron, e.g.:
#   0 3 * * * /home/ubuntu/sedna/scripts/backup-db.sh >> /home/ubuntu/backup.log 2>&1
#
# Free-tier note: EC2's 30GB EBS volume is the only free storage here.
# Keeps the last 14 daily backups locally and prunes older ones automatically.
# For off-instance durability, optionally sync BACKUP_DIR to S3
# (5GB/month free for 12 months) — see the commented aws s3 sync line below.
set -euo pipefail
cd "$(dirname "$0")/.."

BACKUP_DIR="${BACKUP_DIR:-$HOME/sedna-backups}"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUT_FILE="$BACKUP_DIR/sedna-$TIMESTAMP.sql.gz"

set -a; source .env; set +a

docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$OUT_FILE"

echo "Backup written to $OUT_FILE"

# Optional: sync to S3 for off-instance durability (uncomment + `aws configure` first)
# aws s3 sync "$BACKUP_DIR" s3://your-bucket-name/sedna-backups/

# Prune backups older than 14 days
find "$BACKUP_DIR" -name "sedna-*.sql.gz" -mtime +14 -delete
