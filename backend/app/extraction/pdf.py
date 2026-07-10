"""Extraction PDF → texte : pdfplumber, puis OCR Tesseract (fra) en secours.

Les sites .gov.bf publient beaucoup de scans : si le texte natif est quasi
vide, on bascule en OCR. Renvoie (texte, statut) avec statut ∈ ok | ocr | echec.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pdfplumber

logger = logging.getLogger(__name__)

SEUIL_TEXTE_NATIF = 100  # en dessous de ~100 caractères, on considère le PDF scanné


def extraire_texte(path: Path) -> tuple[str, str]:
    try:
        with pdfplumber.open(path) as pdf:
            natif = "\n\n".join(page.extract_text() or "" for page in pdf.pages).strip()
            if len(natif) >= SEUIL_TEXTE_NATIF:
                return natif, "ok"
            return _ocr(pdf), "ocr"
    except Exception:
        logger.exception("Extraction impossible : %s", path)
        return "", "echec"


def _ocr(pdf: pdfplumber.PDF) -> str:
    import pytesseract  # import tardif : dépend du binaire tesseract

    pages = []
    for page in pdf.pages:
        image = page.to_image(resolution=200).original
        pages.append(pytesseract.image_to_string(image, lang="fra"))
    return "\n\n".join(pages).strip()
