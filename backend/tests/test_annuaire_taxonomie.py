"""Taxonomie de l'annuaire : regroupement des intitulés ministériels."""

import pytest

from app.annuaire_taxonomie import portefeuille, sigle_fiable, type_institution


@pytest.mark.parametrize(
    "nom,sigle,attendu",
    [
        ("Ministère de la Santé", None, "ministere"),
        # sigle parasite recopié d'une nomination voisine : reste un ministère
        ("Ministère de l'Environnement, de l'Eau et de l'Assainissement", "ONEA", "ministere"),
        ("Présidence du Faso", None, "institution"),
        ("Cour de cassation", None, "juridiction"),
        ("Office national de l'eau et de l'assainissement", "ONEA", "etablissement"),
    ],
)
def test_type_institution(nom, sigle, attendu):
    assert type_institution(nom, sigle) == attendu


def test_sigle_parasite_non_affiche():
    assert not sigle_fiable("Ministère de la Sécurité", "ENEF")
    assert sigle_fiable("École nationale des eaux et forêts", "ENEF")
    assert not sigle_fiable("Ministère de la Santé", None)


@pytest.mark.parametrize(
    "a,b",
    [
        ("Ministère de la Santé", "Ministère de la Santé et de l'Hygiène publique"),
        ("Ministère des Infrastructures", "Ministère des Infrastructures et du Désenclavement"),
        # casse et accents différents d'un intitulé à l'autre
        (
            "Ministère des Affaires étrangères",
            "Ministère des Affaires Étrangères, de la Coopération Régionale "
            "et des Burkinabè de l'Extérieur",
        ),
        (
            "Ministère de l’Administration territoriale et de la mobilité",
            "Ministère de l’Administration territoriale, de la Décentralisation et de la Sécurité",
        ),
    ],
)
def test_intitules_successifs_regroupes(a, b):
    assert portefeuille(a) == portefeuille(b) is not None


@pytest.mark.parametrize(
    "a,b",
    [
        # trois ministères distincts partageant leur mot de tête
        (
            "Ministère de l’Enseignement de base, de l’Alphabétisation",
            "Ministère de l’Enseignement supérieur, de la Recherche et de l’Innovation",
        ),
        (
            "Ministère de l’Enseignement secondaire et de la Formation professionnelle",
            "Ministère de l’Enseignement supérieur, de la Recherche et de l’Innovation",
        ),
        (
            "Ministère de l’Industrie, du Commerce et de l’Artisanat",
            "Ministère du Développement industriel, du Commerce et de l’Artisanat",
        ),
    ],
)
def test_ministeres_distincts_non_regroupes(a, b):
    assert portefeuille(a) != portefeuille(b)


def test_accents_du_mot_de_tete():
    # « Économie » ne doit pas être tronqué en « conomie » par le pliage
    assert portefeuille("Ministère de l'Économie et des Finances") == "economie"
    assert portefeuille("Ministère de l’Énergie, des Mines et des Carrières") == "energie"


def test_portefeuille_hors_ministere():
    assert portefeuille("Cour des comptes") is None
    assert portefeuille(None) is None
