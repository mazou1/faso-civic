"""Taxonomie de l'annuaire : type d'institution (déduit du nom, le champ
`structure.type` n'ayant jamais été peuplé) et catégorie de fonction (déduite
de l'intitulé du poste). Heuristiques déterministes par mots-clés, priorité du
spécifique au générique — la première règle qui matche gagne.
"""

from __future__ import annotations

import re

# --- type d'institution -------------------------------------------------------
# groupe d'affichage → ordre + libellé
GROUPES_INSTITUTION = [
    ("ministere", "Ministères"),
    ("institution", "Présidence, Primature & institutions"),
    ("juridiction", "Justice & juridictions"),
    ("etablissement", "Établissements publics & sociétés d'État"),
]

_INSTIT = [
    ("ministere", re.compile(r"^\s*minist[èe]re\b", re.I)),
    ("institution", re.compile(
        r"^\s*(?:pr[ée]sidence|primature|premier\s+minist|assembl[ée]e|"
        r"conseil\s+[ée]conomique|conseil\s+sup[ée]rieur|m[ée]diateur|"
        r"grande\s+chancellerie|secr[ée]tariat\s+g[ée]n[ée]ral\s+du\s+gouvernement)", re.I)),
    ("juridiction", re.compile(
        r"^\s*(?:cour\b|tribunal|conseil\s+constitutionnel|conseil\s+d.[ée]tat|"
        r"conseil\s+sup[ée]rieur\s+de\s+la\s+magistrature|parquet|minist[èe]re\s+public)", re.I)),
]


def type_institution(nom: str | None, sigle: str | None = None) -> str:
    """ministere | institution | juridiction | etablissement (défaut).

    Un « Ministère … » PORTANT un sigle est en réalité l'établissement/société
    d'État désigné par ce sigle (artefact de données : son nom a été fixé à celui
    de son ministère de tutelle). Les vrais ministères n'ont pas de sigle ici.
    """
    n = nom or ""
    if sigle and re.match(r"^\s*minist[èe]re\b", n, re.I):
        return "etablissement"
    for code, motif in _INSTIT:
        if motif.search(n):
            return code
    return "etablissement"


# --- catégorie de fonction ----------------------------------------------------
# ordre = priorité (spécifique avant générique)
CATEGORIES_FONCTION = [
    "Membres du gouvernement",
    "Diplomatie & représentation",
    "Conseils d'administration",
    "Cabinet & conseil",
    "Direction & encadrement",
    "Inspection & contrôle",
    "Autres fonctions",
]

_FONCTION = [
    ("Membres du gouvernement", re.compile(
        r"\bministres?\b|secr[ée]taire\s+d.[ée]tat|ministre\s+d.[ée]tat", re.I)),
    ("Diplomatie & représentation", re.compile(
        r"ambassad|consul\b|consulaire|charg[ée]\s+d.affaires|mission\s+diplomatique|"
        r"repr[ée]sentant\s+permanent", re.I)),
    ("Conseils d'administration", re.compile(
        r"administrateur|conseil\s+d.administration|repr[ée]sentant.{0,25}[ée]tat", re.I)),
    ("Cabinet & conseil", re.compile(
        r"cabinet|charg[ée]s?\s+de\s+missions?|conseiller|charg[ée]s?\s+d.[ée]tudes?|"
        r"attach[ée]|secr[ée]taire\s+particulier", re.I)),
    ("Direction & encadrement", re.compile(
        r"directeur|directrice|direction|chef\s+de\b|secr[ée]taire\s+g[ée]n[ée]ral|"
        r"secr[ée]taire\s+technique|coordonnateur|coordinateur|pr[ée]sident|recteur|"
        r"proviseur|gouverneur|haut-?commissaire|pr[ée]fet", re.I)),
    ("Inspection & contrôle", re.compile(
        r"inspect|contr[ôo]le|contr[ôo]leur|v[ée]rificateur|auditeur", re.I)),
]


def categorie_fonction(poste: str | None) -> str:
    p = poste or ""
    for cat, motif in _FONCTION:
        if motif.search(p):
            return cat
    return "Autres fonctions"
