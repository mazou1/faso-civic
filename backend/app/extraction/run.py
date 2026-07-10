"""Structuration manuelle des CR : python -m app.extraction.run [max_docs]

Traite les comptes rendus du Conseil des ministres pas encore structurés
(décisions + nominations), les plus récents d'abord.
"""

import logging
import sys

from sqlalchemy import select

from app.db import SessionLocal
from app.extraction.conseil_ministres import traiter_document
from app.models import Document


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    max_docs = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    with SessionLocal() as db:
        docs = db.scalars(
            select(Document)
            .where(
                Document.type_doc == "cr_conseil",
                Document.date_structuration.is_(None),
            )
            .order_by(Document.date_publication.desc().nulls_last())
            .limit(max_docs)
        ).all()
        if not docs:
            print("Aucun compte rendu en attente de structuration.")
            return 0
        total_d = total_n = 0
        for doc in docs:
            d, n = traiter_document(db, doc)
            total_d += d
            total_n += n
        print(
            f"{len(docs)} document(s) traité(s) : {total_d} décision(s) et "
            f"{total_n} nomination(s) extraites (à valider dans /admin)."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
