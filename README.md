# Faso Civic — Plateforme civique Burkina Faso

Plateforme citoyenne indépendante qui agrège, structure et recroise l'information
publique burkinabè (journal officiel, conseil des ministres, nominations, budget,
communiqués…) et la restitue avec cartes et graphiques. Chaque donnée affichée est
liée à son document source officiel.

📄 Cadrage complet : [`cadrage-plateforme-civique-v2.md`](cadrage-plateforme-civique-v2.md)
— inspiré de [vie-publique.sn](https://www.vie-publique.sn) (Code for Senegal).

## Stack

Python 3.12 · FastAPI · PostgreSQL 17 + PostGIS · SQLAlchemy/Alembic · SQLAdmin
(back-office) · APScheduler (worker d'ingestion) · httpx/selectolax/feedparser ·
pdfplumber + Tesseract (OCR) · frontend Vue 3 + MapLibre + ECharts (phase 3).

## Démarrage (Docker)

```bash
cp .env.example .env   # ajuster les mots de passe
docker compose up --build
```

- API + doc OpenAPI : http://localhost:8001/docs
- Back-office : http://localhost:8001/admin
- Le worker collecte les flux RSS toutes les 30 minutes.

## Développement local

```bash
docker compose up -d db            # Postgres/PostGIS sur localhost:5434
cd backend
uv venv && uv pip install -e ".[dev]"
.venv/bin/alembic upgrade head
.venv/bin/python -m app.ingestion.run all      # collecte manuelle (RSS + Conseil des ministres)
.venv/bin/uvicorn app.main:app --reload        # API sur :8000
.venv/bin/pytest
```

## Chaîne Conseil des ministres (phase 1)

```bash
python -m app.ingestion.run conseil_ministres  # collecte les CR (API REST WordPress, cat. 23)
FASO_ANTHROPIC_API_KEY=sk-ant-... \
python -m app.extraction.run 5                 # structuration LLM : décisions + nominations
# → valider dans /admin (statut a_valider → valide), puis :
python -m app.annuaire                         # consolide les mandats (annuaire de l'État)
```

L'extraction utilise l'API Claude (`claude-opus-4-8`, sortie structurée Pydantic).
Rien n'est publié sans validation humaine : `/decisions` et `/nominations`
n'exposent que les entités validées, chacune liée à son document source.

## Structure

```
backend/
  app/
    api/          # routes publiques (documents, sources, recherche plein texte)
    ingestion/    # collecteurs (base, rss, …), registre, scheduler
    extraction/   # PDF → texte (pdfplumber + OCR fra)
    admin.py      # back-office SQLAdmin (validation des extractions)
    models.py     # schéma : source, document, personne, nomination, mandat, run
  alembic/        # migrations
data/             # archives brutes (PDF/HTML) — hors git, à sauvegarder
```

## Licence

GPL-3.0.
