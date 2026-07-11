"""Assemblée législative — synchronisation de la liste des députés.

assembleenationale.bf sert la liste côté serveur : chaque député est une
carte avec photo officielle (an.bf/storage/Photos/…) et le nom en attribut
alt. On synchronise la table depute (les disparus passent actif=False).
"""

from __future__ import annotations

import logging
import re

from selectolax.parser import HTMLParser
from sqlalchemy import select

from app.ingestion.base import Collector
from app.models import Depute

logger = logging.getLogger(__name__)


class AssembleeCollector(Collector):
    slug = "assemblee"
    groupe = "institutionnel"
    url_deputes = "https://www.assembleenationale.bf/depute/depute"

    def collect(self) -> None:
        resp = self.get(self.url_deputes)
        tree = HTMLParser(resp.text)

        legislature = None
        m = re.search(r"Legislature\s*:\s*([0-9]{4})", resp.text)
        if m:
            legislature = m.group(1)

        vus: dict[str, str | None] = {}
        for img in tree.css("img[alt]"):
            src = (img.attributes.get("src") or "").strip()
            nom = (img.attributes.get("alt") or "").strip()
            if "storage/Photos" in src and len(nom) > 3:
                vus.setdefault(nom, src)
        if not vus:
            raise ValueError("Aucun député trouvé — le gabarit du site a probablement changé")

        existants = {d.nom_complet: d for d in self.db.scalars(select(Depute)).all()}
        for nom, photo in vus.items():
            d = existants.get(nom)
            if d is None:
                self.db.add(
                    Depute(nom_complet=nom, legislature=legislature, photo_url=photo, actif=True)
                )
                self.nb_nouveaux += 1
            else:
                d.photo_url = photo or d.photo_url
                d.legislature = legislature or d.legislature
                d.actif = True
                self.nb_vus += 1
        for nom, d in existants.items():
            if nom not in vus and d.actif:
                d.actif = False
                logger.info("Député sorti de la liste : %s", nom)
        self.db.commit()
