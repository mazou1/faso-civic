# Contribuer à FasoCivic

Merci de votre intérêt ! Ce projet vit de contributions : nouvelles sources de
données, corrections, améliorations du site, relecture des extractions.

## Mise en place

Suivre le [README](README.md#développement-local). En résumé : Postgres via
Docker (`docker compose up -d db`), backend Python 3.12 avec
[uv](https://github.com/astral-sh/uv), frontend Vue 3 avec Vite.

Ports locaux non standard (des projets voisins occupent les ports usuels) :
Postgres **5434**, API **8001**, site **8090**.

## Conventions

- **Tout est en français** : code (noms de variables, docstrings), interface,
  messages de commit. Le projet s'adresse à des lecteurs francophones.
- **Rien n'est publié sans validation humaine.** Toute nouvelle extraction
  automatique doit produire des entités `statut_validation='a_valider'` ; les
  routes publiques ne servent que le statut `valide`. Ne contournez jamais ce
  principe.
- **Chaque donnée est sourcée.** Une nouvelle table de faits porte un
  `document_id` (ou un `source_libre` explicite) ; une nouvelle vue affiche le
  lien vers la source.
- **Archiver avant de traiter.** Un collecteur écrit le brut dans `data/`
  (voir `Collector.archive`) avant toute extraction.
- Politesse de collecte : ≥ 1 s entre requêtes, User-Agent identifiant le
  projet (déjà gérés par `Collector.get`).

## Pièges connus

- Les images Docker `api` et `worker` **embarquent le code** : après une
  modification backend, `docker compose up -d --build api worker` (pas
  `restart`).
- Migrations Alembic : la colonne `tsv` et l'index `ix_document_tsv` sont créés
  en SQL brut et **exclus de l'autogénération** (filtre `include_name` dans
  `alembic/env.py`). Vérifiez toujours le contenu d'une migration autogénérée.
- L'OCR (Tesseract) tourne dans le worker et monopolise le CPU : mettez le
  conteneur en pause pendant les builds npm.

## Ajouter un collecteur

1. Créer `backend/app/ingestion/<source>.py` héritant de `Collector`
   (voir `assemblee.py` pour un exemple court, `wordpress.py` pour un site WP).
2. Déclarer la source dans `SEEDS` et la classe dans `COLLECTORS`
   (`ingestion/registry.py`).
3. Tester en réel : `python -m app.ingestion.run <slug>` — l'exécution est
   journalisée dans la table `run` (visible dans /admin).

## Ajouter un dossier thématique

Ajouter une entrée dans `frontend/src/views/DossiersView.vue` (titre,
description, étiquettes, lien). Pour un dossier interactif autonome, suivre le
modèle de `apps/plan-relance/` (build embarqué dans `frontend/public/`).

## Issues et PR

- Utilisez les gabarits d'issues : **bug**, **source cassée ou dépubliée**
  (précieux : les sites officiels changent souvent), **proposition de source**.
- Une PR = un sujet. Décrivez ce qui change et comment vous l'avez vérifié
  (l'interface se teste en réel : `docker compose up --build`).
- `pytest` doit passer ; pour le front, vérifiez les pages touchées au
  navigateur dans les deux thèmes (clair/sombre).

## Code de conduite

Projet citoyen, indépendant et non partisan. Les contributions à visée
partisane ou les données non sourcées ne sont pas acceptées.
