from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Document, Source

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
