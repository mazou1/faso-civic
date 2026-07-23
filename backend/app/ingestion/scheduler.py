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
from app.ingestion.surveillance import verifier_sources_muettes

logger = logging.getLogger(__name__)


def run_medias() -> None:
    with SessionLocal() as db:
        for cls in active_collectors(db, groupe="media"):
            cls(db).run()


def run_institutionnel() -> None:
    """Sources institutionnelles quotidiennes (Légiburkina, actualités gouv…)
    puis extraction bornée des réalisations d'infrastructure sur les nouvelles
    actualités (si une clé LLM est disponible)."""
    with SessionLocal() as db:
        for cls in active_collectors(db, groupe="institutionnel"):
            cls(db).run()
    cle = (
        settings.mistral_api_key
        if settings.llm_provider == "mistral"
        else settings.anthropic_api_key
    )
    if not cle:
        return
    from app.extraction.realisations import traiter_lot

    with SessionLocal() as db:
        # borné : le flot quotidien est faible ; le backfill se lance à la main
        vus, total, _, echecs = traiter_lot(db, max_docs=60)
    logger.info(
        "Réalisations : %d actualité(s) examinée(s), %d extraite(s) (à valider), %d échec(s)",
        vus, total, echecs,
    )


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

    # misfire_grace_time large : sur une machine qui se met en veille (WSL2,
    # portable), un déclenchement dû pendant la suspension serait sinon « manqué »
    # et sauté au réveil — d'où des sources muettes silencieuses. 6h de tolérance
    # + coalesce : le job dû tourne une fois au réveil.
    scheduler = BlockingScheduler(
        timezone="Africa/Ouagadougou",
        job_defaults={"coalesce": True, "misfire_grace_time": 6 * 3600},
    )
    scheduler.add_job(run_medias, "interval", minutes=30, id="medias", coalesce=True)
    scheduler.add_job(
        verifier_sources_muettes,
        CronTrigger(hour=7, minute=30),
        id="alerte_sources_muettes",
    )
    # Le Conseil des ministres se tient désormais le jeudi ; le CR est publié
    # le soir ou le lendemain — passage jeudi soir + rattrapages.
    scheduler.add_job(
        run_conseil_ministres,
        CronTrigger(day_of_week="thu", hour=20, minute=0),
        id="cm_jeudi",
        coalesce=True,
    )
    scheduler.add_job(
        run_conseil_ministres,
        CronTrigger(day_of_week="fri,sat", hour=10, minute=0),
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
    verifier_sources_muettes()
    scheduler.start()


if __name__ == "__main__":
    main()
