#!/usr/bin/env bash
# Sauvegarde de production : base (pg_dump) + archives (data/).
# À lancer depuis la racine du dépôt sur le VPS. Idéal en cron quotidien.
#
#   0 3 * * *  cd /srv/faso && ./deploy/backup.sh >> /var/log/faso-backup.log 2>&1
set -euo pipefail

COMPOSE="docker compose -f docker-compose.prod.yml"
DEST="${FASO_BACKUP_DIR:-/srv/faso-backups}"
HORODATAGE="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$DEST"

echo "[$(date)] Dump de la base…"
$COMPOSE exec -T db pg_dump -U faso -Fc faso > "$DEST/faso-$HORODATAGE.dump"

echo "[$(date)] Archive de data/ (PDF/HTML bruts)…"
tar -czf "$DEST/data-$HORODATAGE.tar.gz" -C backend data

# Rétention : garder les 14 derniers de chaque type
ls -1t "$DEST"/faso-*.dump      2>/dev/null | tail -n +15 | xargs -r rm -f
ls -1t "$DEST"/data-*.tar.gz    2>/dev/null | tail -n +15 | xargs -r rm -f

echo "[$(date)] Sauvegarde terminée dans $DEST"
du -sh "$DEST"/faso-"$HORODATAGE".dump "$DEST"/data-"$HORODATAGE".tar.gz
