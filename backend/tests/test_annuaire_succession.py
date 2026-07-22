"""Identité de siège pour la détection des successions dans l'annuaire."""

import pytest

from app.annuaire_succession import cle_siege


@pytest.mark.parametrize(
    "poste",
    [
        "Administrateur représentant l'État au Conseil d'administration de X",
        "Membre du Conseil d'administration",
        "Conseiller technique",
        "Chargé de mission",
        "Chargée d'études",
        "Inspecteur technique des services",
        "Maître de conférences en Démographie",
    ],
)
def test_postes_collegiaux_sans_succession(poste):
    # plusieurs titulaires coexistent : jamais de clé de siège
    assert cle_siege(poste, structure_unique=True) is None
    assert cle_siege(poste, structure_unique=False) is None


def test_dg_etablissement_suit_le_renommage():
    # cas ANPTIC : le libellé de la structure varie, le siège reste le même
    a = cle_siege("Directeur général de l'Agence nationale pour la promotion des TIC (ANPTIC)")
    b = cle_siege("Directeur général de l'Agence nationale de promotion des TIC")
    assert a == b == "dg"


def test_dg_multiples_sous_un_ministere_ne_collisionnent_pas():
    # un ministère héberge plusieurs directions générales : ne JAMAIS les
    # réduire à une clé commune, sinon elles se fermeraient l'une l'autre
    impots = cle_siege("Directeur général des impôts", structure_unique=False)
    douanes = cle_siege("Directeur général des douanes", structure_unique=False)
    assert impots != douanes
    assert impots and douanes


def test_directions_specifiques_distinctes():
    rh = cle_siege("Directeur des ressources humaines de X")
    fin = cle_siege("Directeur financier et comptable de X")
    assert rh != fin
    # « des ressources humaines » ne doit pas être tronqué en « directeur »
    assert rh != "directeur"


@pytest.mark.parametrize(
    "poste,attendu",
    [
        ("Secrétaire général du ministère de la Santé", "sg"),
        ("Secrétaire général adjoint", "sga"),
        ("Président du Conseil d'administration de l'ANPTIC", "pca"),
        ("Directeur de cabinet du ministre", "dircab"),
        ("Gouverneur de la région du Sahel", "gouverneur"),
        ("Préfet du département de Korsimoro", "prefet"),
        ("Ambassadeur du Burkina Faso à Copenhague", "ambassadeur"),
        ("Directeur général adjoint de la société", "dga"),
    ],
)
def test_roles_sommet(poste, attendu):
    assert cle_siege(poste, structure_unique=True) == attendu
