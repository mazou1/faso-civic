"""Normalisation des noms de lieux pour le géocodage."""

import pytest

from app.geo import normaliser_lieu


@pytest.mark.parametrize(
    "brut,attendu",
    [
        ("Ouagadougou", "ouagadougou"),
        ("Bobo-Dioulasso", "bobo dioulasso"),
        ("Fada N'Gourma", "fada n gourma"),
        ("Dédougou", "dedougou"),
        # mots génériques et prépositions retirés
        ("commune de Manga", "manga"),
        ("Ville de Kaya", "kaya"),
        ("région du Sahel", "sahel"),
        ("province du Houet", "houet"),
        ("  Ziniaré  ", "ziniare"),
        (None, ""),
        ("", ""),
    ],
)
def test_normaliser_lieu(brut, attendu):
    assert normaliser_lieu(brut) == attendu
