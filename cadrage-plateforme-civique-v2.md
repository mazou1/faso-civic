# Cadrage v2 — Plateforme civique Burkina Faso

**Version 2 du 9 juillet 2026.** Ce document remplace le périmètre « veille temps réel » (voir `rapport-sources-donnees-temps-reel.md`, conservé pour référence : ses sections RSS médias, Overpass/OSM et HDX restent utilisées ici).

---

## 1. Vision et positionnement

Une plateforme citoyenne **indépendante** qui agrège, structure et recroise l'information publique burkinabè — journal officiel, textes de loi, comptes rendus du Conseil des ministres, communiqués, budget, marchés publics, décisions de justice, rapports de contrôle — et la restitue sur un site interactif fiable avec cartes et graphiques.

**Modèle d'inspiration** : [vie-publique.sn](https://www.vie-publique.sn) (Code for Senegal, GPL-3.0, [dépôt GitHub](https://github.com/Code-for-Senegal/vie-publique.sn)). On reprend leur positionnement éditorial, pas leur stack (Nuxt 4 + Directus, curation majoritairement manuelle).

**Différenciateurs visés :**
1. **Ingestion automatisée** (scraping + RSS + parsing PDF) là où le modèle sénégalais saisit à la main.
2. **Recoupement** : nominations extraites des CR du Conseil des ministres → annuaire de l'État avec historique ; texte du JO ↔ version consolidée Légiburkina ; attributions de marchés ↔ lignes budgétaires.
3. **Traçabilité systématique** : chaque donnée affichée porte un lien vers le document source officiel, sa date de publication et sa date de collecte. C'est à la fois l'argument de fiabilité et la protection juridique (on ne publie que du public, sourcé).

**Principe de neutralité** : aucune analyse d'opinion, aucune donnée conflictuelle (ACLED, HRW et assimilés restent exclus). Des faits publics, présentés tels quels.

---

## 2. Périmètre fonctionnel

### V1 (cœur)
| Rubrique | Contenu | Source primaire |
|---|---|---|
| **Conseil des ministres** | Comptes rendus hebdomadaires, indexés et datés | gouvernement.gov.bf / sig.gov.bf / presidencedufaso.bf |
| **Nominations** | Extraites des CR (personne, poste, structure, date, référence) | dérivé des CR |
| **Journal officiel & textes** | Décrets, arrêtés, lois — métadonnées + lien (texte intégral si accessible) | jobf.gov.bf, legiburkina.gov.bf |
| **Gouvernement** | Composition actuelle + historique des remaniements | dérivé des nominations + pages officielles |
| **Actualités officielles** | Communiqués et déclarations agrégés | sig.gov.bf, presidencedufaso.bf, RSS AIB/Sidwaya |
| **Budget** | Tableau de bord : loi de finances par ministère/secteur, évolution pluriannuelle | dgb.gov.bf, finances.gov.bf |

### V2 (extensions)
| Rubrique | Contenu | Source primaire |
|---|---|---|
| **Marchés publics** | Appels d'offres et attributions (montant, attributaire, autorité contractante) | dgcmef.gov.bf |
| **Justice & contrôle** | Décisions du Conseil constitutionnel ; rapports ASCE-LC ; rapports Cour des comptes (site introuvable — relais via médias/ASCE-LC à creuser) | conseil-constitutionnel.gov.bf, asce-lc.bf |
| **Parlement (ALT)** | Lois votées, ordre du jour | assembleenationale.bf |
| **Carte de l'État** | Découpage 13 régions / 45 provinces / 351 communes, services publics géolocalisés | OSM/Overpass + INSD |
| **Données pays** | Indicateurs INSD (population, éducation, santé, prix) | insd.bf, data.gov.bf, HDX |

### Hors périmètre
Veille sécuritaire temps réel, feux/inondations/imagerie satellite (FIRMS, Copernicus, GDELT…), réseaux sociaux, données conflictuelles. Réintégrables plus tard comme couche « contexte » optionnelle si besoin.

---

## 3. Inventaire des sources (vérifiées en direct le 2026-07-09, toutes HTTP 200)

| Source | URL | Format attendu | Cadence de collecte | Notes |
|---|---|---|---|---|
| Conseil des ministres | gouvernement.gov.bf | HTML (articles) | Hebdo (mercredi soir + rattrapage J+1) | Cœur du recoupement nominations |
| SIG (communiqués) | sig.gov.bf | HTML | 2×/jour | |
| Présidence | presidencedufaso.bf | HTML | Quotidien | |
| Légiburkina | legiburkina.gov.bf | HTML + PDF | Quotidien | Plateforme SGG-CM lancée nov. 2024 ; ⚠️ l'ancien domaine legiburkina.**bf** est mort |
| Journal officiel | jobf.gov.bf | PDF (⚠️ modèle achat/abonnement à vérifier) | Hebdo | Coût d'abonnement = éventuel poste budgétaire ; métadonnées probablement libres |
| Assemblée (ALT) | assembleenationale.bf | HTML + PDF | Hebdo | |
| Budget | dgb.gov.bf, finances.gov.bf | PDF (lois de finances, budget citoyen), parfois XLS | Trimestriel + à chaque loi de finances | Saisie/parsing initial = gros chantier ponctuel |
| Marchés publics | dgcmef.gov.bf | HTML + PDF (revue des marchés) | Hebdo | V2 |
| Conseil constitutionnel | conseil-constitutionnel.gov.bf | PDF (décisions) | Hebdo | V2 |
| ASCE-LC | asce-lc.bf | PDF (rapports) | Mensuel | V2 ; ⚠️ HTTPS obligatoire, HTTP ne répond pas |
| INSD | insd.bf | PDF/XLS | Mensuel | Indicateurs pour graphiques |
| Open data national | data.gov.bf | CSV/API CKAN à confirmer | Mensuel | Fraîcheur à auditer |
| RSS médias (AIB, Sidwaya, leFaso, Burkina24, Le Pays) | cf. rapport v1 §1 | RSS 2.0 | 30 min | Contexte/actualités ; flux ~15 items, poller souvent |
| OSM Overpass | overpass-api.de | JSON | Hebdo (deltas) | Fond de carte + services publics ; étiquette ~10 000 req/j |
| HDX HAPI | hapi.humdata.org | JSON | Hebdo | Indicateurs complémentaires (BFA), bêta |

**Point mort identifié** : la **Cour des comptes** n'a pas de site trouvable en ligne (courdescomptes.gov.bf, cour-comptes.bf : DNS morts). Ses rapports publics devront être récupérés via relais (ASCE-LC, médias, dépôt manuel).

---

## 4. Modèle de données (noyau)

Tout gravite autour du **document source** ; les entités structurées y sont rattachées.

```
source            (id, nom, url_base, type, cadence, licence)
document          (id, source_id, url, url_archive, titre, type_doc,        -- cr_conseil, decret, arrete, loi,
                   date_publication, date_collecte, hash_contenu,           -- communique, decision, rapport, marche…
                   fichier_pdf, texte_extrait, statut_extraction, tsv)      -- tsv = tsvector recherche plein texte

personne          (id, nom_complet, nom_normalise, notes)
structure         (id, nom, sigle, type, parent_id)                         -- ministère, direction, société d'État…
nomination        (id, document_id, personne_id, structure_id, poste,
                   date_effet, type)                                        -- nomination / fin de fonction
mandat            (id, personne_id, structure_id, poste, date_debut,
                   date_fin, nomination_debut_id, nomination_fin_id)        -- dérivé : l'annuaire et son historique

texte_juridique   (id, document_id, numero, type, date_signature,
                   ministere_porteur, url_legiburkina, url_jo)
ligne_budget      (id, annee, ministere_id, programme, nature,
                   montant_vote, montant_revise, document_id)
marche_public     (id, document_id, autorite_id, objet, attributaire,
                   montant, date_attribution)                                -- V2
decision_justice  (id, document_id, juridiction, numero, date, objet)        -- V2

division_admin    (id, nom, niveau, parent_id, geom)                         -- PostGIS : région/province/commune
lieu_service      (id, nom, type, division_id, geom, source_osm_id)          -- écoles, hôpitaux, mairies… (OSM)
```

Règles :
- `document.hash_contenu` → détection de modification/republication silencieuse ; on **versionne**, on n'écrase jamais.
- Toute entité extraite garde son `document_id` → le « voir la source » de l'UI est une jointure, pas une option.
- `personne.nom_normalise` (translittération/casse) pour rapprocher les mentions d'une même personne entre CR — avec table de fusion manuelle pour les homonymes.

---

## 5. Pipeline d'ingestion

Quatre étages, chacun rejouable indépendamment :

1. **Collecte** — scrapers par source (HTTP + parsing HTML) et lecteurs RSS. Sortie : `document` brut + PDF archivé sur disque. Politesse : 1 req/s max par domaine, User-Agent identifiant le projet, cache conditionnel (ETag/Last-Modified).
2. **Extraction** — PDF → texte (`pdfplumber`, fallback OCR `tesseract` fra pour les scans, fréquents sur les sites .gov.bf). Sortie : `texte_extrait` + `statut_extraction` (ok / ocr / échec → file de revue).
3. **Structuration** — extraction d'entités depuis le texte :
   - règles/regex pour le balisage stable (numéros de décrets, dates, montants) ;
   - **LLM (API Claude) pour les nominations et le semi-structuré** : les CR du Conseil des ministres ont un format prose ; un prompt d'extraction vers JSON validé par schéma Pydantic est bien plus robuste que des regex. Coût marginal (1 CR/semaine).
   - Toute extraction automatique porte un `score_confiance` ; sous un seuil → **file de validation humaine** avant publication.
4. **Publication** — les entités validées deviennent visibles côté API/site ; recalcul des vues dérivées (annuaire `mandat`, agrégats budget).

**Ordonnancement** : APScheduler dans un process dédié (pas de Celery/Redis en V1 — les volumes sont faibles : quelques dizaines de documents/jour). Journal d'exécution en base + alerte si une source ne produit rien pendant N × sa cadence (détection de panne ou de changement de gabarit HTML — le risque n°1 de ce projet).

---

## 6. Stack technique

Choix directeur (décision utilisateur) : **stack légère Python / FastAPI / PostgreSQL**, complétée comme suit.

### Backend
| Besoin | Choix | Pourquoi |
|---|---|---|
| API | **FastAPI** + Pydantic v2 | Décision de base ; OpenAPI gratuit → l'API publique documentée est un livrable en soi (esprit open data) |
| ORM / migrations | SQLAlchemy 2 + Alembic | Standard, versionnement du schéma indispensable (modèle évolutif) |
| Base | **PostgreSQL 16** + **PostGIS** + `pg_trgm` | PostGIS pour les cartes ; recherche plein texte via `tsvector` (config `french`) — **pas d'Elasticsearch**, Postgres suffit à cette échelle |
| Scraping | `httpx` + `selectolax` (ou BeautifulSoup), `feedparser` | Léger ; Playwright seulement si un site s'avère full-JS (aucun repéré pour l'instant) |
| PDF | `pdfplumber` + `pytesseract` (fallback OCR) | Les .gov.bf publient beaucoup de scans |
| Extraction LLM | SDK `anthropic`, sorties JSON validées Pydantic | Étage 3 du pipeline, volumes faibles |
| Scheduler | **APScheduler** (process worker dédié) | Évite Celery/Redis/RabbitMQ — rien ici n'exige une file distribuée |
| Admin / validation | **SQLAdmin** (ou Starlette-Admin) monté sur l'app FastAPI | Remplace Directus : CRUD + file de validation des extractions, zéro service supplémentaire |
| Stockage fichiers | Disque local (volume Docker), interface type S3 si migration ultérieure | Léger d'abord |

### Frontend
| Besoin | Choix | Pourquoi |
|---|---|---|
| Framework | **Vue 3 + Vite** (SPA statique servie par nginx) | Léger, et même écosystème que vie-publique.sn → leurs composants/écrans restent une référence directe ; pas de SSR Nuxt à opérer |
| Cartes | **MapLibre GL JS** + tuiles OSM + GeoJSON PostGIS | Open source, pas de clé API |
| Graphiques | **ECharts** | Budget treemaps, séries temporelles, sans licence |
| SEO (à traiter, une SPA y est faible) | pré-rendu des pages de contenu ou passage ultérieur à Nuxt si le besoin le justifie | Le contenu civique vit beaucoup du référencement — point de vigilance assumé |

### Infra
- **Docker Compose** : `api`, `worker` (scrapers + scheduler), `db` (Postgres/PostGIS), `nginx` (statique + reverse proxy). Un seul VPS suffit largement en V1.
- Sauvegardes : `pg_dump` quotidien + copie des PDF (le corpus de documents archivés **est** l'actif du projet — certains disparaissent des sites officiels).
- Licence du code : GPL-3.0 (cohérent avec l'inspiration et l'esprit du projet) — à confirmer.

---

## 7. Cartes et graphiques (V1)

- **Tableau de bord budget** : dépenses/recettes par ministère (treemap), évolution pluriannuelle, part par secteur.
- **Annuaire de l'État** : organigramme navigable ministères → structures, fiche personne avec historique des postes, frise des remaniements.
- **Activité gouvernementale** : volume de décrets/nominations par mois, nuage des structures les plus concernées.
- **Carte administrative** : régions/provinces/communes (choropleth population INSD), services publics OSM (écoles, santé, mairies) — V1 simple, enrichie en V2.

---

## 8. Fiabilité et principes éditoriaux

1. Chaque page affiche : source officielle (lien), date de publication, date de collecte.
2. Ne jamais corriger silencieusement un document officiel ; les erreurs manifestes sont signalées, pas réécrites.
3. Extraction automatique ≠ publication automatique : seuil de confiance + revue humaine sur les entités sensibles (nominations, montants).
4. Archivage : conserver le PDF/HTML original horodaté (les sites officiels dépublient).
5. Indépendance affichée : mentions légales claires, pas d'affiliation, pas de données conflictuelles.
6. API publique en lecture : la plateforme redistribue ce qu'elle structure.

---

## 9. Risques

| Risque | Impact | Mitigation |
|---|---|---|
| Changement de gabarit HTML des sites .gov.bf | Rupture silencieuse d'ingestion | Alerte « source muette », tests de non-régression par scraper, parsing défensif |
| PDF scannés de mauvaise qualité | Extraction dégradée | OCR + file de revue humaine ; publier le PDF même sans texte |
| JO payant (jobf.gov.bf) | Trou dans le corpus | Vérifier le coût ; Légiburkina couvre les textes gratuitement ; métadonnées JO probablement libres |
| Cour des comptes sans site | Rubrique contrôle incomplète | Collecte indirecte (ASCE-LC, médias), dépôt manuel |
| Contexte politique (transition) | Pression / blocage | Neutralité stricte, uniquement du public sourcé, hébergement hors du pays, code open source |
| Homonymie des personnes | Annuaire faux | Fusion manuelle assistée, jamais automatique seule |

---

## 10. Feuille de route

- **Phase 0 — Socle (1-2 sem.)** : repo, Docker Compose, schéma Postgres/Alembic, squelette FastAPI + SQLAdmin.
- **Phase 1 — Première chaîne complète (2-3 sem.)** : scraper Conseil des ministres → extraction nominations (LLM + validation) → annuaire + pages CR sur le site. *Une seule rubrique, mais de bout en bout — c'est la preuve du concept du recoupement.*
- **Phase 2 — Corpus (3-4 sem.)** : Légiburkina, SIG/Présidence, RSS médias ; recherche plein texte ; pages documents.
- **Phase 3 — Visualisations (2-3 sem.)** : tableau de bord budget (saisie/parsing lois de finances), carte administrative MapLibre.
- **Phase 4 — V2** : marchés publics, justice/contrôle, ALT, API publique documentée, app mobile éventuelle.

---

*Sources burkinabè vérifiées en direct (HTTP 200) le 2026-07-09. Inspiration : vie-publique.sn — Code for Senegal, GPL-3.0.*
