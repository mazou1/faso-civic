"""Collecteur des comptes rendus du Conseil des ministres — PHASE 1.

Squelette volontairement non enregistré dans le registre tant que le
gabarit HTML de gouvernement.gov.bf n'a pas été analysé. La chaîne cible :
listing → pages CR → archivage HTML → extraction des nominations (LLM,
validation humaine) → annuaire (mandats).
"""

from __future__ import annotations

from app.ingestion.base import Collector


class ConseilMinistresCollector(Collector):
    slug = "conseil_ministres"
    listing_url = "https://www.gouvernement.gov.bf/"

    def collect(self) -> None:
        raise NotImplementedError(
            "Phase 1 : analyser le gabarit du site, extraire la liste des CR, "
            "archiver chaque compte rendu (type_doc='cr_conseil')."
        )
