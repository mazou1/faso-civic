"""Worker d'ingestion : APScheduler, cadences du cadrage §3.

Un seul process, pas de file distribuée — les volumes (dizaines de
documents/jour) ne justifient ni Celery ni Airflow.
"""

import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from app.db import SessionLocal
from app.ingestion.registry import active_collectors, seed_sources

logger = logging.getLogger(__name__)


def run_all_rss() -> None:
    with SessionLocal() as db:
        for cls in active_collectors(db):
            cls(db).run()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    with SessionLocal() as db:
        seed_sources(db)

    scheduler = BlockingScheduler(timezone="Africa/Ouagadougou")
    scheduler.add_job(run_all_rss, "interval", minutes=30, id="rss", coalesce=True)
    # Phase 1 : job hebdomadaire Conseil des ministres (mercredi soir + rattrapage jeudi)
    # Phase 2 : jobs quotidiens Légiburkina / SIG / Présidence

    logger.info("Worker d'ingestion démarré — collecte RSS immédiate puis toutes les 30 min")
    run_all_rss()
    scheduler.start()


if __name__ == "__main__":
    main()
