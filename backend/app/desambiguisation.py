"""Désambiguïsation des homonymes par matricule de la fonction publique.

Les comptes rendus citent le matricule après le nom (« Mamadou SERE,
Mle 39 652 W ») : c'est un identifiant fort. Deux étapes idempotentes :

- `extraire`  : pour chaque nomination validée, retrouve le nom dans le texte
                du CR source et relève le matricule qui le suit (regex, pas de
                LLM). Ambiguïtés (même nom, matricules différents dans le même
                CR) laissées vides.
- `eclater`   : pour chaque Personne dont les nominations portent plusieurs
                matricules distincts, crée une Personne par matricule
                supplémentaire et réaffecte les nominations. Les nominations
                sans matricule suivent leur structure si elle désigne un seul
                groupe, sinon restent sur la personne d'origine.

Relancer ensuite `python -m app.annuaire` (les mandats sont reconstruits).

Usage : python -m app.desambiguisation [extraire|eclater|tout]
"""

from __future__ import annotations

import logging
import re
import sys
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Document, Nomination, Personne

logger = logging.getLogger(__name__)

# correspondance 1:1 (les index restent alignés entre texte brut et texte plié)
_SANS_ACCENT = str.maketrans(
    "àâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ’",
    "aaaeeeeiioouuucAAAEEEEIIOOUUUC'",
)
MATRICULE = re.compile(r"M[Ll][Ee]\.?\s*([0-9][0-9 . ]{2,14}[A-Z]?)\b")


def _plier(s: str) -> str:
    return s.translate(_SANS_ACCENT).lower()


def _normaliser_matricule(brut: str) -> str:
    return re.sub(r"[ . ]", "", brut).upper()


def _matricule_apres_nom(texte_plie: str, texte: str, nom: str) -> str | None:
    """Matricule suivant une occurrence du nom complet ; None si absent ou ambigu."""
    motif = re.compile(r"\s+".join(re.escape(t) for t in _plier(nom).split()))
    trouves: set[str] = set()
    for m in motif.finditer(texte_plie):
        fenetre = texte[m.end() : m.end() + 60]
        mm = MATRICULE.search(fenetre)
        # le matricule doit suivre immédiatement (virgule/espace), pas une autre personne
        if mm and mm.start() <= 15:
            trouves.add(_normaliser_matricule(mm.group(1)))
    return trouves.pop() if len(trouves) == 1 else None


def extraire(db: Session) -> int:
    """Renseigne Nomination.matricule depuis les textes des CR (idempotent)."""
    nominations = db.scalars(
        select(Nomination).where(
            Nomination.statut_validation == "valide", Nomination.matricule.is_(None)
        )
    ).all()
    par_doc: dict[int, list[Nomination]] = defaultdict(list)
    for n in nominations:
        par_doc[n.document_id].append(n)

    total = 0
    for doc_id, noms in par_doc.items():
        texte = db.scalar(select(Document.texte_extrait).where(Document.id == doc_id))
        if not texte:
            continue
        texte_plie = _plier(texte)
        for n in noms:
            matricule = _matricule_apres_nom(texte_plie, texte, n.personne.nom_complet)
            if matricule:
                n.matricule = matricule
                total += 1
    db.commit()
    return total


def eclater(db: Session) -> tuple[int, int]:
    """Éclate les Personne dont les nominations portent des matricules distincts."""
    personnes = db.scalars(select(Personne)).all()
    crees = reaffectees = 0
    for p in personnes:
        noms = db.scalars(select(Nomination).where(Nomination.personne_id == p.id)).all()
        groupes: dict[str, list[Nomination]] = defaultdict(list)
        sans: list[Nomination] = []
        for n in noms:
            (groupes[n.matricule] if n.matricule else sans).append(n)

        if not groupes:
            continue
        if len(groupes) == 1:
            p.matricule = next(iter(groupes))  # enrichissement simple
            continue

        # le groupe le plus fourni garde la fiche existante
        ordre = sorted(groupes, key=lambda m: len(groupes[m]), reverse=True)
        p.matricule = ordre[0]
        fiches: dict[str, Personne] = {ordre[0]: p}
        for matricule in ordre[1:]:
            double = Personne(
                nom_complet=p.nom_complet,
                nom_normalise=p.nom_normalise,
                matricule=matricule,
                notes="Créée par désambiguïsation des homonymes (matricule).",
            )
            db.add(double)
            db.flush()
            fiches[matricule] = double
            crees += 1
            for n in groupes[matricule]:
                n.personne_id = double.id
                reaffectees += 1

        # sans matricule : suivre la structure si elle ne désigne qu'un groupe
        structures = {
            matricule: {n.structure_id for n in gr if n.structure_id}
            for matricule, gr in groupes.items()
        }
        for n in sans:
            if n.structure_id is None:
                continue
            cibles = [m for m, st in structures.items() if n.structure_id in st]
            if len(cibles) == 1 and cibles[0] != ordre[0]:
                n.personne_id = fiches[cibles[0]].id
                reaffectees += 1
    db.commit()
    return crees, reaffectees


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    commande = sys.argv[1] if len(sys.argv) > 1 else "tout"
    with SessionLocal() as db:
        if commande in ("extraire", "tout"):
            n = extraire(db)
            print(f"{n} matricule(s) extraits des comptes rendus.")
        if commande in ("eclater", "tout"):
            crees, reaffectees = eclater(db)
            print(
                f"{crees} fiche(s) créées par éclatement, {reaffectees} nomination(s) réaffectées. "
                "Relancer : python -m app.annuaire"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
