# Sources de données ouvertes temps réel / quasi temps réel pour une plateforme de veille sur le Burkina Faso

**État vérifié : juillet 2026** — Rapport issu d'une recherche approfondie multi-agents (5 axes, 24 sources lues, 117 affirmations extraites, 25 vérifiées de façon adversariale par tests en direct des API). ACLED et Human Rights Watch exclus à la demande.

---

## 1. Temps réel (latence < 1 h)

### GDELT DOC 2.0 — veille médias mondiale ✅ vérifié en direct
- **Endpoint** : `https://api.gdeltproject.org/api/v2/doc/doc?query="Burkina Faso"&mode=artlist&format=json`
- **Accès** : gratuit, sans clé ni inscription. Attention : rate-limiting agressif (HTTP 429) depuis des IP datacenter partagées — prévoir backoff et IP dédiée.
- **Latence** : index mis à jour ~15 min ; test live (2026-07-01) : HTTP 200 avec articles de juin 2026, dont burkina24.com (sourcecountry "Burkina Faso").
- **Profondeur** : contrairement à une croyance répandue (réfutée 0-3 par les vérificateurs), l'API ne se limite PAS aux 3 derniers mois — elle couvre tout l'archive depuis le **1er janvier 2017** via `startdatetime`/`enddatetime` (~9,5 ans). Le défaut `TIMESPAN` de 3 mois est modifiable.
- **Langues** : recherche translinguale sur 65 langues (presse francophone couverte) avec mots-clés anglais.
- **Formats** : JSON, CSV, RSS, JSONFeed.

> ⚠️ **L'API GDELT GEO 2.0 est morte.** Testée le 2026-07-01 : HTTP 404 sur toutes les variantes (deux chemins réseau indépendants), sans annonce publique. Ne pas l'inclure dans l'architecture. Pour la couche géolocalisée : fichiers bruts **GKG 2.0** publiés toutes les 15 minutes, ou GDELT sur BigQuery.

### Flux RSS des médias burkinabè ✅ vérifiés actifs (juin-juillet 2026)
| Média | Flux | Notes |
|---|---|---|
| leFaso.net | `https://lefaso.net/spip.php?page=backend` | RSS 2.0, 15 items, 10+ articles/jour vérifiés le 2026-07-01 (09:56–21:10), pas de paywall. **Poller plusieurs fois/jour** (le flux ne garde que ~15 items). |
| Sidwaya (quotidien d'État) | `sidwaya.info/feed` | Gratuit, sans inscription |
| Burkina24 | `burkina24.com/feed` | Un des plus gros médias en ligne du pays |
| AIB (agence de presse officielle) | `aib.media/feed` | |
| Le Pays | `lepays.bf/feed` | |

Latence de quelques minutes à quelques heures ; couverture directe des thèmes sécurité/terrorisme, politique, économie. C'est la brique locale qui complète GDELT (qui, lui, dépend de l'indexation des médias).

### Open-Meteo — météo ✅ vérifié en direct sur Ouagadougou
- **Endpoint** : `https://api.open-meteo.com/v1/forecast?latitude=12.37&longitude=-1.52&current=temperature_2m,precipitation,wind_speed_10m`
- **Accès** : gratuit, **sans clé ni inscription**, 10 000 appels/jour (usage non commercial). Licence CC BY 4.0, code AGPLv3.
- **Latence** : conditions actuelles au pas de 15 min ; modèles régionaux 1-2 km rafraîchis toutes les 1-3 h, globaux toutes les 6 h.
- **Bonus** : réanalyse ERA5 depuis 1940 pour la calibration historique, et **Flood API** (GloFAS v4 sans clé — voir §2).

### OpenSky Network — trafic aérien (avec réserves)
- **Endpoint** : `GET https://opensky-network.org/api/states/all?lamin=9.4&lomin=-5.5&lamax=15.1&lomax=2.4` (bbox Burkina Faso), JSON.
- **Changement d'accès récent** : l'authentification Basic n'est plus acceptée — **OAuth2 client credentials obligatoire** pour l'accès authentifié. Anonyme : 400 crédits/jour, résolution 10 s, pas d'historique. Compte gratuit : 4 000 crédits/jour, résolution 5 s, 1 h d'historique. Gratuit uniquement pour usage recherche/non commercial.
- **Limite majeure** : couverture ADS-B crowdsourcée **faible au Sahel** (peu de récepteurs au sol). Le complément satellitaire ADS-C (Alphasat) couvre l'Afrique mais reste parcellaire (~5 % de la flotte régionale équipée en 2024 ; le Burkina n'est pas dans le top 5 africain). À considérer comme couche d'appoint, pas comme source fiable.

### Overpass API (OpenStreetMap) — infrastructure
- **Endpoint** : `https://overpass-api.de/api/interpreter` (XML/JSON), miroirs sans limite : `maps.mail.ru/osm/tools/overpass/api/interpreter`, `overpass.private.coffee/api/interpreter`.
- **Accès** : gratuit, sans inscription ; étiquette ~10 000 requêtes et 1 Go/jour, identifier son app via User-Agent.
- **Latence** : quelques minutes derrière la base OSM (horodatage `osm_base` dans chaque réponse). Aucun changement restrictif signalé (doc mise à jour 2026-06-11).
- **Usage** : routes, ponts, hôpitaux, infrastructures — la couche de référence géographique de la plateforme.

---

## 2. Quasi temps réel (latence < 48 h)

### NASA FIRMS — feux actifs / anomalies thermiques ✅ vérifié en direct
- **Endpoint** : `/api/area/csv/[MAP_KEY]/[SOURCE]/[bbox ou "world"]/[1..5 jours]` sur `firms.modaps.eosdis.nasa.gov` ; existe aussi `/api/country/` avec code **BFA**. Sortie CSV.
- **Accès** : gratuit, **MAP_KEY obligatoire** (inscription email gratuite, exigence vérifiée activement en direct). Quota **5 000 transactions / 10 min** (une requête multi-jours compte plusieurs transactions ; augmentation possible sur demande).
- **Sources couvrant le Burkina** : MODIS_NRT, VIIRS_SNPP_NRT, VIIRS_NOAA20_NRT, VIIRS_NOAA21_NRT. Latence **~3 h** après passage satellite. (L'Ultra Real-Time <60 s existe mais **US/Canada uniquement** — comme LANDSAT_NRT.)
- Endpoint `/api/data_availability/` pour piloter automatiquement les fenêtres d'ingestion.

### ReliefWeb API v2 — rapports humanitaires ⚠️ conditions durcies
- **Endpoint** : `https://api.reliefweb.int/v2/reports` avec `filter[field]=primary_country.iso3&filter[value]=bfa` ; 9 types de contenus (reports, disasters, countries…). JSON, lecture seule, licence CC BY 4.0.
- **Changement récent confirmé (3-0)** : depuis le **1er novembre 2025**, `appname` **pré-approuvé obligatoire** — formulaire, revue par ReliefWeb, confirmation email. Sans lui : HTTP 403 (vérifié en direct). Gratuit, mais ce n'est plus "sans inscription".
- **Quotas** : max 1 000 entrées/appel et **1 000 appels/jour** (négociable via feedback@reliefweb.int).
- **v1 décommissionnée** (arrêt complet fin T1 2026) — n'utiliser que la v2.
- **Latence** : publication continue, typiquement quelques heures après les rapports sources.

### Copernicus Data Space Ecosystem (CDSE) — imagerie Sentinel
- L'ancien **SciHub a fermé fin octobre 2023** — toute doc/tutoriel pointant dessus est obsolète.
- **Accès** : gratuit avec inscription ; APIs **STAC**, **OData**, **openEO** (traitement côté serveur), **S3** et **Sentinel Hub** (traitement temps réel sans téléchargement massif). Quotas horaires/mensuels de volume et bande passante à intégrer au design.
- Sentinel-1/2/3/5P couvrent le Burkina Faso ; latence de mise à disposition selon produit (heures).

### GFM / GloFAS — inondations (Copernicus EMS) ✅ WMS testé en direct
- **Global Flood Monitoring** : cartographie automatique des inondations à partir de **chaque passage Sentinel-1 SAR** (bande C, tous temps — crucial pendant la saison des pluies nuageuse), cartes livrées **~5 h après acquisition**, 10×10 m, consensus de 3 algorithmes indépendants. 11 produits (étendue d'inondation, population affectée, etc.).
- **Accès gratuit** via : WMS OGC avec requêtes temporelles (`https://geoserver.gfm.eodc.eu/geoserver/gfm/ows` — HTTP 200 vérifié), **notifications push** pour événements détectés, REST-APIs par produit, portail `portal.gfm.eodc.eu`.
- La couche "Sentinel-1 Schedule" donne la prochaine acquisition prévue par zone — utile pour estimer la latence de revisite sur le Burkina.
- GloFAS (prévision de crues) : temps réel via FTP dédié sur demande (NetCDF), ou **plus simple : Open-Meteo Flood API** (GloFAS v4, REST, sans clé, débits par lat/lon, réanalyse 1984→présent + 7 mois de prévision).

### Google Flood Forecasting API (Flood Hub)
- **Burkina Faso explicitement couvert** (liste officielle, ~150 pays, 240 000+ emplacements de bassins).
- **Endpoints** : `floodforecasting.googleapis.com` — `GET /v1/gauges:queryGaugeForecasts`, `GET /v1/floodStatus:queryLatestFloodStatusByGaugeIds`, `POST /v1/floodStatus:searchLatestFloodStatusByArea`, `POST /v1/gauges:searchGaugesByArea` (host vérifié actif en direct).
- **Accès** : gratuit, licence CC BY 4.0, **mais liste d'attente** (formulaire) + projet Google Cloud + clé API. Prévisions à 7 jours mises à jour quotidiennement, statut d'inondation plusieurs fois par jour. Doc activement maintenue (2026-01-12). → S'inscrire tôt ; utiliser Open-Meteo Flood API en attendant.

---

## 3. Structurel (latence > 48 h — contexte, pas temps réel)

### HDX / HDX HAPI (OCHA)
- **HAPI** : `https://hapi.humdata.org/api/v2/` — indicateurs standardisés multi-sources. Gratuit, "app identifier" = simple base64 nom+email via l'endpoint `encode_identifier` (sans validation — vérifié fonctionnel en direct). **Burkina Faso couvert** (`location_code=BFA`) : sécurité alimentaire, déplacements, population, **prix de marchés WFP au niveau admin2** (vérifié : marché Namouno, niébé en XOF), endpoint pluie `climate/hazards-rainfall`. Encore en **bêta** — endpoints susceptibles de changer.
- **API CKAN classique** : gratuite, sans quota strict, tous les datasets `data.humdata.org/group/bfa` ; lib `hdx-python-api`.
- ⚠️ **Contexte 2025-2026** : crise de financement humanitaire (retour au niveau 2016, retrait US ~40 % du financement mondial, USAID démantelée). OCHA estime 74 % des données de crise à jour début 2025 ; les données PDI/sécurité alimentaire sont classées **au plus haut risque de discontinuité**. Concevoir l'ingestion avec détection de fraîcheur (champ `last_modified`).

### WFP VAM — prix alimentaires
- Dataset HDX `wfp-food-prices-for-burkina-faso` : CSV direct, CC BY-IGO, ~45 000 lignes depuis 1992, géolocalisé au niveau marché, balisé HXL. Source : Afrique Verte via FAO GIEWS/SIM-SONAGESS.
- **Latence réelle : mensuelle** (dernière modif 2026-05-24 pour des données jusqu'au 2026-04-15). Pipeline actif mais **pas quasi temps réel** — à classer en couche contextuelle. L'ancienne API VAM publique a été restreinte au profit de HDX/DataViz.

### IOM DTM — déplacements internes ⚠️ limite majeure pour le Burkina
- **API v3** en production depuis août 2025 (`dtm-apim-portal.iom.int`) — inscription gratuite + subscription key ; libs Python (`dtmapi`), R, JS. Chiffres PDI non sensibles, admin 0-2. v1/v2 non maintenues.
- **MAIS** : le pipeline HDX pour le Burkina tourne chaque semaine (dernière exécution 2026-06-29)… sur des données dont la plage s'arrête au **30 août 2019**. L'API ne fournit pas de chiffres de déplacement récents pour ce pays. Vérifier la Data Coverage Matrix ; chercher les chiffres récents via le cluster CONASUR/OCHA sur HDX.
- **Licence restrictive** : non commercial, pas d'œuvres dérivées ni de redistribution — problématique pour une plateforme qui republie.

---

## 4. Sources fermées ou à exclure (état 2026)

| Source | Statut | Détail |
|---|---|---|
| **GDELT GEO 2.0 API** | ❌ Morte | HTTP 404 vérifié le 2026-07-01, sans annonce. Remplacer par DOC 2.0 + fichiers GKG 15 min. |
| **X / Twitter API** | ❌ Paywall | Plus aucun accès gratuit depuis 2023 ; Basic 200 $/mois (+1 $/compte connecté), enterprise ~42 000 $/mois. |
| **ProMED** | ❌ Effondrée | Flux RSS et Twitter coupés définitivement (juin 2023), archives limitées à 30 jours, abonnement payant, modérateurs en grève. Pour la santé : OMS + HDX à la place. |
| **Copernicus SciHub** | ❌ Fermé | Fin octobre 2023 → migrer vers CDSE. |
| **ReliefWeb API v1** | ❌ Décommissionnée | Arrêt complet fin T1 2026 → v2 uniquement. |
| **Telegram** | ⚠️ Utilisable avec prudence | Bot API / MTProto fonctionnels, mais contexte de conformité durci post-arrestation Durov (partage accru de données avec les autorités, risque de suppression de canaux). |

---

## 5. Architecture d'ingestion recommandée

**Cadences de polling par source :**

| Cadence | Sources |
|---|---|
| 15 min | GDELT DOC 2.0, flux RSS médias burkinabè, fichiers GKG |
| 1 h | Open-Meteo (courant), OpenSky (si retenu) |
| 3-6 h | FIRMS (latence intrinsèque ~3 h), Open-Meteo Flood API |
| Quotidien | ReliefWeb (rester sous 1 000 appels/jour), Flood Hub, GFM (ou mieux : **notifications push GFM**), CDSE catalogue STAC |
| Hebdo | HDX HAPI, Overpass (deltas infra), DTM (pipeline) |
| Mensuel | WFP prix |

**Inscriptions à lancer dès maintenant** (délais d'approbation) :
1. ReliefWeb : demande d'appname pré-approuvé (formulaire + revue)
2. Google Flood Hub : liste d'attente
3. NASA FIRMS : MAP_KEY (immédiat)
4. CDSE Copernicus : compte gratuit
5. OpenSky : client OAuth2
6. DTM Developer Portal : compte + clé

**Principes :**
- **Push avant pull** quand disponible : notifications GFM pour les inondations.
- **Gestion des quotas centralisée** : ReliefWeb 1 000/jour, FIRMS 5 000/10 min, Open-Meteo 10 000/jour, Overpass étiquette 10 000/jour — un rate-limiter par source dans le scheduler.
- **Détection de fraîcheur** : chaque ingestion doit comparer `last_modified`/`dataset_date` et alerter si une source humanitaire décroche (risque réel 2025-2026).
- **Licences** : CC BY 4.0 (ReliefWeb, Open-Meteo, Flood Hub), CC BY-IGO (WFP) → attribution obligatoire ; DTM → ne pas redistribuer les données brutes.
- **Ne pas bâtir sur** : X/Twitter, ProMED, GDELT GEO, DTM pour les chiffres récents de déplacement au Burkina.

---

## 6. Tableau récapitulatif

| Source | Domaine | Latence | Clé/inscription | Quota | Couverture BF | Vérifié live |
|---|---|---|---|---|---|---|
| GDELT DOC 2.0 | Médias/événements | ~15 min | Non | 429 sur IP partagées | Oui (65 langues) | ✅ 200 OK |
| RSS médias BF | Médias locaux | Minutes-heures | Non | — | Native | ✅ actifs |
| Open-Meteo | Météo | 15 min-6 h | Non | 10 000/j | Oui (testé Ouaga) | ✅ |
| Overpass/OSM | Infrastructure | Minutes | Non | ~10 000/j étiquette | Oui | ✅ |
| OpenSky | Aérien | Secondes | OAuth2 | 400-8 000 crédits/j | **Faible (ADS-B Sahel)** | ✅ |
| FIRMS | Feux | ~3 h | MAP_KEY gratuite | 5 000/10 min | Oui (VIIRS/MODIS NRT) | ✅ |
| ReliefWeb v2 | Humanitaire | Heures | appname pré-approuvé (11/2025) | 1 000/j | Oui (filtre bfa) | ✅ 403 sans appname |
| CDSE Sentinel | Satellite | Heures | Compte gratuit | Volume/bande passante | Oui | — |
| GFM/GloFAS | Inondations | ~5 h post-acquisition | Non (WMS) | — | Oui (mondial) | ✅ WMS 200 |
| Google Flood Hub | Prévision crues | Quotidien+ | Liste d'attente + GCP | Non précisé | **Oui (liste officielle)** | ✅ host actif |
| HDX HAPI | Humanitaire | Jours-mois | App identifier (auto) | — | Oui (BFA, 249 loc.) | ✅ bêta |
| WFP prix | Sécurité alim. | **Mensuel** | Non (CKAN) | — | Oui (niveau marché) | ✅ |
| IOM DTM v3 | Déplacements | Rounds (semaines+) | Portail + clé | — | ⚠️ **Données figées à 2019** | ✅ |

---

*Rapport généré le 2026-07-03 à partir du workflow deep-research du 2026-07-01 (106 agents, vérifications adversariales 3 votes par affirmation, tests en direct des endpoints).*
