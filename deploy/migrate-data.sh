#!/usr/bin/env bash
# Migration des données LOCALES vers la PROD — à lancer depuis votre machine de
# dev, à la racine du dépôt. Ne recalcule rien : copie la base déjà traitée +
# les archives. Usage :
#
#   ./deploy/migrate-data.sh user@vps.hetzner /srv/faso
#
set -euo pipefail

CIBLE="${1:?Usage: migrate-data.sh user@hote /chemin/du/depot/sur/le/vps}"
CHEMIN="${2:?Usage: migrate-data.sh user@hote /chemin/du/depot/sur/le/vps}"
DUMP="faso-migration-$(date +%Y%m%d-%H%M%S).dump"

echo "→ 1/4  Dump de la base locale (format custom, compressé)…"
docker compose exec -T db pg_dump -U faso -Fc faso > "$DUMP"
du -sh "$DUMP"

echo "→ 2/4  Copie du dump vers la prod…"
scp "$DUMP" "$CIBLE:$CHEMIN/$DUMP"

echo "→ 3/4  Copie des archives data/ (3-4 Gio, une fois)…"
rsync -avz --info=progress2 backend/data/ "$CIBLE:$CHEMIN/backend/data/"

echo "→ 4/4  Restauration sur la prod…"
echo "   Sur le VPS, la db doit tourner :  docker compose -f docker-compose.prod.yml up -d db"
ssh "$CIBLE" "cd $CHEMIN && cat $DUMP | docker compose -f docker-compose.prod.yml exec -T db pg_restore -U faso -d faso --clean --if-exists --no-owner"

echo "✓ Terminé. Démarrez le reste :  ssh $CIBLE 'cd $CHEMIN && docker compose -f docker-compose.prod.yml up -d'"
rm -f "$DUMP"
