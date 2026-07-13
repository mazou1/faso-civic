"""Flux RSS 2.0 de la plateforme : suivre les nouvelles publications dans un
lecteur de flux, sans compte ni e-mail.

Trois flux : les comptes rendus du Conseil des ministres, le fil d'actualités
(médias + communiqués) et les nouveaux textes juridiques. Généré à la main
(pas de dépendance) avec échappement XML strict.
"""

from __future__ import annotations

from datetime import datetime, time, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape

from starlette.requests import Request


def _date_rfc822(d) -> str | None:
    if d is None:
        return None
    if not isinstance(d, datetime):
        d = datetime.combine(d, time(12, 0), tzinfo=timezone.utc)
    elif d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return format_datetime(d)


def _base_site(request: Request) -> str:
    """Origine publique du site (le RSS est servi sous /api mais renvoie vers
    les pages du site à la racine du même hôte)."""
    return str(request.base_url).rstrip("/").removesuffix("/api")


def flux_rss(
    request: Request,
    *,
    titre: str,
    description: str,
    chemin: str,
    items: list[dict],
) -> str:
    """`items` : liste de {titre, lien, description, date, guid}."""
    base = _base_site(request)
    self_url = f"{base}/api{chemin}"
    morceaux = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        "<channel>",
        f"<title>{escape(titre)}</title>",
        f"<link>{escape(base)}/</link>",
        f"<description>{escape(description)}</description>",
        "<language>fr</language>",
        f'<atom:link href="{escape(self_url)}" rel="self" type="application/rss+xml"/>',
    ]
    for it in items:
        morceaux.append("<item>")
        morceaux.append(f"<title>{escape(it['titre'])}</title>")
        morceaux.append(f"<link>{escape(it['lien'])}</link>")
        morceaux.append(f'<guid isPermaLink="false">{escape(str(it["guid"]))}</guid>')
        if it.get("description"):
            morceaux.append(f"<description>{escape(it['description'])}</description>")
        pub = _date_rfc822(it.get("date"))
        if pub:
            morceaux.append(f"<pubDate>{pub}</pubDate>")
        morceaux.append("</item>")
    morceaux.append("</channel></rss>")
    return "\n".join(morceaux)
