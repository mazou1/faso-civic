"""Extraction des marchés attribués depuis le Quotidien des Marchés Publics.

Approche déterministe (pas de LLM) : les « Synthèses des résultats » du
Quotidien (DGCMEF) sont des tableaux à colonnes préservées par pdfplumber ;
`marches_tableau.extraire_marches` lit l'autorité contractante, l'objet, la
référence, l'attributaire retenu et son montant. Les résultats arrivent en
statut_validation='a_valider' — validation humaine avant publication.

Usage : python -m app.extraction.marches [max_docs]
"""

from __future__ import annotations

import logging
import sys

from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.extraction.marches_tableau import extraire_marches
from app.models import Document, Marche


def traiter_document(db, doc: Document) -> int:
    """Extrait les marchés attribués d'un Quotidien depuis son PDF archivé."""
    if not doc.fichier:
        return 0
    marches = extraire_marches(settings.data_dir / doc.fichier)
    for m in marches:
        db.add(
            Marche(
                document_id=doc.id,
                autorite=m["autorite"],
                objet=m["objet"],
                reference=m.get("reference"),
                mode=m.get("mode"),
                attributaire=m["attributaire"],
                montant_fcfa=m["montant_fcfa"],
                region=m.get("region"),
                date_attribution=doc.date_publication,
                score_confiance=None,  # extraction déterministe, pas de score
                statut_validation="a_valider",
            )
        )
    db.commit()
    return len(marches)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    max_docs = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    with SessionLocal() as db:
        deja = select(Marche.document_id).distinct().subquery()
        docs = db.scalars(
            select(Document)
            .where(
                Document.type_doc == "marche_public",
                Document.fichier.is_not(None),
                Document.id.not_in(select(deja.c.document_id)),
            )
            .order_by(Document.date_publication.desc().nulls_last())
            .limit(max_docs)
        ).all()
        if not docs:
            print("Aucun Quotidien en attente d'extraction.")
            return 0
        total = 0
        for doc in docs:
            n = traiter_document(db, doc)
            total += n
            logging.info("%s : %d marché(s) attribué(s)", doc.titre, n)
        print(f"{len(docs)} Quotidien(s) : {total} marché(s) à valider dans /admin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
