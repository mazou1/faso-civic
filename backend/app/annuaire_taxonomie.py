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

    Le nom fait foi. Un « Ministère … » portant un sigle (ONEA, SAMU, ENEF…)
    reste un ministère : vérifié en base le 2026-07-21, aucun de ces sigles ne
    désigne une structure par ailleurs et les mandats rattachés sont bien des
    postes ministériels (directeurs provinciaux, inspecteurs techniques…). Le
    sigle est du bruit d'extraction — voir `sigle_fiable`.
    """
    n = nom or ""
    for code, motif in _INSTIT:
        if motif.search(n):
            return code
    return "etablissement"


def sigle_fiable(nom: str | None, sigle: str | None) -> bool:
    """Un sigle accolé à un nom de ministère provient d'une nomination voisine
    (« Directeur général de l'ONEA ») et ne désigne pas la structure : on ne
    l'affiche pas."""
    return bool(sigle) and not re.match(r"^\s*minist[èe]re\b", nom or "", re.I)


# --- portefeuille ministériel -------------------------------------------------
# Les ministères sont renommés à chaque remaniement (« Ministère de la Santé »
# → « … de la Santé et de l'Hygiène publique ») et chaque intitulé a créé sa
# propre structure. On les regroupe sous un portefeuille commun, sans rien
# fusionner en base : les intitulés successifs restent visibles.

_ARTICLES = re.compile(
    r"^(?:de(?:s|\s+la|\s+l)?|du|d|l|le|la|les|et|en|aux?|charg[ée]e?s?)$", re.I)
_ACCENTS = str.maketrans("àâäçéèêëîïôöùûüÿ", "aaaceeeeiioouuuy")

# Mots de tête trop génériques pour identifier seuls un portefeuille : on prend
# alors les deux premiers mots significatifs (« Enseignement de base » ≠
# « Enseignement supérieur »).
_LEADS_AMBIGUS = {
    "affaires", "action", "developpement", "enseignement",
    "fonction", "transition", "conseil", "secretariat",
}


def _mots_significatifs(nom: str) -> list[str]:
    n = re.sub(r"^\s*minist[èe]re\s*", "", nom or "", flags=re.I)
    # minuscules AVANT le pliage : la table ne couvre que le bas de casse, et
    # un « É » résiduel serait mangé par le découpage (« Économie » → conomie)
    n = n.lower().translate(_ACCENTS).replace("’", " ").replace("'", " ")
    mots = [m for m in re.split(r"[^a-z]+", n) if m]
    return [m for m in mots if not _ARTICLES.match(m)]


def portefeuille(nom: str | None) -> str | None:
    """Clé de regroupement des intitulés successifs d'un même ministère, ou
    None hors ministère. Heuristique volontairement prudente : deux intitulés
    ne sont regroupés que s'ils partagent leur(s) mot(s) de tête."""
    if type_institution(nom) != "ministere":
        return None
    mots = _mots_significatifs(nom or "")
    if not mots:
        return None
    if mots[0] in _LEADS_AMBIGUS and len(mots) > 1:
        return f"{mots[0]} {mots[1]}"
    return mots[0]


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
