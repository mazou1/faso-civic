"""Validation en masse par seuil de confiance.

Complément CLI aux actions de l'admin : valide d'un coup toutes les décisions
et nominations `a_valider` dont le score de confiance atteint le seuil.
Les entités sous le seuil restent en file pour revue manuelle dans /admin.

Usage : python -m app.validation [seuil]   (défaut : 0.9)
"""

from __future__ import annotations

import logging
import sys

from sqlalchemy import func, select, update

from app.db import SessionLocal
from app.models import BudgetExercice, Decision, EngagementFinancier, Nomination


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    seuil = float(sys.argv[1]) if len(sys.argv) > 1 else 0.9
    with SessionLocal() as db:
        cibles = (
            (Decision, "décisions"),
            (Nomination, "nominations"),
            (EngagementFinancier, "engagements financiers"),
            (BudgetExercice, "budgets d'exercice"),
        )
        for modele, nom in cibles:
            valides = db.execute(
                update(modele)
                .where(
                    modele.statut_validation == "a_valider",
                    modele.score_confiance >= seuil,
                )
                .values(statut_validation="valide")
            ).rowcount
            restants = db.scalar(
                select(func.count())
                .select_from(modele)
                .where(modele.statut_validation == "a_valider")
            )
            print(f"{nom} : {valides} validées (confiance ≥ {seuil}), {restants} restantes à revoir")
        db.commit()
    print("Penser à consolider l'annuaire : python -m app.annuaire")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
