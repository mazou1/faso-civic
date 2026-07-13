"""« La source en contexte » : localiser la phrase d'un compte rendu d'où une
entité a été extraite, et la renvoyer avec les ancres surlignées.

Rien n'est stocké au moment de l'extraction : on localise à la demande dans le
texte intégral, en s'ancrant sur ce qui apparaît mot pour mot (matricule, nom,
montant, bénéficiaire). Renvoie du HTML sûr (texte échappé, seuls des <mark>
ajoutés) ou None si l'ancre est introuvable.
"""

from __future__ import annotations

import html
import re

# fin de phrase / d'énumération : point suivi d'espace, ou « ; - » qui sépare
# deux nominations dans un même bloc. On garde des bornes lisibles.
_FIN = re.compile(r"\.\s|\s*;\s*-")


def _regex_matricule(mat: str) -> re.Pattern | None:
    """« 355091N » → motif tolérant les espaces/points du texte (« 355 091 N »)."""
    car = [c for c in mat if c.isalnum()]
    if len(car) < 4:
        return None
    return re.compile(r"[\s.]*".join(map(re.escape, car)), re.IGNORECASE)


def _trouver(texte: str, ancre: str, matricule: bool = False) -> tuple[int, int] | None:
    if matricule:
        motif = _regex_matricule(ancre)
        m = motif.search(texte) if motif else None
    else:
        m = re.search(re.escape(ancre), texte, re.IGNORECASE)
    return (m.start(), m.end()) if m else None


def _bornes_phrase(texte: str, deb: int, fin: int) -> tuple[int, int]:
    """Étend [deb, fin] aux limites de la phrase englobante."""
    # début : après le dernier tiret de puce ou fin de phrase avant l'ancre
    gauche = max(texte.rfind("\n", 0, deb), texte.rfind(". ", 0, deb) + 1)
    tiret = texte.rfind("- ", max(gauche, 0), deb)
    debut = max(gauche, tiret)
    if debut < 0:
        debut = 0
    debut = min(debut + 2, deb) if texte[debut : debut + 2] in ("- ", "\n-") else max(debut, 0)
    # fin : première fin de phrase après l'ancre
    m = _FIN.search(texte, fin)
    finp = m.start() + 1 if m else min(fin + 240, len(texte))
    return debut, finp


def localiser(texte: str | None, ancres: list[tuple[str, bool]]) -> str | None:
    """`ancres` = liste de (chaîne, est_matricule), essayées dans l'ordre.

    Renvoie la phrase englobante en HTML échappé avec les ancres en <mark>,
    ou None si aucune ancre n'est trouvée.
    """
    if not texte:
        return None
    spans: list[tuple[int, int]] = []
    for ancre, est_mat in ancres:
        if not ancre:
            continue
        pos = _trouver(texte, ancre, est_mat)
        if pos:
            spans.append(pos)
    if not spans:
        return None
    spans.sort()
    debut, fin = _bornes_phrase(texte, spans[0][0], spans[0][1])
    # surligne toutes les ancres tombant dans la phrase
    dedans = sorted((max(d, debut), min(f, fin)) for d, f in spans if d >= debut and f <= fin)
    out, curseur = [], debut
    for d, f in dedans:
        if d < curseur:
            continue
        out.append(html.escape(texte[curseur:d]))
        out.append("<mark>" + html.escape(texte[d:f]) + "</mark>")
        curseur = f
    out.append(html.escape(texte[curseur:fin]))
    return re.sub(r"\s+", " ", "".join(out)).strip()
