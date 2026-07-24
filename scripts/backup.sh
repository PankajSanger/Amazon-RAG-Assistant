#!/bin/sh
# Nightly local backup of data/ (SQLite DB + cookies) and chroma_store/
# (vector index). Keeps the last 7 daily archives, deletes older ones.
# Intended to run via cron on the deployment host - see README for the
# crontab entry. Protects against application-level data loss (a bad
# reindex, accidental deletion); it does NOT protect against total
# instance/volume loss, since backups live on the same EBS volume as
# the data they're backing up.
set -e

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="$APP_DIR/backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/backup-$TIMESTAMP.tar.gz" -C "$APP_DIR" data chroma_store

ls -1t "$BACKUP_DIR"/backup-*.tar.gz | tail -n +8 | xargs -r rm --
