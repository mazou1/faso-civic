"""Consolidation de l'annuaire : nominations validées → mandats.

Les mandats sont une vue dérivée : on les reconstruit entièrement à chaque
consolidation (idempotent, pas de logique incrémentale fragile). Seules les
nominations avec statut_validation='valide' comptent.

Règles v1 (simples, à raffiner) :
- une nomination ouvre un mandat (personne, poste, structure, date_debut) ;
- une fin_fonction ferme le mandat ouvert le plus récent de la même personne
  (même structure si renseignée) ;
- une nouvelle nomination de la même personne au même poste/structure ne
  crée pas de doublon.

Usage : python -m app.annuaire
"""

from __future__ import annotations

import logging

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Document, Mandat, Nomination

logger = logging.getLogger(__name__)


def consolider(db: Session) -> int:
    db.execute(delete(Mandat))

    nominations = db.scalars(
        select(Nomination)
        .join(Document)
        .where(Nomination.statut_validation == "valide")
        .order_by(
            Document.date_publication.asc().nulls_first(),
            Nomination.id.asc(),
        )
    ).all()

    ouverts: dict[int, list[Mandat]] = {}  # personne_id -> mandats sans date_fin
    total = 0
    for nom in nominations:
        date_ref = nom.date_effet or nom.document.date_publication
        if nom.type == "nomination":
            deja = any(
                m.poste == nom.poste and m.structure_id == nom.structure_id
                for m in ouverts.get(nom.personne_id, [])
            )
            if deja:
                continue
            mandat = Mandat(
                personne_id=nom.personne_id,
                structure_id=nom.structure_id,
                poste=nom.poste,
                date_debut=date_ref,
                nomination_debut_id=nom.id,
            )
            db.add(mandat)
            ouverts.setdefault(nom.personne_id, []).append(mandat)
            total += 1
        else:  # fin_fonction
            candidats = ouverts.get(nom.personne_id, [])
            if nom.structure_id is not None:
                cibles = [m for m in candidats if m.structure_id == nom.structure_id] or candidats
            else:
                cibles = candidats
            if cibles:
                mandat = cibles[-1]
                mandat.date_fin = date_ref
                mandat.nomination_fin_id = nom.id
                candidats.remove(mandat)

    db.commit()
    logger.info("Annuaire consolidé : %d mandat(s) à partir de %d nomination(s) validées",
                total, len(nominations))
    return total


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    with SessionLocal() as db:
        n = consolider(db)
        print(f"{n} mandat(s) consolidés.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
