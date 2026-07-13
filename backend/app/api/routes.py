from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import (
    BudgetExercice,
    Decision,
    Document,
    EngagementFinancier,
    Mandat,
    Nomination,
    Personne,
    Source,
    Structure,
)

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/health")
def health() -> dict:
    db_ok = False
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        pass
    return {"status": "ok" if db_ok else "degraded", "db": db_ok}


@router.get("/stats")
def stats(db: Session = Depends(get_db)) -> dict:
    """Agrégats pour le tableau de bord — contenus validés uniquement."""
    valide_d = Decision.statut_validation == "valide"
    valide_n = Nomination.statut_validation == "valide"
    annee = func.extract("year", Document.date_publication).label("annee")

    par_annee_d = dict(
        db.execute(
            select(annee, func.count()).join_from(Decision, Document).where(valide_d).group_by(annee)
        ).all()
    )
    par_annee_n = dict(
        db.execute(
            select(annee, func.count()).join_from(Nomination, Document).where(valide_n).group_by(annee)
        ).all()
    )
    annees = sorted(set(par_annee_d) | set(par_annee_n))

    par_type = db.execute(
        select(Decision.type, func.count()).where(valide_d).group_by(Decision.type).order_by(func.count().desc())
    ).all()

    # regroupement par structure canonique (fusion des renommages — cf. app/fusion.py)
    from sqlalchemy.orm import aliased

    canon = aliased(Structure)
    top_structures = db.execute(
        select(func.coalesce(canon.sigle, canon.nom), func.count())
        .join_from(Mandat, Structure, Mandat.structure_id == Structure.id)
        .join(canon, canon.id == func.coalesce(Structure.canonique_id, Structure.id))
        .group_by(canon.id)
        .order_by(func.count().desc())
        .limit(10)
    ).all()

    return {
        "totaux": {
            "decisions": db.scalar(select(func.count()).select_from(Decision).where(valide_d)),
            "nominations": db.scalar(select(func.count()).select_from(Nomination).where(valide_n)),
            "personnes": db.scalar(select(func.count(func.distinct(Mandat.personne_id)))),
            "mandats": db.scalar(select(func.count()).select_from(Mandat)),
            "comptes_rendus": db.scalar(
                select(func.count()).select_from(Document).where(Document.type_doc == "cr_conseil")
            ),
        },
        "par_annee": [
            {
                "annee": int(a),
                "decisions": int(par_annee_d.get(a, 0)),
                "nominations": int(par_annee_n.get(a, 0)),
            }
            for a in annees
        ],
        "decisions_par_type": [{"type": t, "n": int(n)} for t, n in par_type],
        "top_structures": [{"structure": s, "mandats": int(n)} for s, n in top_structures],
    }


@router.get("/assemblee")
def assemblee(db: Session = Depends(get_db)) -> dict:
    """Composition de l'Assemblée législative (synchronisée depuis le site officiel)."""
    from app.models import Depute

    deputes = db.scalars(
        select(Depute).where(Depute.actif.is_(True)).order_by(Depute.nom_complet)
    ).all()
    president = next((d for d in deputes if d.role), None)
    return {
        "stats": {
            "deputes": len(deputes),
            "legislature": deputes[0].legislature if deputes else None,
        },
        "president": {
            "nom_complet": president.nom_complet,
            "role": president.role,
            "photo_url": president.photo_url,
        }
        if president
        else None,
        "deputes": [
            {"nom_complet": d.nom_complet, "photo_url": d.photo_url, "role": d.role}
            for d in deputes
        ],
    }


@router.get("/gouvernement")
def gouvernement(db: Session = Depends(get_db)) -> dict:
    """Composition officielle du gouvernement (décret de composition), validée."""
    from app.models import MembreGouvernement

    membres = db.scalars(
        select(MembreGouvernement)
        .where(
            MembreGouvernement.statut_validation == "valide",
            MembreGouvernement.actif.is_(True),
        )
        .order_by(MembreGouvernement.ordre)
    ).all()
    doc = membres[0].document if membres else None
    # ordre -1 = Président du Faso (préside le Conseil, hors effectif gouvernement)
    gouv = [m for m in membres if m.ordre >= 0]
    femmes = sum(1 for m in gouv if m.genre == "F")

    def _sortie(m):
        return {
            "ordre": m.ordre,
            "civilite": m.civilite,
            "nom_complet": m.nom_complet,
            "poste": m.poste,
            "photo_url": m.photo_url,
        }

    return {
        "source": {
            "titre": doc.titre if doc else None,
            "date": doc.date_publication if doc else None,
            "url": doc.url if doc else None,
        },
        "stats": {"membres": len(gouv), "femmes": femmes},
        "president": next((_sortie(m) for m in membres if m.ordre == -1), None),
        "premier_ministre": next((_sortie(m) for m in gouv if m.ordre == 0), None),
        "ministres": [_sortie(m) for m in gouv if m.ordre > 0],
    }


class ActualiteOut(BaseModel):
    id: int
    source: str
    source_nom: str
    titre: str | None
    url: str
    date_publication: date | None
    resume: str | None
    type_doc: str


@router.get("/actualites", response_model=list[ActualiteOut])
def list_actualites(
    db: Session = Depends(get_db),
    source: str | None = Query(None, description="Slug de la source (lefaso, aib, presidence…)"),
    page: int = Query(1, ge=1),
    par_page: int = Query(20, ge=1, le=100),
):
    """Fil d'actualités agrégé : médias burkinabè (RSS) et communiqués officiels."""
    stmt = (
        select(Document)
        .join(Source)
        .where(Document.type_doc.in_(("article_presse", "communique")))
    )
    if source:
        stmt = stmt.where(Source.slug == source)
    stmt = (
        stmt.order_by(Document.date_publication.desc().nulls_last(), Document.id.desc())
        .offset((page - 1) * par_page)
        .limit(par_page)
    )
    resultats = []
    for d in db.scalars(stmt).all():
        resume = (d.meta or {}).get("resume")
        if resume:
            from app.extraction.texte import html_vers_texte

            resume = html_vers_texte(resume)[:280] or None
        resultats.append(
            ActualiteOut(
                id=d.id,
                source=d.source.slug,
                source_nom=d.source.nom,
                titre=d.titre,
                url=d.url,
                date_publication=d.date_publication,
                resume=resume,
                type_doc=d.type_doc,
            )
        )
    return resultats


@router.get("/recherche")
def recherche(
    db: Session = Depends(get_db),
    q: str = Query(..., min_length=2, description="Recherche globale sur tout le site"),
) -> dict:
    """Recherche fédérée : personnes, conseils des ministres, décisions,
    textes juridiques et actualités — top résultats par catégorie."""
    motif = f"%{q}%"

    personnes = db.execute(
        select(Personne.id, Personne.nom_complet, Personne.matricule)
        .where(Personne.nom_complet.ilike(motif))
        .order_by(Personne.nom_complet)
        .limit(8)
    ).all()

    def _docs(types: tuple[str, ...], n: int = 8):
        requete = func.websearch_to_tsquery("french", q)
        return db.execute(
            select(
                Document.id,
                Document.type_doc,
                Document.titre,
                Document.date_publication,
                Document.url,
                Document.meta,
                func.ts_headline(
                    "french",
                    func.coalesce(Document.texte_extrait, Document.titre, ""),
                    requete,
                    "MaxWords=28, MinWords=16, MaxFragments=1",
                ).label("extrait"),
            )
            .where(
                Document.type_doc.in_(types),
                text("document.tsv @@ websearch_to_tsquery('french', :q)"),
            )
            .order_by(
                text("ts_rank(document.tsv, websearch_to_tsquery('french', :q)) desc"),
                Document.date_publication.desc().nulls_last(),
            )
            .limit(n)
            .params(q=q)
        ).all()

    conseils = _docs(("cr_conseil",))
    textes = _docs(TYPES_TEXTES)
    actualites = _docs(("article_presse", "communique"))
    marches = _docs(("marche_public",), n=6)

    decisions = db.execute(
        select(Decision.id, Decision.objet, Decision.ministere, Decision.document_id, Document.date_publication)
        .join(Document)
        .where(
            Decision.statut_validation == "valide",
            Decision.objet.ilike(motif) | Decision.ministere.ilike(motif),
        )
        .order_by(Document.date_publication.desc().nulls_last())
        .limit(8)
    ).all()

    return {
        "q": q,
        "personnes": [
            {"id": p.id, "nom_complet": p.nom_complet, "matricule": p.matricule} for p in personnes
        ],
        "conseils": [
            {"id": d.id, "titre": d.titre, "date": d.date_publication, "extrait": d.extrait}
            for d in conseils
        ],
        "decisions": [
            {
                "id": d.id,
                "objet": d.objet,
                "ministere": d.ministere,
                "document_id": d.document_id,
                "date": d.date_publication,
            }
            for d in decisions
        ],
        "textes": [
            {
                "id": d.id,
                "type_doc": d.type_doc,
                "titre": d.titre,
                "reference": (d.meta or {}).get("reference"),
                "date": d.date_publication,
                "url_pdf": d.url,
                "extrait": d.extrait,
            }
            for d in textes
        ],
        "actualites": [
            {"id": d.id, "titre": d.titre, "date": d.date_publication, "url": d.url, "extrait": d.extrait}
            for d in actualites
        ],
        "marches": [
            {"id": d.id, "titre": d.titre, "date": d.date_publication, "url": d.url, "extrait": d.extrait}
            for d in marches
        ],
    }


class ConseilOut(BaseModel):
    id: int
    titre: str | None
    date_conseil: date | None
    url: str
    decisions: int
    nominations: int
    engagements: int


class ConseilsPage(BaseModel):
    total: int
    conseils: list[ConseilOut]


@router.get("/conseils", response_model=ConseilsPage)
def list_conseils(
    db: Session = Depends(get_db),
    q: str | None = Query(None, min_length=2, description="Recherche dans le titre ou le texte"),
    page: int = Query(1, ge=1),
    par_page: int = Query(20, ge=1, le=100),
):
    """Comptes rendus du Conseil des ministres, avec le volume de contenus validés extraits."""
    n_dec = (
        select(Decision.document_id, func.count().label("n"))
        .where(Decision.statut_validation == "valide")
        .group_by(Decision.document_id)
        .subquery()
    )
    n_nom = (
        select(Nomination.document_id, func.count().label("n"))
        .where(Nomination.statut_validation == "valide")
        .group_by(Nomination.document_id)
        .subquery()
    )
    n_eng = (
        select(EngagementFinancier.document_id, func.count().label("n"))
        .where(EngagementFinancier.statut_validation == "valide")
        .group_by(EngagementFinancier.document_id)
        .subquery()
    )
    base = (
        select(Document, n_dec.c.n, n_nom.c.n, n_eng.c.n)
        .outerjoin(n_dec, n_dec.c.document_id == Document.id)
        .outerjoin(n_nom, n_nom.c.document_id == Document.id)
        .outerjoin(n_eng, n_eng.c.document_id == Document.id)
        .where(
            Document.type_doc == "cr_conseil",
            # une entrée par conseil : on écarte les coquilles sans contenu extrait
            (n_dec.c.n.is_not(None)) | (n_nom.c.n.is_not(None)) | (n_eng.c.n.is_not(None)),
        )
    )
    if q:
        base = base.where(Document.titre.ilike(f"%{q}%") | Document.texte_extrait.ilike(f"%{q}%"))
    total = db.scalar(select(func.count()).select_from(base.subquery()))
    lignes = db.execute(
        base.order_by(Document.date_publication.desc().nulls_last(), Document.id.desc())
        .offset((page - 1) * par_page)
        .limit(par_page)
    ).all()
    return ConseilsPage(
        total=int(total or 0),
        conseils=[
            ConseilOut(
                id=d.id,
                titre=d.titre,
                date_conseil=d.date_publication,
                url=d.url,
                decisions=int(nd or 0),
                nominations=int(nn or 0),
                engagements=int(ne or 0),
            )
            for d, nd, nn, ne in lignes
        ],
    )


@router.get("/conseils/{doc_id}")
def get_conseil(doc_id: int, db: Session = Depends(get_db)) -> dict:
    """Un conseil des ministres et tout son contenu validé, traçable."""
    d = db.get(Document, doc_id)
    if d is None or d.type_doc != "cr_conseil":
        raise HTTPException(404, "Compte rendu introuvable")
    decisions = db.scalars(
        select(Decision)
        .where(Decision.document_id == doc_id, Decision.statut_validation == "valide")
        .order_by(Decision.id)
    ).all()
    nominations = db.scalars(
        select(Nomination)
        .where(Nomination.document_id == doc_id, Nomination.statut_validation == "valide")
        .order_by(Nomination.id)
    ).all()
    engagements = db.scalars(
        select(EngagementFinancier)
        .where(
            EngagementFinancier.document_id == doc_id,
            EngagementFinancier.statut_validation == "valide",
        )
        .order_by(EngagementFinancier.montant_fcfa.desc().nulls_last())
    ).all()
    return {
        "id": d.id,
        "titre": d.titre,
        "date_conseil": d.date_publication,
        "url": d.url,
        "texte": d.texte_extrait,
        "pdf": bool(d.fichier and d.mime == "application/pdf"),
        "decisions": [
            {"id": x.id, "ministere": x.ministere, "type": x.type, "objet": x.objet}
            for x in decisions
        ],
        "nominations": [
            {
                "id": x.id,
                "personne": x.personne.nom_complet,
                "poste": x.poste,
                "structure": str(x.structure) if x.structure else None,
                "type": x.type,
            }
            for x in nominations
        ],
        "engagements": [
            {
                "id": x.id,
                "type": x.type,
                "objet": x.objet,
                "beneficiaire": x.beneficiaire,
                "montant_fcfa": x.montant_fcfa,
            }
            for x in engagements
        ],
    }


@router.get("/finances/stats")
def finances_stats(db: Session = Depends(get_db)) -> dict:
    """Agrégats financiers — engagements et budgets validés uniquement."""
    valide = EngagementFinancier.statut_validation == "valide"
    annee = func.extract("year", Document.date_publication).label("annee")

    par_annee = db.execute(
        select(annee, func.count(), func.sum(EngagementFinancier.montant_fcfa))
        .join_from(EngagementFinancier, Document)
        .where(valide)
        .group_by(annee)
        .order_by(annee)
    ).all()
    par_type = db.execute(
        select(EngagementFinancier.type, func.count(), func.sum(EngagementFinancier.montant_fcfa))
        .where(valide)
        .group_by(EngagementFinancier.type)
        .order_by(func.sum(EngagementFinancier.montant_fcfa).desc())
    ).all()
    par_ministere = db.execute(
        select(EngagementFinancier.ministere, func.sum(EngagementFinancier.montant_fcfa))
        .where(valide, EngagementFinancier.ministere.is_not(None))
        .group_by(EngagementFinancier.ministere)
        .order_by(func.sum(EngagementFinancier.montant_fcfa).desc())
        .limit(10)
    ).all()
    budgets = db.scalars(
        select(BudgetExercice)
        .where(
            BudgetExercice.statut_validation == "valide",
            BudgetExercice.recettes_fcfa.is_not(None)
            | BudgetExercice.depenses_fcfa.is_not(None),
        )
        .order_by(BudgetExercice.exercice, BudgetExercice.id)
    ).all()
    from app.models import DotationBudgetaire, RepartitionBudgetaire

    dotations = db.execute(
        select(
            DotationBudgetaire.exercice,
            DotationBudgetaire.ministere,
            DotationBudgetaire.montant_fcfa,
            DotationBudgetaire.source_libre,
        )
        .where(DotationBudgetaire.statut_validation == "valide")
        .order_by(DotationBudgetaire.exercice.desc(), DotationBudgetaire.montant_fcfa.desc())
    ).all()
    repartitions = db.execute(
        select(
            RepartitionBudgetaire.exercice,
            RepartitionBudgetaire.sens,
            RepartitionBudgetaire.libelle,
            RepartitionBudgetaire.montant_fcfa,
            RepartitionBudgetaire.source_libre,
        )
        .where(RepartitionBudgetaire.statut_validation == "valide")
        .order_by(RepartitionBudgetaire.exercice.desc(), RepartitionBudgetaire.montant_fcfa.desc())
    ).all()

    return {
        "totaux": {
            "engagements": db.scalar(
                select(func.count()).select_from(EngagementFinancier).where(valide)
            ),
            "montant_total_fcfa": int(
                db.scalar(select(func.sum(EngagementFinancier.montant_fcfa)).where(valide)) or 0
            ),
        },
        "par_annee": [
            {"annee": int(a), "engagements": int(n), "montant_fcfa": int(m or 0)}
            for a, n, m in par_annee
        ],
        "par_type": [
            {"type": t, "engagements": int(n), "montant_fcfa": int(m or 0)} for t, n, m in par_type
        ],
        "par_ministere": [
            {"ministere": mi, "montant_fcfa": int(m or 0)} for mi, m in par_ministere
        ],
        "budgets": [
            {
                "exercice": b.exercice,
                "type_loi": b.type_loi,
                "recettes_fcfa": b.recettes_fcfa,
                "depenses_fcfa": b.depenses_fcfa,
            }
            for b in budgets
        ],
        "dotations": [
            {"exercice": ex, "ministere": mi, "montant_fcfa": int(m), "source": src}
            for ex, mi, m, src in dotations
        ],
        "repartitions": [
            {"exercice": ex, "sens": s, "libelle": l, "montant_fcfa": int(m), "source": src}
            for ex, s, l, m, src in repartitions
        ],
    }


class EngagementOut(BaseModel):
    id: int
    document_url: str
    date_conseil: date | None
    ministere: str | None
    type: str
    objet: str
    beneficiaire: str | None
    montant_fcfa: int | None


@router.get("/finances/engagements", response_model=list[EngagementOut])
def list_engagements(
    db: Session = Depends(get_db),
    type: str | None = None,
    q: str | None = Query(None, min_length=2, description="Filtre sur objet/bénéficiaire/ministère"),
    tri: str = Query("montant", description="montant | date"),
    page: int = Query(1, ge=1),
    par_page: int = Query(20, ge=1, le=100),
):
    """Engagements financiers décidés en Conseil des ministres — validés uniquement."""
    stmt = (
        select(EngagementFinancier)
        .join(Document)
        .where(EngagementFinancier.statut_validation == "valide")
    )
    if type:
        stmt = stmt.where(EngagementFinancier.type == type)
    if q:
        motif = f"%{q}%"
        stmt = stmt.where(
            EngagementFinancier.objet.ilike(motif)
            | EngagementFinancier.beneficiaire.ilike(motif)
            | EngagementFinancier.ministere.ilike(motif)
        )
    if tri == "date":
        stmt = stmt.order_by(Document.date_publication.desc().nulls_last(), EngagementFinancier.id.desc())
    else:
        stmt = stmt.order_by(EngagementFinancier.montant_fcfa.desc().nulls_last())
    stmt = stmt.offset((page - 1) * par_page).limit(par_page)
    return [
        EngagementOut(
            id=e.id,
            document_url=e.document.url,
            date_conseil=e.document.date_publication,
            ministere=e.ministere,
            type=e.type,
            objet=e.objet,
            beneficiaire=e.beneficiaire,
            montant_fcfa=e.montant_fcfa,
        )
        for e in db.scalars(stmt).all()
    ]


class MandatOut(BaseModel):
    id: int
    personne_id: int
    personne: str
    matricule: str | None
    poste: str
    structure: str | None
    date_debut: date | None
    date_fin: date | None
    document_url: str | None


class AnnuairePage(BaseModel):
    total: int
    mandats: list[MandatOut]


@router.get("/annuaire", response_model=AnnuairePage)
def annuaire(
    db: Session = Depends(get_db),
    q: str | None = Query(None, min_length=2, description="Nom de personne ou de structure"),
    en_cours: bool = Query(False, description="Seulement les mandats sans date de fin"),
    page: int = Query(1, ge=1),
    par_page: int = Query(25, ge=1, le=100),
):
    """Annuaire de l'État : mandats issus des nominations validées."""
    stmt = select(Mandat).join(Personne).outerjoin(Structure)
    if q:
        motif = f"%{q}%"
        stmt = stmt.where(
            Personne.nom_complet.ilike(motif)
            | Structure.nom.ilike(motif)
            | Structure.sigle.ilike(motif)
            | Mandat.poste.ilike(motif)
        )
    if en_cours:
        stmt = stmt.where(Mandat.date_fin.is_(None))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    stmt = (
        stmt.order_by(Mandat.date_debut.desc().nulls_last(), Mandat.id.desc())
        .offset((page - 1) * par_page)
        .limit(par_page)
    )
    resultats = []
    for m in db.scalars(stmt).all():
        doc = m.nomination_debut_id and db.get(Nomination, m.nomination_debut_id)
        resultats.append(
            MandatOut(
                id=m.id,
                personne_id=m.personne_id,
                personne=m.personne.nom_complet,
                matricule=m.personne.matricule,
                poste=m.poste,
                structure=str(m.structure) if m.structure else None,
                date_debut=m.date_debut,
                date_fin=m.date_fin,
                document_url=doc.document.url if doc else None,
            )
        )
    return AnnuairePage(total=int(total or 0), mandats=resultats)


class FichePersonne(BaseModel):
    id: int
    nom_complet: str
    matricule: str | None
    en_fonction: bool
    fonctions: list[dict]
    homonymes: list[dict]


@router.get("/personnes/{personne_id}", response_model=FichePersonne)
def fiche_personne(personne_id: int, db: Session = Depends(get_db)):
    """Fiche d'une personnalité publique : son parcours de fonctions, chaque
    entrée reliée au compte rendu de nomination."""
    p = db.get(Personne, personne_id)
    if p is None:
        raise HTTPException(404, "Personne introuvable")
    homonymes = [
        {"id": h.id, "matricule": h.matricule}
        for h in db.scalars(
            select(Personne).where(
                Personne.nom_normalise == p.nom_normalise, Personne.id != p.id
            )
        ).all()
    ]
    mandats = db.scalars(
        select(Mandat)
        .where(Mandat.personne_id == personne_id)
        .order_by(Mandat.date_fin.is_(None).desc(), Mandat.date_debut.desc().nulls_last())
    ).all()
    fonctions = []
    for m in mandats:
        nom_deb = m.nomination_debut_id and db.get(Nomination, m.nomination_debut_id)
        doc = nom_deb.document if nom_deb else None
        fonctions.append(
            {
                "poste": m.poste,
                "structure": str(m.structure) if m.structure else None,
                "date_debut": m.date_debut.isoformat() if m.date_debut else None,
                "date_fin": m.date_fin.isoformat() if m.date_fin else None,
                "nomination_id": m.nomination_debut_id,
                "source_titre": doc.titre if doc else None,
                "source_url": doc.url if doc else None,
                "source_id": doc.id if doc and doc.type_doc == "cr_conseil" else None,
            }
        )
    return FichePersonne(
        id=p.id,
        nom_complet=p.nom_complet,
        matricule=p.matricule,
        en_fonction=any(m.date_fin is None for m in mandats),
        fonctions=fonctions,
        homonymes=homonymes,
    )


class SourceOut(BaseModel):
    slug: str
    nom: str
    url_base: str
    type: str
    cadence: str
    actif: bool

    model_config = {"from_attributes": True}


@router.get("/sources", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db)):
    return db.scalars(select(Source).order_by(Source.slug)).all()


@router.get("/sources/etat")
def sources_etat(db: Session = Depends(get_db)) -> dict:
    """Fraîcheur des collectes : sources muettes (rien collecté depuis trop
    longtemps au regard de leur cadence) et date du dernier run réussi."""
    from app.ingestion.surveillance import etat_sources

    etats = etat_sources(db)
    return {"muettes": sum(1 for e in etats if e["muette"]), "sources": etats}


class DocumentOut(BaseModel):
    id: int
    source: str
    source_nom: str | None = None
    url: str
    titre: str | None
    type_doc: str
    date_publication: date | None
    date_collecte: datetime
    pdf: bool = False

    @classmethod
    def from_row(cls, d: Document) -> "DocumentOut":
        return cls(
            id=d.id,
            source=d.source.slug,
            source_nom=d.source.nom,
            url=d.url,
            titre=d.titre,
            type_doc=d.type_doc,
            date_publication=d.date_publication,
            date_collecte=d.date_collecte,
            pdf=bool(d.fichier and d.mime == "application/pdf"),
        )


class DocumentsPage(BaseModel):
    total: int
    documents: list[DocumentOut]
    types: list[dict]
    sources: list[dict]


@router.get("/documents", response_model=DocumentsPage)
def list_documents(
    db: Session = Depends(get_db),
    source: str | None = None,
    type_doc: str | None = None,
    q: str | None = Query(None, min_length=2, description="Recherche plein texte (français)"),
    page: int = Query(1, ge=1),
    par_page: int = Query(20, ge=1, le=100),
):
    """Bibliothèque de tous les documents archivés, avec facettes types/sources."""

    def _filtre(stmt, avec_source=True, avec_type=True):
        if source and avec_source:
            stmt = stmt.where(Source.slug == source)
        if type_doc and avec_type:
            stmt = stmt.where(Document.type_doc == type_doc)
        if q:
            stmt = stmt.where(
                text("document.tsv @@ websearch_to_tsquery('french', :q)")
            ).params(q=q)
        return stmt

    base = _filtre(select(Document).join(Source))
    total = db.scalar(select(func.count()).select_from(base.subquery()))
    docs = db.scalars(
        base.order_by(Document.date_publication.desc().nulls_last(), Document.id.desc())
        .offset((page - 1) * par_page)
        .limit(par_page)
    ).all()

    # facettes : chaque dimension est comptée sous les AUTRES filtres actifs
    types = db.execute(
        _filtre(
            select(Document.type_doc, func.count()).join(Source), avec_type=False
        ).group_by(Document.type_doc).order_by(func.count().desc())
    ).all()
    sources = db.execute(
        _filtre(
            select(Source.slug, Source.nom, func.count()).join_from(Document, Source),
            avec_source=False,
        ).group_by(Source.slug, Source.nom).order_by(func.count().desc())
    ).all()

    return DocumentsPage(
        total=int(total or 0),
        documents=[DocumentOut.from_row(d) for d in docs],
        types=[{"type_doc": t, "n": int(n)} for t, n in types],
        sources=[{"slug": s, "nom": nom, "n": int(n)} for s, nom, n in sources],
    )


class DocumentDetail(DocumentOut):
    texte_extrait: str | None
    statut_extraction: str
    meta: dict | None


@router.get("/documents/{doc_id}", response_model=DocumentDetail)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    d = db.get(Document, doc_id)
    if d is None:
        raise HTTPException(404, "Document introuvable")
    base = DocumentOut.from_row(d).model_dump()
    return DocumentDetail(
        **base,
        texte_extrait=d.texte_extrait,
        statut_extraction=d.statut_extraction,
        meta=d.meta,
    )


@router.get("/contexte/{genre}/{entite_id}")
def contexte(genre: str, entite_id: int, db: Session = Depends(get_db)) -> dict:
    """« La source en contexte » : la phrase du compte rendu d'où provient une
    nomination ou un engagement, avec les ancres surlignées (<mark>)."""
    from app.extraction.contexte import localiser

    if genre == "nomination":
        n = db.get(Nomination, entite_id)
        if n is None:
            raise HTTPException(404, "Nomination introuvable")
        doc = n.document
        ancres = [(n.matricule or "", True), (n.personne.nom_complet, False)]
    elif genre == "engagement":
        e = db.get(EngagementFinancier, entite_id)
        if e is None:
            raise HTTPException(404, "Engagement introuvable")
        doc = e.document
        ancres = [(e.beneficiaire or "", False)]
    else:
        raise HTTPException(404, "Type de contexte inconnu")

    return {
        "passage": localiser(doc.texte_extrait, ancres),
        "document": {"id": doc.id, "titre": doc.titre, "url": doc.url},
    }


@router.get("/documents/{doc_id}/fichier")
def get_document_fichier(doc_id: int, db: Session = Depends(get_db)):
    """Sert le fichier archivé d'un document (PDF officiel téléchargé à la collecte)."""
    from fastapi.responses import FileResponse

    from app.config import settings

    d = db.get(Document, doc_id)
    if d is None or not d.fichier:
        raise HTTPException(404, "Fichier introuvable")
    chemin = settings.data_dir / d.fichier
    if not chemin.is_file():
        raise HTTPException(404, "Fichier absent de l'archive")
    nom = f"{(d.titre or 'document').strip()[:80]}.pdf" if d.mime == "application/pdf" else chemin.name
    return FileResponse(chemin, media_type=d.mime or "application/octet-stream", filename=nom)


TYPES_TEXTES = ("decret", "loi", "arrete", "ordonnance", "charte", "constitution", "texte_juridique")


class TexteOut(BaseModel):
    id: int
    type_doc: str
    titre: str | None
    reference: str | None
    date_publication: date | None
    secteur: str | None
    description: str | None
    url_pdf: str
    jo_numero: str | None
    jo_url: str | None


class TextesPage(BaseModel):
    total: int
    textes: list[TexteOut]


@router.get("/textes", response_model=TextesPage)
def list_textes(
    db: Session = Depends(get_db),
    q: str | None = Query(None, min_length=2, description="Recherche plein texte (français)"),
    type: str | None = Query(None, description="decret | loi | arrete | ordonnance | charte | constitution"),
    page: int = Query(1, ge=1),
    par_page: int = Query(20, ge=1, le=100),
):
    """Textes juridiques (Légiburkina) : décrets, lois, arrêtés… avec lien PDF et Journal officiel."""
    stmt = select(Document).where(Document.type_doc.in_(TYPES_TEXTES))
    if type:
        stmt = stmt.where(Document.type_doc == type)
    if q:
        stmt = stmt.where(text("document.tsv @@ websearch_to_tsquery('french', :q)")).params(q=q)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    stmt = (
        stmt.order_by(Document.date_publication.desc().nulls_last(), Document.id.desc())
        .offset((page - 1) * par_page)
        .limit(par_page)
    )
    resultats = []
    for d in db.scalars(stmt).all():
        meta = d.meta or {}
        # après téléchargement du PDF, texte_extrait contient le texte intégral ;
        # la description courte d'origine est préservée dans meta['description']
        description = meta.get("description") or d.texte_extrait
        resultats.append(
            TexteOut(
                id=d.id,
                type_doc=d.type_doc,
                titre=d.titre,
                reference=meta.get("reference"),
                date_publication=d.date_publication,
                secteur=meta.get("secteur"),
                description=(description[:600] if description else None),
                url_pdf=d.url,
                jo_numero=meta.get("jo_numero"),
                jo_url=meta.get("jo_url"),
            )
        )
    return TextesPage(total=int(total or 0), textes=resultats)


class DecisionOut(BaseModel):
    id: int
    document_id: int
    document_url: str
    date_conseil: date | None
    ministere: str | None
    type: str
    objet: str


@router.get("/decisions", response_model=list[DecisionOut])
def list_decisions(
    db: Session = Depends(get_db),
    ministere: str | None = Query(None, description="Filtre contient, insensible à la casse"),
    type: str | None = None,
    page: int = Query(1, ge=1),
    par_page: int = Query(20, ge=1, le=100),
):
    """Décisions du Conseil des ministres — contenus validés uniquement."""
    stmt = (
        select(Decision)
        .join(Document)
        .where(Decision.statut_validation == "valide")
    )
    if ministere:
        stmt = stmt.where(Decision.ministere.ilike(f"%{ministere}%"))
    if type:
        stmt = stmt.where(Decision.type == type)
    stmt = (
        stmt.order_by(Document.date_publication.desc().nulls_last(), Decision.id.desc())
        .offset((page - 1) * par_page)
        .limit(par_page)
    )
    return [
        DecisionOut(
            id=d.id,
            document_id=d.document_id,
            document_url=d.document.url,
            date_conseil=d.document.date_publication,
            ministere=d.ministere,
            type=d.type,
            objet=d.objet,
        )
        for d in db.scalars(stmt).all()
    ]


class NominationOut(BaseModel):
    id: int
    document_id: int
    document_url: str
    date_conseil: date | None
    personne_id: int
    personne: str
    poste: str
    structure: str | None
    date_effet: date | None
    type: str


class NominationsPage(BaseModel):
    total: int
    nominations: list[NominationOut]


@router.get("/nominations", response_model=NominationsPage)
def list_nominations(
    db: Session = Depends(get_db),
    q: str | None = Query(None, description="Recherche sur le nom de la personne"),
    page: int = Query(1, ge=1),
    par_page: int = Query(20, ge=1, le=100),
):
    """Nominations en Conseil des ministres — contenus validés uniquement."""
    stmt = (
        select(Nomination)
        .join(Document)
        .where(Nomination.statut_validation == "valide")
    )
    if q:
        from app.models import Personne

        stmt = stmt.join(Personne).where(Personne.nom_complet.ilike(f"%{q}%"))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    stmt = (
        stmt.order_by(Document.date_publication.desc().nulls_last(), Nomination.id.desc())
        .offset((page - 1) * par_page)
        .limit(par_page)
    )
    return NominationsPage(
        total=int(total or 0),
        nominations=[
            NominationOut(
                id=n.id,
                document_id=n.document_id,
                document_url=n.document.url,
                date_conseil=n.document.date_publication,
                personne_id=n.personne_id,
                personne=n.personne.nom_complet,
                poste=n.poste,
                structure=str(n.structure) if n.structure else None,
                date_effet=n.date_effet,
                type=n.type,
            )
            for n in db.scalars(stmt).all()
        ],
    )


# ── Export open data (CSV) ────────────────────────────────────────────────
# Les jeux de données validés, téléchargeables en CSV pour réutilisation
# (journalistes, chercheurs, société civile). Une ligne = un fait sourcé.

def _csv(colonnes: list[str], lignes) -> "StreamingResponse":
    import csv
    import io

    from fastapi.responses import StreamingResponse

    def flux():
        tampon = io.StringIO()
        w = csv.writer(tampon)
        w.writerow(colonnes)
        yield tampon.getvalue()
        for ligne in lignes:
            tampon.seek(0)
            tampon.truncate(0)
            w.writerow(ligne)
            yield tampon.getvalue()

    return StreamingResponse(flux(), media_type="text/csv; charset=utf-8")


@router.get("/export/nominations.csv")
def export_nominations(db: Session = Depends(get_db)):
    """Toutes les nominations validées, avec leur compte rendu source."""
    stmt = (
        select(Nomination)
        .join(Document)
        .where(Nomination.statut_validation == "valide")
        .order_by(Document.date_publication.desc().nulls_last(), Nomination.id.desc())
    )
    lignes = (
        (
            n.id,
            n.personne.nom_complet,
            n.personne.matricule or "",
            n.poste,
            str(n.structure) if n.structure else "",
            "fin de fonction" if n.type == "fin_fonction" else "nomination",
            n.document.date_publication.isoformat() if n.document.date_publication else "",
            n.document.url,
        )
        for n in db.scalars(stmt).all()
    )
    return _csv(
        ["id", "personne", "matricule", "poste", "structure", "type", "date_conseil", "source_url"],
        lignes,
    )


@router.get("/export/engagements.csv")
def export_engagements(db: Session = Depends(get_db)):
    """Engagements financiers validés du Conseil des ministres."""
    stmt = (
        select(EngagementFinancier)
        .join(Document)
        .where(EngagementFinancier.statut_validation == "valide")
        .order_by(EngagementFinancier.montant_fcfa.desc().nulls_last())
    )
    lignes = (
        (
            e.id,
            e.type,
            e.objet,
            e.beneficiaire or "",
            e.ministere or "",
            e.montant_fcfa if e.montant_fcfa is not None else "",
            e.document.date_publication.isoformat() if e.document.date_publication else "",
            e.document.url,
        )
        for e in db.scalars(stmt).all()
    )
    return _csv(
        ["id", "type", "objet", "beneficiaire", "ministere", "montant_fcfa", "date_conseil", "source_url"],
        lignes,
    )


@router.get("/export/decisions.csv")
def export_decisions(db: Session = Depends(get_db)):
    """Décisions validées du Conseil des ministres."""
    stmt = (
        select(Decision)
        .join(Document)
        .where(Decision.statut_validation == "valide")
        .order_by(Document.date_publication.desc().nulls_last(), Decision.id.desc())
    )
    lignes = (
        (
            d.id,
            d.type,
            d.ministere or "",
            d.objet,
            d.document.date_publication.isoformat() if d.document.date_publication else "",
            d.document.url,
        )
        for d in db.scalars(stmt).all()
    )
    return _csv(["id", "type", "ministere", "objet", "date_conseil", "source_url"], lignes)


@router.get("/export/textes.csv")
def export_textes(db: Session = Depends(get_db)):
    """Textes juridiques (Légiburkina) : décrets, lois, arrêtés…"""
    stmt = (
        select(Document)
        .where(Document.type_doc.in_(TYPES_TEXTES))
        .order_by(Document.date_publication.desc().nulls_last(), Document.id.desc())
    )
    lignes = (
        (
            d.id,
            d.type_doc,
            (d.meta or {}).get("reference", ""),
            d.titre or "",
            d.date_publication.isoformat() if d.date_publication else "",
            (d.meta or {}).get("jo_numero", ""),
            d.url,
        )
        for d in db.scalars(stmt).all()
    )
    return _csv(["id", "type", "reference", "titre", "date", "journal_officiel", "url_pdf"], lignes)


@router.get("/export/annuaire.csv")
def export_annuaire(db: Session = Depends(get_db)):
    """Annuaire de l'État : mandats consolidés."""
    stmt = select(Mandat).join(Personne).outerjoin(Structure).order_by(
        Mandat.date_debut.desc().nulls_last(), Mandat.id.desc()
    )
    lignes = (
        (
            m.id,
            m.personne.nom_complet,
            m.personne.matricule or "",
            m.poste,
            str(m.structure) if m.structure else "",
            m.date_debut.isoformat() if m.date_debut else "",
            m.date_fin.isoformat() if m.date_fin else "",
            "en cours" if m.date_fin is None else "terminé",
        )
        for m in db.scalars(stmt).all()
    )
    return _csv(
        ["id", "personne", "matricule", "poste", "structure", "date_debut", "date_fin", "statut"],
        lignes,
    )


# ── Flux RSS ──────────────────────────────────────────────────────────────
# Suivre les nouvelles publications dans un lecteur de flux, sans compte.

@router.get("/rss/conseils.xml")
def rss_conseils(request: Request, db: Session = Depends(get_db)):
    from fastapi.responses import Response

    from app.api.rss import flux_rss

    base = str(request.base_url).rstrip("/").removesuffix("/api")
    docs = db.scalars(
        select(Document)
        .where(Document.type_doc == "cr_conseil")
        .order_by(Document.date_publication.desc().nulls_last(), Document.id.desc())
        .limit(30)
    ).all()
    items = [
        {
            "titre": d.titre or "Conseil des ministres",
            "lien": f"{base}/conseils/{d.id}",
            "guid": f"conseil-{d.id}",
            "date": d.date_publication,
        }
        for d in docs
    ]
    xml = flux_rss(
        request,
        titre="FasoCivic — Conseils des ministres",
        description="Les comptes rendus du Conseil des ministres du Burkina Faso.",
        chemin="/rss/conseils.xml",
        items=items,
    )
    return Response(xml, media_type="application/rss+xml; charset=utf-8")


@router.get("/rss/actualites.xml")
def rss_actualites(request: Request, db: Session = Depends(get_db)):
    from fastapi.responses import Response

    from app.api.rss import flux_rss
    from app.extraction.texte import html_vers_texte

    docs = db.scalars(
        select(Document)
        .where(Document.type_doc.in_(("article_presse", "communique")))
        .order_by(Document.date_publication.desc().nulls_last(), Document.id.desc())
        .limit(40)
    ).all()
    items = []
    for d in docs:
        resume = (d.meta or {}).get("resume")
        items.append(
            {
                "titre": d.titre or d.source.nom,
                "lien": d.url,  # l'article renvoie à sa source d'origine
                "guid": f"actu-{d.id}",
                "description": (html_vers_texte(resume)[:280] if resume else None),
                "date": d.date_publication,
            }
        )
    xml = flux_rss(
        request,
        titre="FasoCivic — Actualités",
        description="Le fil d'actualités agrégé : médias burkinabè et communiqués officiels.",
        chemin="/rss/actualites.xml",
        items=items,
    )
    return Response(xml, media_type="application/rss+xml; charset=utf-8")


@router.get("/rss/textes.xml")
def rss_textes(request: Request, db: Session = Depends(get_db)):
    from fastapi.responses import Response

    from app.api.rss import flux_rss

    docs = db.scalars(
        select(Document)
        .where(Document.type_doc.in_(TYPES_TEXTES))
        .order_by(Document.date_publication.desc().nulls_last(), Document.id.desc())
        .limit(30)
    ).all()
    items = [
        {
            "titre": ((d.meta or {}).get("reference") or d.titre or "Texte juridique"),
            "lien": d.url,
            "guid": f"texte-{d.id}",
            "description": ((d.meta or {}).get("description") or None),
            "date": d.date_publication,
        }
        for d in docs
    ]
    xml = flux_rss(
        request,
        titre="FasoCivic — Lois & décrets",
        description="Les nouveaux textes juridiques publiés (Légiburkina).",
        chemin="/rss/textes.xml",
        items=items,
    )
    return Response(xml, media_type="application/rss+xml; charset=utf-8")
