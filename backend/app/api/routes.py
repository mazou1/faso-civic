from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Decision, Document, Mandat, Nomination, Personne, Source, Structure

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

    top_structures = db.execute(
        select(func.coalesce(Structure.sigle, Structure.nom), func.count())
        .join_from(Mandat, Structure)
        .group_by(Structure.id)
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


class MandatOut(BaseModel):
    id: int
    personne: str
    poste: str
    structure: str | None
    date_debut: date | None
    date_fin: date | None
    document_url: str | None


@router.get("/annuaire", response_model=list[MandatOut])
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
                personne=m.personne.nom_complet,
                poste=m.poste,
                structure=str(m.structure) if m.structure else None,
                date_debut=m.date_debut,
                date_fin=m.date_fin,
                document_url=doc.document.url if doc else None,
            )
        )
    return resultats


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


class DocumentOut(BaseModel):
    id: int
    source: str
    url: str
    titre: str | None
    type_doc: str
    date_publication: date | None
    date_collecte: datetime

    @classmethod
    def from_row(cls, d: Document) -> "DocumentOut":
        return cls(
            id=d.id,
            source=d.source.slug,
            url=d.url,
            titre=d.titre,
            type_doc=d.type_doc,
            date_publication=d.date_publication,
            date_collecte=d.date_collecte,
        )


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    source: str | None = None,
    type_doc: str | None = None,
    q: str | None = Query(None, min_length=2, description="Recherche plein texte (français)"),
    page: int = Query(1, ge=1),
    par_page: int = Query(20, ge=1, le=100),
):
    stmt = select(Document).join(Source)
    if source:
        stmt = stmt.where(Source.slug == source)
    if type_doc:
        stmt = stmt.where(Document.type_doc == type_doc)
    if q:
        stmt = stmt.where(text("document.tsv @@ websearch_to_tsquery('french', :q)")).params(q=q)
    stmt = (
        stmt.order_by(Document.date_publication.desc().nulls_last(), Document.id.desc())
        .offset((page - 1) * par_page)
        .limit(par_page)
    )
    return [DocumentOut.from_row(d) for d in db.scalars(stmt).all()]


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


@router.get("/textes", response_model=list[TexteOut])
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
    return resultats


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
    personne: str
    poste: str
    structure: str | None
    date_effet: date | None
    type: str


@router.get("/nominations", response_model=list[NominationOut])
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
    stmt = (
        stmt.order_by(Document.date_publication.desc().nulls_last(), Nomination.id.desc())
        .offset((page - 1) * par_page)
        .limit(par_page)
    )
    return [
        NominationOut(
            id=n.id,
            document_id=n.document_id,
            document_url=n.document.url,
            date_conseil=n.document.date_publication,
            personne=n.personne.nom_complet,
            poste=n.poste,
            structure=str(n.structure) if n.structure else None,
            date_effet=n.date_effet,
            type=n.type,
        )
        for n in db.scalars(stmt).all()
    ]
