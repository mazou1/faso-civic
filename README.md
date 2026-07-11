# FasoCivic — l'information publique du Burkina Faso

[![Licence: GPL-3.0](https://img.shields.io/badge/licence-GPL--3.0-009e49)](LICENSE)
![Python 3.12](https://img.shields.io/badge/python-3.12-15a35b)
![Vue 3](https://img.shields.io/badge/vue-3-b3841a)
![FastAPI](https://img.shields.io/badge/fastapi-0.11x-15a35b)

Plateforme citoyenne indépendante qui **collecte, archive, structure et restitue
l'information publique burkinabè** : conseils des ministres, nominations, lois et
décrets, budget de l'État, composition du gouvernement et de l'Assemblée.
Chaque donnée affichée est reliée à son document source officiel.

Inspirée de [vie-publique.sn](https://www.vie-publique.sn) (Code for Senegal).

![Tableau de bord FasoCivic](docs/captures/accueil.png)

## Principes

1. **Sources officielles uniquement** — sites gouvernementaux (`.gov.bf`),
   Assemblée, Présidence, Légiburkina, et médias publics pour le fil d'actualités.
2. **Chaque chiffre est sourcé** — toute décision, nomination ou montant renvoie
   au compte rendu ou au texte officiel dont il est extrait.
3. **Rien n'est publié sans validation humaine** — l'extraction automatique
   (LLM) produit des entités `a_valider` ; seules les entités validées dans le
   back-office sortent sur l'API et le site.
4. **Le corpus est archivé en propre** — les sites officiels dépublient ;
   chaque document collecté (HTML, PDF) est conservé tel quel avant traitement.

## Ce que couvre la plateforme

| Section | Contenu |
|---|---|
| **Conseil des ministres** | 145 comptes rendus structurés (2022→) : résumé des décisions, texte intégral, PDF officiel |
| **Décisions** | 1 299 décisions validées, filtrables par ministère et nature |
| **Annuaire de l'État** | 8 107 mandats reconstitués, 8 157 nominations, fiches personnalités **désambiguïsées par matricule** (6 188 personnes) |
| **Gouvernement** | Composition officielle avec portraits (Présidence du Faso), suivie à chaque remaniement |
| **Assemblée** | 71 députés synchronisés depuis an.bf, président de l'ALT, lois votées |
| **Lois & décrets** | 4 900 textes juridiques (Légiburkina) avec PDF archivés ; ~1 500 déjà en texte intégral (OCR en cours sur le reste) |
| **Finances** | Budget de l'État par exercice, répartition des recettes/dépenses, allocations sectorielles, 428 engagements chiffrés du Conseil des ministres |
| **Documents** | Bibliothèque des 5 363 documents archivés, facettes par type et source |
| **Recherche** | Plein texte français sur tout le corpus, extraits surlignés |
| **Dossiers** | Grands sujets (dont le [Plan de relance PND 2026-2030](apps/plan-relance/)) |

<table>
  <tr>
    <td><img src="docs/captures/conseils.png" alt="Conseils des ministres"></td>
    <td><img src="docs/captures/finances.png" alt="Finances publiques"></td>
    <td><img src="docs/captures/gouvernement.png" alt="Gouvernement"></td>
  </tr>
</table>

## Architecture

```
   collecte (APScheduler)          structuration              publication
┌──────────────────────┐   ┌───────────────────────────┐   ┌──────────────────┐
│ collecteurs httpx     │   │ extraction LLM             │   │ API FastAPI      │
│ RSS · WordPress ·     │──▶│ (décisions, nominations,   │──▶│ /api/…           │
│ Légiburkina · an.bf … │   │ engagements) + OCR + regex │   │                  │
│        │              │   │ (matricules)               │   │ SPA Vue 3        │
│        ▼              │   │        │                   │   │ (ECharts, nginx) │
│ archivage data/       │   │        ▼                   │   └──────────────────┘
│ (PDF/HTML bruts)      │   │ VALIDATION HUMAINE         │
└──────────────────────┘   │ (back-office SQLAdmin)     │
                            └───────────────────────────┘
```

```
backend/
  app/
    api/            # routes publiques (conseils, annuaire, finances, recherche…)
    ingestion/      # collecteurs + registre + scheduler (worker)
    extraction/     # LLM (Mistral/Claude), PDF → texte, OCR Tesseract
    admin.py        # back-office SQLAdmin (validation)
    annuaire.py     # consolidation nominations → mandats
    desambiguisation.py  # homonymes : matricules extraits des CR
    fusion.py       # dédoublonnage des structures
  alembic/          # migrations
frontend/           # SPA Vue 3 + Vite, servie par nginx (proxy /api)
apps/plan-relance/  # dossier interactif PND 2026-2030 (React, servi sous /plan-relance/)
docs/               # cadrage, rapports, captures d'écran
data/               # archives brutes — hors git, à sauvegarder
```

## Sources collectées

| Source | Type | Cadence |
|---|---|---|
| gouvernement.gov.bf | Comptes rendus du Conseil des ministres | jeudi + rattrapages |
| legiburkina.gov.bf | Lois, décrets, arrêtés (+ PDF) | quotidien |
| assembleenationale.bf | Députés, président de l'ALT | quotidien |
| presidencedufaso.bf | Communiqués (RSS), composition du gouvernement | quotidien |
| finances.gov.bf | Veille du Budget citoyen | quotidien |
| lefaso.net, sidwaya.info, aib.media, burkina24.com, lepays.bf | Actualités (RSS) | 30 min |

## Démarrage rapide (Docker)

```bash
cp .env.example .env        # ajuster mots de passe et clé LLM
docker compose up --build
```

- Site : http://localhost:8090
- API + doc OpenAPI : http://localhost:8001/docs (ou /api/docs via le site)
- Back-office : http://localhost:8001/admin
- Le worker collecte selon les cadences ci-dessus.

> ⚠️ Les images `api` et `worker` embarquent le code : après une modification
> backend, `docker compose up -d --build api worker` (un simple `restart` ne
> recharge rien).

## Développement local

```bash
# Backend
docker compose up -d db                      # Postgres/PostGIS sur localhost:5434
cd backend
uv venv && uv pip install -e ".[dev]"
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload      # API sur :8000
.venv/bin/pytest

# Frontend
cd frontend && npm install && npm run dev    # Vite proxy /api → :8000

# Dossier Plan de relance (après modification de apps/plan-relance/src)
cd apps/plan-relance && npm install && npm run build   # sortie dans frontend/public/
```

## Cycle de vie des données

```bash
python -m app.ingestion.run all           # collecte manuelle (sinon : worker)
python -m app.extraction.run 5            # structuration LLM des 5 prochains CR
# → valider dans /admin (ou : python -m app.validation 0.9)
python -m app.desambiguisation           # matricules + éclatement des homonymes
python -m app.annuaire                    # reconsolide les mandats
python -m app.fusion proposer 0.75        # doublons de structures → CSV à relire
python -m app.extraction.ocr_textes 500   # OCR des textes scannés (worker, Tesseract)
```

L'extraction LLM utilise **Mistral** par défaut (`FASO_LLM_PROVIDER=mistral`,
tier gratuit) avec bascule possible vers l'API Claude.

## Méthodologie et limites

- Les entités extraites automatiquement portent un score de confiance et ne
  sont **jamais publiées sans validation** dans le back-office.
- Les homonymes de l'annuaire sont distingués par le **matricule de la fonction
  publique** cité dans les comptes rendus (couvre ~91 % des nominations) ; les
  fiches concernées affichent une note de méthode.
- Légiburkina publie ~96 % de scans : la recherche couvre référence et
  description pour tout le corpus, le texte intégral progresse avec l'OCR.
- Les traductions des CR en langues nationales (mooré, fulfuldé, dioula,
  gulimancema) sont archivées mais exclues de l'extraction.
- Détail complet : page « À propos & méthodologie » du site, et
  [`docs/cadrage-plateforme-civique-v2.md`](docs/cadrage-plateforme-civique-v2.md).

## API ouverte

Toutes les données validées sont servies par une API documentée (OpenAPI) :

```bash
curl 'http://localhost:8090/api/conseils?par_page=5'
curl 'http://localhost:8090/api/recherche?q=barrage'
curl 'http://localhost:8090/api/finances/stats'
```

## Contribuer

Les contributions sont bienvenues — collecteurs de nouvelles sources, données
budgétaires, corrections, traductions. Lire [`CONTRIBUTING.md`](CONTRIBUTING.md),
et ouvrir une issue avec les gabarits fournis (bug, source dépubliée,
proposition de source).

## Licence et crédits

Code sous licence [GPL-3.0](LICENSE). Les données restituées proviennent de
documents publics officiels burkinabè, cités et liés partout où elles
apparaissent. Merci à [Code for Senegal](https://github.com/Code-for-Senegal)
dont [vie-publique.sn](https://www.vie-publique.sn) a inspiré ce projet.
