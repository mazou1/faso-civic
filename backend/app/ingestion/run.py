"""Exécution manuelle d'un collecteur : python -m app.ingestion.run <slug|all>"""

import logging
import sys

from app.db import SessionLocal
from app.ingestion.registry import COLLECTORS, active_collectors, seed_sources


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if len(sys.argv) != 2:
        print(f"Usage : python -m app.ingestion.run <slug|all>\nSlugs : {', '.join(COLLECTORS)}")
        return 1
    target = sys.argv[1]
    with SessionLocal() as db:
        seed_sources(db)
        if target == "all":
            classes = active_collectors(db)
        elif target in COLLECTORS:
            classes = [COLLECTORS[target]]
        else:
            print(f"Slug inconnu : {target}. Slugs : {', '.join(COLLECTORS)}")
            return 1
        for cls in classes:
            cls(db).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
