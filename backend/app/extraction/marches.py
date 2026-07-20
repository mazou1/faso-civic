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


def renettoyer_objets() -> int:
    """Nettoie objet ET attributaire des marchés en base (idempotent). Les
    lignes dont l'attributaire est cassé (objet débordé) sont démotées en
    'a_valider' pour revue plutôt que publiées avec un faux attributaire."""
    from app.extraction.marches_tableau import nettoyer_attributaire, nettoyer_objet

    with SessionLocal() as db:
        marches = db.scalars(select(Marche)).all()
        obj_mod = att_mod = demotes = 0
        for m in marches:
            net_o = nettoyer_objet(m.objet)
            if net_o and net_o != m.objet:
                m.objet = net_o
                obj_mod += 1
            net_a = nettoyer_attributaire(m.attributaire)
            if net_a is None:  # attributaire inexploitable → à revoir
                if m.statut_validation == "valide":
                    m.statut_validation = "a_valider"
                    demotes += 1
            elif net_a != m.attributaire:
                m.attributaire = net_a
                att_mod += 1
        db.commit()
        print(
            f"{obj_mod} objet(s) et {att_mod} attributaire(s) nettoyés ; "
            f"{demotes} ligne(s) cassée(s) démotée(s) en a_valider."
        )
    return 0


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if len(sys.argv) > 1 and sys.argv[1] == "renettoyer":
        return renettoyer_objets()
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
