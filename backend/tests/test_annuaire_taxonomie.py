"""Taxonomie de l'annuaire : regroupement des intitulés ministériels."""

import pytest

from app.annuaire_taxonomie import (
    intitule_officiel,
    portefeuille,
    sigle_fiable,
    type_institution,
)


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


def test_structure_dont_tous_les_mandats_sont_le_ca_du_sigle():
    """Cas SOGEMAB : le nom du ministère a été recopié sur l'entité, pas
    l'inverse. Seule une structure à ~100 % de sièges au CA bascule."""
    nom, sigle = "Ministère de la Guerre et de la Défense patriotique", "SOGEMAB"
    assert type_institution(nom, sigle, part_ca=1.0) == "etablissement"
    assert sigle_fiable(nom, sigle, part_ca=1.0)
    # 62 % = le plus haut ratio des structures qui sont bien des ministères
    assert type_institution(nom, sigle, part_ca=0.62) == "ministere"
    assert type_institution(nom, sigle, part_ca=None) == "ministere"


def test_portefeuille_ignore_une_structure_requalifiee():
    nom = "Ministère de la Guerre et de la Défense patriotique"
    assert portefeuille(nom, type_deduit="etablissement") is None
    assert portefeuille(nom, type_deduit="ministere") == "guerre"


@pytest.mark.parametrize(
    "a,b",
    [
        (
            "Ministère de la Construction de la Patrie",
            "Ministère des Infrastructures et du Désenclavement",
        ),
        (
            "Ministère de la Construction de la Patrie",
            "Ministère de l’Urbanisme, des Affaires foncières et de l’Habitat",
        ),
        (
            "Ministère de l’Industrie, du Commerce et de l’Artisanat",
            "Ministère du Développement industriel, du Commerce et de l’Artisanat",
        ),
        (
            "Ministère des Serviteurs du Peuple",
            "Ministère de la Fonction publique, du Travail et de la Protection sociale",
        ),
        (
            "Ministère de la Famille et de la Solidarité",
            "Ministère de l'Action humanitaire et de la solidarité nationale",
        ),
        (
            "Ministère de la Famille et de la Solidarité",
            "Ministère de la Solidarité, de l’Action humanitaire, de la Réconciliation nationale",
        ),
    ],
)
def test_alias_de_renommage(a, b):
    assert portefeuille(a) == portefeuille(b) is not None


def test_defense_rattachee_a_guerre():
    """Intitulé du gouvernement en vigueur (trombinoscope de janvier 2026)."""
    assert portefeuille("Ministère de la Guerre et de la Défense patriotique") == portefeuille(
        "Ministère de la Défense et des Anciens Combattants"
    )


@pytest.mark.parametrize(
    "poste,attendu",
    [
        (
            "Ministre d'État, Ministre de la Guerre et de la Défense patriotique",
            "Ministère de la Guerre et de la Défense patriotique",
        ),
        ("Ministre de la Justice", "Ministère de la Justice"),
        ("Ministre des Serviteurs du Peuple", "Ministère des Serviteurs du Peuple"),
        (
            "Ministre de la Communication, de la Culture, des Arts et du Tourisme, "
            "Porte-parole du Gouvernement",
            "Ministère de la Communication, de la Culture, des Arts et du Tourisme",
        ),
        # postes qui ne sont pas des ministères de plein exercice
        ("Président du Faso, Chef de l'État", None),
        ("Premier ministre, Chef du Gouvernement", None),
        ("Ministre déléguée auprès du Ministre de l'Économie et des Finances, chargée du Budget", None),
        ("Ministre Secrétaire général du Gouvernement et du Conseil des ministres", None),
        ("Ministre Directeur de Cabinet du Président du Faso", None),
    ],
)
def test_intitule_officiel(poste, attendu):
    assert intitule_officiel(poste) == attendu


@pytest.mark.parametrize(
    "nom,attendu",
    [
        ("Région du Sahel", "territoriale"),
        ("Province du Gourma", "territoriale"),
        ("Département de Korsimoro", "territoriale"),
        ("Commune de Ouagadougou", "territoriale"),
        # noms nus de région (historiques et réforme 2025)
        ("Boucle du Mouhoun", "territoriale"),
        ("Hauts-Bassins", "territoriale"),
        ("Goulmou", "territoriale"),
        # police déconcentrée : AVANT le motif territorial (« … de la Comoé »)
        ("Direction provinciale de la police nationale de la Comoé", "police"),
        ("Direction régionale de la police nationale du Sahel", "police"),
        # diplomatie
        ("Ambassade du Burkina Faso à Berlin", "diplomatique"),
        ("Consulat général du Burkina Faso à Abidjan", "diplomatique"),
        # NE bascule pas : établissement dont le nom contient une région
        ("Agence de l'eau du Nakanbé", "etablissement"),
        ("Centre hospitalier régional de Dori", "etablissement"),
    ],
)
def test_type_territorial_police_diplomatique(nom, attendu):
    assert type_institution(nom) == attendu


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
            "Ministère de la Santé",
            "Ministère de la Sécurité",
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
