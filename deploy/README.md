# Déploiement — VPS unique (Hetzner)

Tout tourne sur une seule machine avec Docker Compose, derrière **Caddy** qui
gère l'HTTPS automatiquement (Let's Encrypt). Aucun retraitement des données :
la base déjà calculée en local est migrée telle quelle.

## Ce que contiennent ces fichiers

| Fichier | Rôle |
|---|---|
| `../docker-compose.prod.yml` | Pile de prod autonome (db, api, worker, web, caddy). Seul Caddy expose 80/443. |
| `Caddyfile` | Reverse proxy + TLS. Route `/admin` et `/docs` vers l'API, le reste vers le front. |
| `.env.prod.example` | Modèle des variables d'environnement (secrets, domaine, clé LLM). |
| `migrate-data.sh` | Copie base + archives depuis le local vers la prod (sans recalcul). |
| `backup.sh` | Sauvegarde quotidienne (pg_dump + archive de `data/`). |

## 1. Provisionner le VPS

- Hetzner Cloud, **CX22** (2 vCPU / 4 Go RAM / 40 Go) suffit largement ; prévoir
  un **volume** ou un CX32 si `data/` doit grandir (3,7 Gio aujourd'hui).
- Image Ubuntu 24.04. Installer Docker :
  ```bash
  curl -fsSL https://get.docker.com | sh
  ```
- Pare-feu (Hetzner Cloud Firewall ou `ufw`) : n'ouvrir que **22, 80, 443**.

## 2. DNS

Créer un enregistrement **A** `faso.example.org` → IP du VPS (et `AAAA` si IPv6).
Attendre la propagation avant le premier lancement (Caddy a besoin du domaine
résolu pour obtenir le certificat).

## 3. Déployer

```bash
git clone git@github.com:mazou1/faso-civic.git /srv/faso
cd /srv/faso
cp deploy/.env.prod.example .env
nano .env          # domaine + secrets (voir les commandes openssl dans le fichier)

docker compose -f docker-compose.prod.yml up -d --build
```

Caddy obtient le certificat tout seul. Le site est en ligne sur
`https://faso.example.org`, le back-office sur `/admin`.

## 4. Migrer les données locales (sans rien relancer)

Depuis votre **machine de dev** (base et `data/` locaux) :

```bash
./deploy/migrate-data.sh user@IP_DU_VPS /srv/faso
```

Le script : dump de la base (~50-100 Mo), copie vers la prod, `rsync` des
archives `data/` (une fois), puis restauration. Détail manuel équivalent :

```bash
# local
docker compose exec -T db pg_dump -U faso -Fc faso > faso.dump
scp faso.dump user@vps:/srv/faso/
rsync -avz backend/data/ user@vps:/srv/faso/backend/data/
# vps
docker compose -f docker-compose.prod.yml up -d db
cat faso.dump | docker compose -f docker-compose.prod.yml exec -T db \
  pg_restore -U faso -d faso --clean --if-exists --no-owner
docker compose -f docker-compose.prod.yml up -d
```

> Des avertissements bénins peuvent apparaître au `pg_restore` (extension
> `postgis` déjà présente dans l'image) — sans conséquence.

Ensuite le worker **poursuit en incrémental** : il ne collecte que le nouveau.

## 5. Exploitation

```bash
# Logs
docker compose -f docker-compose.prod.yml logs -f api worker caddy

# Après un git pull (le code est baké dans les images api/worker/web)
docker compose -f docker-compose.prod.yml up -d --build

# Traitements manuels (validation, annuaire…)
docker compose -f docker-compose.prod.yml exec api python -m app.validation 0.9
docker compose -f docker-compose.prod.yml exec api python -m app.annuaire
```

## 6. Sauvegardes

```bash
chmod +x deploy/backup.sh
# cron quotidien à 3h
( crontab -l 2>/dev/null; echo "0 3 * * * cd /srv/faso && ./deploy/backup.sh >> /var/log/faso-backup.log 2>&1" ) | crontab -
```

Pousser aussi les sauvegardes hors du VPS (Hetzner Storage Box, rclone vers R2…)
pour se prémunir d'une perte de la machine.

## Durcissement (rappels)

- **Secrets neufs** en prod (ne pas réutiliser le `.env` de dev) : régénérer
  `FASO_SECRET_KEY`, `FASO_ADMIN_PASSWORD`, `POSTGRES_PASSWORD`.
- **Postgres non exposé** : la pile de prod ne publie aucun port de base — n'y
  ajoutez pas de mapping `5432`.
- **`/admin`** : envisager une restriction par IP dans le `Caddyfile` (bloc
  commenté `@adminblocked`) en plus du mot de passe.
- Garder le système à jour (`unattended-upgrades`).
