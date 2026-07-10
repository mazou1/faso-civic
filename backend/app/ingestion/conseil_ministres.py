"""Comptes rendus du Conseil des ministres — gouvernement.gov.bf.

Le site est un WordPress avec API REST ouverte ; la catégorie 23
(« Compte rendu », vérifiée le 2026-07-10) contient les CR officiels.
Chaîne complète : collecte → texte → extraction LLM des nominations
(app.extraction.nominations) → validation humaine → annuaire (app.annuaire).
"""

from __future__ import annotations

from app.ingestion.wordpress import WordPressCollector


class ConseilMinistresCollector(WordPressCollector):
    slug = "conseil_ministres"
    groupe = "cm"  # cadence hebdomadaire propre (mercredi), distincte du quotidien institutionnel
    api_base = "https://gouvernement.gov.bf/wp-json/wp/v2"
    categories = "23"  # « Compte rendu » (parent « Conseil des ministres »)
    type_doc = "cr_conseil"
