"""Utilitaires texte : HTML → texte brut, normalisation des noms de personnes."""

from __future__ import annotations

import re
import unicodedata

from selectolax.parser import HTMLParser


def html_vers_texte(html: str) -> str:
    """Extrait le texte lisible d'un fragment HTML (contenu WordPress, etc.)."""
    tree = HTMLParser(html)
    for node in tree.css("script, style"):
        node.decompose()
    texte = tree.body.text(separator="\n") if tree.body else tree.text(separator="\n")
    texte = re.sub(r"[ \t ]+", " ", texte)
    texte = re.sub(r"\n\s*\n+", "\n\n", texte)
    return texte.strip()


def normaliser_nom(nom: str) -> str:
    """Forme canonique pour rapprocher les mentions d'une même personne.

    Minuscules, sans accents, espaces réduits. La fusion des homonymes
    reste une décision humaine (cf. cadrage §4).
    """
    nfkd = unicodedata.normalize("NFKD", nom)
    sans_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    unifie = sans_accents.replace("’", "'").replace("‘", "'").replace("-", " ")
    return re.sub(r"\s+", " ", unifie).strip().lower()
