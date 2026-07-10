"""Collecteur RSS des médias burkinabè (métadonnées d'articles).

Les flux ne gardent que ~15 items : le scheduler les interroge toutes les
30 minutes. Phase 0 : on stocke les métadonnées (titre, lien, date) ;
la récupération du texte intégral viendra si le besoin éditorial se confirme.
"""

from __future__ import annotations

import hashlib
from datetime import date

import feedparser

from app.ingestion.base import Collector


class RSSCollector(Collector):
    groupe = "media"
    feed_url: str
    type_doc: str = "article_presse"

    def collect(self) -> None:
        resp = self.get(self.feed_url)
        feed = feedparser.parse(resp.content)
        if feed.bozo and not feed.entries:
            raise ValueError(f"Flux RSS illisible : {self.feed_url} ({feed.bozo_exception})")
        for entry in feed.entries:
            link = getattr(entry, "link", None)
            titre = getattr(entry, "title", None)
            if not link:
                continue
            pub: date | None = None
            parsed = getattr(entry, "published_parsed", None) or getattr(
                entry, "updated_parsed", None
            )
            if parsed:
                pub = date(parsed.tm_year, parsed.tm_mon, parsed.tm_mday)
            digest = hashlib.sha256(f"{link}|{titre}".encode()).hexdigest()
            self.upsert_document(
                url=link,
                type_doc=self.type_doc,
                titre=titre,
                date_publication=pub,
                hash_contenu=digest,
                statut_extraction="na",
                meta={"resume": getattr(entry, "summary", None)},
            )


def make_rss_collector(
    slug: str, feed_url: str, type_doc: str = "article_presse"
) -> type[RSSCollector]:
    return type(
        f"RSS_{slug}",
        (RSSCollector,),
        {"slug": slug, "feed_url": feed_url, "type_doc": type_doc},
    )
