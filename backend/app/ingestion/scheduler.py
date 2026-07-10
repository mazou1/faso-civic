"""Worker d'ingestion : APScheduler, cadences du cadrage §3.

Un seul process, pas de file distribuée — les volumes (dizaines de
documents/jour) ne justifient ni Celery ni Airflow.
"""

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.db import SessionLocal
from app.ingestion.registry import active_collectors, seed_sources

logger = logging.getLogger(__name__)


def run_medias() -> None:
    with SessionLocal() as db:
        for cls in active_collectors(db, groupe="media"):
            cls(db).run()


def run_institutionnel() -> None:
    """Sources institutionnelles quotidiennes (Légiburkina…)."""
    with SessionLocal() as db:
        for cls in active_collectors(db, groupe="institutionnel"):
            cls(db).run()


def run_conseil_ministres() -> None:
    """Collecte des CR puis structuration LLM (si une clé API est disponible)."""
    with SessionLocal() as db:
        for cls in active_collectors(db, groupe="cm"):
            cls(db).run()
    cle = (
        settings.mistral_api_key
        if settings.llm_provider == "mistral"
        else settings.anthropic_api_key
    )
    if not cle:
        logger.warning(
            "Aucune clé API pour le fournisseur '%s' — structuration des CR non lancée",
            settings.llm_provider,
        )
        return
    from app.extraction import run as extraction_run

    extraction_run.main()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    with SessionLocal() as db:
        seed_sources(db)

    scheduler = BlockingScheduler(timezone="Africa/Ouagadougou")
    scheduler.add_job(run_medias, "interval", minutes=30, id="medias", coalesce=True)
    # Le Conseil des ministres se tient le mercredi ; le CR est publié le soir
    # ou le lendemain — deux passages hebdomadaires + rattrapage quotidien léger.
    scheduler.add_job(
        run_conseil_ministres,
        CronTrigger(day_of_week="wed", hour=20, minute=0),
        id="cm_mercredi",
        coalesce=True,
    )
    scheduler.add_job(
        run_conseil_ministres,
        CronTrigger(day_of_week="thu,fri", hour=10, minute=0),
        id="cm_rattrapage",
        coalesce=True,
    )
    # Institutionnel quotidien : Légiburkina (textes juridiques) tôt le matin.
    # La Présidence passe par le job RSS « medias » toutes les 30 min.
    scheduler.add_job(
        run_institutionnel,
        CronTrigger(hour=6, minute=0),
        id="institutionnel_quotidien",
        coalesce=True,
    )

    logger.info("Worker d'ingestion démarré — collecte immédiate puis cadences planifiées")
    run_medias()
    run_conseil_ministres()
    run_institutionnel()
    scheduler.start()


if __name__ == "__main__":
    main()
