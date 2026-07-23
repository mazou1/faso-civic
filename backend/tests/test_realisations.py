"""Pré-filtre de pertinence des actualités (avant appel LLM)."""

import pytest

from app.extraction.realisations import SECTEUR_PAR_TYPE, pertinent


@pytest.mark.parametrize(
    "titre",
    [
        "Souveraineté énergétique : une centrale thermique de 50 MW inaugurée à Pabré",
        "Santé : pose de la première pierre d'un hôpital à Manga",
        "Route Bobo-Banfora : le tronçon bitumé réceptionné",
        "Éducation : un lycée mis en service à Dori",
        "Eau : inauguration d'un château d'eau à Kaya",
    ],
)
def test_pertinent_infrastructures(titre):
    assert pertinent(titre, "")


@pytest.mark.parametrize(
    "titre",
    [
        "Athlétisme : Marthe Koala décroche l'or au World Continental Tour",
        "Le Président a reçu les émissaires de la CEDEAO",
        "Nomination : le camarade ministre installe son cabinet",
        "Congrès extraordinaire de la Communauté internationale des Soufis",
    ],
)
def test_non_pertinent(titre):
    assert not pertinent(titre, "")


def test_prefiltre_exige_ouvrage_ET_acte():
    # un ouvrage sans acte d'ouverture, ou l'inverse, ne passe pas
    assert not pertinent("Le ministre visite une école", "")
    assert not pertinent("Inauguration du nouveau logo du ministère", "")


def test_tous_les_types_ont_un_secteur():
    from app.extraction.realisations import RealisationExtraite

    # chaque valeur du Literal `type` doit avoir un secteur
    types_literal = RealisationExtraite.model_fields["type"].annotation.__args__
    for t in types_literal:
        assert t in SECTEUR_PAR_TYPE, f"type sans secteur : {t}"
