"""Seed du gazetteer `localite` depuis app/data/localites_bf.csv (GeoNames).

Idempotent : ne réinsère pas ce qui existe déjà (clé nom_normalise + type +
region). Usage : python -m app.geo_seed
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path

from sqlalchemy import select

from app.db import SessionLocal
from app.geo import normaliser_lieu
from app.models import Localite

logger = logging.getLogger(__name__)

CSV = Path(__file__).parent / "data" / "localites_bf.csv"


def seed(db) -> int:
    existants = {
        (n, t, r or "")
        for n, t, r in db.execute(
            select(Localite.nom_normalise, Localite.type, Localite.region)
        ).all()
    }
    ajouts = 0
    with CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            nom = row["nom"].strip()
            norm = normaliser_lieu(nom)
            cle = (norm, row["type"], row["region"] or "")
            if not norm or cle in existants:
                continue
            existants.add(cle)
            db.add(
                Localite(
                    nom=nom,
                    nom_normalise=norm,
                    type=row["type"],
                    region=row["region"] or None,
                    province=row["province"] or None,
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    population=int(row["population"]) if row["population"] else None,
                    source="geonames",
                )
            )
            ajouts += 1
    db.commit()
    return ajouts


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    with SessionLocal() as db:
        n = seed(db)
        total = db.scalar(select(Localite.id).order_by(Localite.id.desc()).limit(1)) or 0
    print(f"{n} localité(s) ajoutée(s) au gazetteer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
