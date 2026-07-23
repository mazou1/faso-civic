"""Géocodage à la commune : nom de lieu extrait → localité du gazetteer.

Le gazetteer `localite` (GeoNames, cf. app/data/localites_bf.csv) porte régions,
provinces et communes avec coordonnées. On rapproche un nom de lieu brut d'une
localité : correspondance exacte sur la forme normalisée, sinon similarité
trigramme (pg_trgm). En cas d'ambiguïté (homonymes), la plus peuplée gagne.
"""

from __future__ import annotations

import re
import unicodedata

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Localite


def normaliser_lieu(nom: str | None) -> str:
    """Forme canonique pour le rapprochement : minuscules, sans accents, sans
    ponctuation, espaces réduits. Retire les mots génériques et les prépositions
    de tête (« commune de Manga » → « manga »)."""
    n = unicodedata.normalize("NFKD", nom or "")
    n = "".join(c for c in n if not unicodedata.combining(c))
    n = n.lower().replace("'", " ").replace("-", " ")
    n = re.sub(r"\b(commune|ville|village|province|region|departement|secteur)\b", " ", n)
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    # prépositions de tête laissées par le nettoyage (« de manga »)
    n = re.sub(r"^(?:de |du |des |d |la |le |les |a |au |aux )+", "", n)
    return n.strip()


def geocoder(db: Session, nom: str | None, seuil: float = 0.55) -> Localite | None:
    """Localité correspondant au nom donné, ou None. Exact d'abord (la plus
    peuplée en cas d'homonymes), puis similarité trigramme au-dessus du seuil."""
    cle = normaliser_lieu(nom)
    if not cle:
        return None

    exact = db.scalars(
        select(Localite)
        .where(Localite.nom_normalise == cle)
        .order_by(Localite.population.desc().nulls_last())
    ).first()
    if exact is not None:
        return exact

    # flou : opérateur trigramme `%` (adossé à l'index GIN), tri similarité
    # puis population. `.op("%")` évite les soucis d'échappement de text().
    sim = func.similarity(Localite.nom_normalise, cle).label("sim")
    ligne = db.execute(
        select(Localite, sim)
        .where(Localite.nom_normalise.op("%")(cle))
        .order_by(sim.desc(), Localite.population.desc().nulls_last())
        .limit(1)
    ).first()
    if ligne and ligne.sim is not None and ligne.sim >= seuil:
        return ligne[0]
    return None
