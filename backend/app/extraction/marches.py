"""Extraction des marchés attribués depuis le Quotidien des Marchés Publics.

Les « Synthèses des résultats » du Quotidien (DGCMEF) donnent, pour chaque
appel, l'entreprise retenue et le montant. Le PDF est volumineux (≈90 pages) :
on le découpe en fenêtres et un LLM (Mistral par défaut) en extrait les
marchés RÉELLEMENT attribués (attributaire + montant identifiables). Tout
arrive en statut_validation='a_valider' — validation humaine avant publication.

Usage : python -m app.extraction.marches [max_docs]
"""

from __future__ import annotations

import logging
import re
import sys
import time

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.extraction.conseil_ministres import MODELE_ANTHROPIC, MODELE_MISTRAL
from app.models import Document, Marche

logger = logging.getLogger(__name__)

# On n'extrait pas au fil du texte (les tableaux comparatifs aplatis brouillent
# tout) mais on s'ancre sur les ATTRIBUTIONS explicites : « … pour un montant
# de [lettres] (CHIFFRES) F CFA ». Le montant est fiable (chiffres entre
# parenthèses) ; le LLM lit une fenêtre ciblée en amont pour l'autorité, l'objet
# et l'attributaire.
AVANT = 700  # caractères de contexte avant l'ancre
APRES = 120
RE_ATTRIB = re.compile(
    r"pour un montant de .{0,120}?\(([\d  .]+)\)\s*(?:F\.?\s?CFA|francs?)",
    re.IGNORECASE,
)


class MarcheExtrait(BaseModel):
    autorite: str = Field(description="Autorité contractante (organisme qui passe le marché)")
    objet: str = Field(description="Objet du marché — ce qui est acquis ou réalisé")
    reference: str | None = Field(
        default=None, description="Référence de l'appel (ex: « Demande de prix n°2026-006/… »)"
    )
    mode: str | None = Field(
        default=None, description="Mode de passation (demande de prix, appel d'offres ouvert…)"
    )
    attributaire: str = Field(description="Entreprise/soumissionnaire retenu (l'attributaire)")
    montant_fcfa: int | None = Field(
        default=None, description="Montant attribué en FCFA, entier sans espaces, sinon null"
    )
    region: str | None = Field(default=None, description="Région si mentionnée")
    confiance: float = Field(ge=0, le=1, description="Certitude de l'extraction, 0 à 1")


class ExtractionMarches(BaseModel):
    marches: list[MarcheExtrait]


PROMPT = """\
Tu analyses un extrait du Quotidien des Marchés Publics du Burkina Faso, centré \
sur UNE attribution de marché (la phrase « … pour un montant de … F CFA »).

Extrais CE marché attribué : l'autorité contractante (l'organisme public qui \
passe le marché — pas une adresse ni un numéro RCCM), l'objet (ce qui est \
acquis ou réalisé), la référence de l'appel (ex: « Demande de prix \
n°2026-006/… »), le mode de passation, l'entreprise ATTRIBUTAIRE (le nom qui \
précède « pour un montant de »), le montant en FCFA et la région si présente.

N'INVENTE RIEN : un champ absent reste null. L'attributaire est une entreprise \
(pas un numéro, pas « Néant »). Retourne ce seul marché dans la liste (ou une \
liste vide si l'extrait ne décrit pas une attribution claire)."""


def _appel_llm(texte: str) -> ExtractionMarches:
    if settings.llm_provider == "anthropic":
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key or None)
        rep = client.messages.parse(
            model=MODELE_ANTHROPIC,
            max_tokens=8000,
            system=PROMPT,
            messages=[{"role": "user", "content": texte}],
            output_format=ExtractionMarches,
        )
        return rep.parsed_output

    from mistralai.client import Mistral

    client = Mistral(api_key=settings.mistral_api_key)
    for tentative in range(4):
        try:
            rep = client.chat.parse(
                model=MODELE_MISTRAL,
                messages=[
                    {"role": "system", "content": PROMPT},
                    {"role": "user", "content": texte},
                ],
                response_format=ExtractionMarches,
                temperature=0,
            )
            break
        except Exception as exc:  # noqa: BLE001
            if getattr(exc, "status_code", None) == 429 and tentative < 3:
                time.sleep(5 * (tentative + 1))
                continue
            raise
    parsed = rep.choices[0].message.parsed
    return parsed or ExtractionMarches(marches=[])


def _montant(brut: str) -> int | None:
    chiffres = re.sub(r"[^\d]", "", brut)
    return int(chiffres) if chiffres else None


def traiter_document(db: Session, doc: Document) -> int:
    """Extrait les marchés attribués d'un Quotidien. Renvoie le nombre créé.

    Une entrée par attribution explicite ; le LLM ne voit qu'une fenêtre ciblée
    autour de l'ancre, ce qui écarte le bruit des tableaux comparatifs.
    """
    texte = doc.texte_extrait or ""
    vus: set[tuple] = set()
    crees = 0
    for anc in RE_ATTRIB.finditer(texte):
        montant = _montant(anc.group(1))
        if not montant or montant < 100_000:  # écarte les fragments de tableau
            continue
        fenetre = texte[max(0, anc.start() - AVANT) : anc.end() + APRES]
        try:
            res = _appel_llm(fenetre)
        except Exception:
            logger.exception("Échec LLM sur une ancre du document %s", doc.id)
            continue
        # la fenêtre est centrée sur UNE attribution : on prend le meilleur candidat
        cand = max(
            (m for m in res.marches if m.attributaire and m.objet),
            key=lambda m: m.confiance,
            default=None,
        )
        if cand is None:
            continue
        cle = (re.sub(r"\s+", "", cand.attributaire.lower()), montant)
        if cle in vus:
            continue
        vus.add(cle)
        db.add(
            Marche(
                document_id=doc.id,
                autorite=cand.autorite[:400],
                objet=cand.objet,
                reference=(cand.reference or None),
                mode=(cand.mode or None),
                attributaire=cand.attributaire[:400],
                montant_fcfa=cand.montant_fcfa or montant,  # le chiffre de l'ancre fait foi
                region=(cand.region or None),
                date_attribution=doc.date_publication,
                score_confiance=cand.confiance,
                statut_validation="a_valider",
            )
        )
        crees += 1
        time.sleep(1.2)  # politesse tier gratuit
    db.commit()
    return crees


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    max_docs = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    with SessionLocal() as db:
        # les Quotidiens sans marché encore extrait, les plus récents d'abord
        deja = select(Marche.document_id).distinct().subquery()
        docs = db.scalars(
            select(Document)
            .where(
                Document.type_doc == "marche_public",
                Document.texte_extrait.is_not(None),
                Document.id.not_in(select(deja.c.document_id)),
            )
            .order_by(Document.date_publication.desc().nulls_last())
            .limit(max_docs)
        ).all()
        if not docs:
            print("Aucun Quotidien en attente d'extraction.")
            return 0
        total = 0
        for doc in docs:
            n = traiter_document(db, doc)
            total += n
            logger.info("%s : %d marché(s) attribué(s) extraits", doc.titre, n)
        print(f"{len(docs)} Quotidien(s) traité(s) : {total} marché(s) à valider dans /admin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
