"""Modèle de données — cf. cadrage-plateforme-civique-v2.md §4.

Tout gravite autour du `Document` source ; les entités structurées
(nominations, mandats…) y sont rattachées pour garantir la traçabilité.
Les champs "type"/"statut" sont des chaînes libres documentées ici plutôt
que des enums PG natifs, pour garder les migrations légères.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Source(Base):
    __tablename__ = "source"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True)
    nom: Mapped[str] = mapped_column(String(200))
    url_base: Mapped[str] = mapped_column(String(500))
    type: Mapped[str] = mapped_column(String(50))  # institutionnel | media | open_data
    cadence: Mapped[str] = mapped_column(String(50), default="quotidien")
    licence: Mapped[str | None] = mapped_column(String(200))
    actif: Mapped[bool] = mapped_column(Boolean, default=True)

    documents: Mapped[list[Document]] = relationship(back_populates="source")

    def __str__(self) -> str:
        return self.slug


class Document(Base):
    __tablename__ = "document"
    __table_args__ = (
        UniqueConstraint("source_id", "url", "hash_contenu", name="uq_document_source_url_hash"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"))
    url: Mapped[str] = mapped_column(String(1000), index=True)
    titre: Mapped[str | None] = mapped_column(String(1000))
    # cr_conseil | decret | arrete | loi | communique | decision | rapport | marche | article_presse
    type_doc: Mapped[str] = mapped_column(String(50), index=True)
    date_publication: Mapped[date | None] = mapped_column(Date, index=True)
    date_collecte: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    hash_contenu: Mapped[str | None] = mapped_column(String(64), index=True)
    fichier: Mapped[str | None] = mapped_column(String(500))  # chemin relatif dans DATA_DIR
    mime: Mapped[str | None] = mapped_column(String(100))
    texte_extrait: Mapped[str | None] = mapped_column(Text)
    # en_attente | ok | ocr | echec | na (na = métadonnées seules, rien à extraire)
    statut_extraction: Mapped[str] = mapped_column(String(20), default="en_attente")
    # renseignée quand l'étage de structuration LLM (nominations/décisions) est passé
    date_structuration: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    meta: Mapped[dict | None] = mapped_column(JSONB)
    # NB : colonne `tsv` (tsvector générée, index GIN) créée en SQL brut dans la
    # migration initiale — volontairement non mappée dans l'ORM.

    source: Mapped[Source] = relationship(back_populates="documents")

    def __str__(self) -> str:
        return f"[{self.type_doc}] {self.titre or self.url}"


class Personne(Base):
    __tablename__ = "personne"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom_complet: Mapped[str] = mapped_column(String(300))
    nom_normalise: Mapped[str] = mapped_column(String(300), index=True)
    notes: Mapped[str | None] = mapped_column(Text)

    def __str__(self) -> str:
        return self.nom_complet


class Structure(Base):
    __tablename__ = "structure"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(500))
    sigle: Mapped[str | None] = mapped_column(String(50), index=True)
    # ministere | direction | societe_etat | etablissement_public | juridiction | autre
    type: Mapped[str] = mapped_column(String(50), default="autre")
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("structure.id"))
    # fusion des doublons/renommages : pointe vers la structure canonique
    # (les stats regroupent par coalesce(canonique_id, id)) — cf. app/fusion.py
    canonique_id: Mapped[int | None] = mapped_column(ForeignKey("structure.id"), index=True)

    parent: Mapped[Structure | None] = relationship(
        remote_side=[id], foreign_keys=[parent_id]
    )
    canonique: Mapped[Structure | None] = relationship(
        remote_side=[id], foreign_keys=[canonique_id]
    )

    def __str__(self) -> str:
        return self.sigle or self.nom


class Nomination(Base):
    """Fait brut extrait d'un document (CR du Conseil des ministres, décret…)."""

    __tablename__ = "nomination"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("document.id"))
    personne_id: Mapped[int] = mapped_column(ForeignKey("personne.id"))
    structure_id: Mapped[int | None] = mapped_column(ForeignKey("structure.id"))
    poste: Mapped[str] = mapped_column(String(500))
    date_effet: Mapped[date | None] = mapped_column(Date)
    type: Mapped[str] = mapped_column(String(20), default="nomination")  # nomination | fin_fonction
    score_confiance: Mapped[float | None] = mapped_column(Float)
    # a_valider | valide | rejete — l'extraction automatique ne publie jamais seule
    statut_validation: Mapped[str] = mapped_column(String(20), default="a_valider", index=True)

    document: Mapped[Document] = relationship()
    personne: Mapped[Personne] = relationship()
    structure: Mapped[Structure | None] = relationship()


class Decision(Base):
    """Mesure prise en Conseil des ministres (hors nominations individuelles) :
    adoption de décret, rapport, communication, autorisation…"""

    __tablename__ = "decision"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("document.id"))
    ministere: Mapped[str | None] = mapped_column(String(300))  # « AU TITRE DE … »
    # adoption_decret | adoption_loi | rapport | communication | autorisation | autre
    type: Mapped[str] = mapped_column(String(30), default="autre", index=True)
    objet: Mapped[str] = mapped_column(Text)  # résumé fidèle de la mesure
    score_confiance: Mapped[float | None] = mapped_column(Float)
    statut_validation: Mapped[str] = mapped_column(String(20), default="a_valider", index=True)

    document: Mapped[Document] = relationship()

    def __str__(self) -> str:
        return f"[{self.type}] {self.objet[:80]}"


class EngagementFinancier(Base):
    """Dépense/engagement chiffré décidé en Conseil des ministres :
    marché public, convention, subvention, prêt, garantie…"""

    __tablename__ = "engagement_financier"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("document.id"))
    ministere: Mapped[str | None] = mapped_column(String(300))
    # marche | convention | subvention | pret | garantie | decaissement | autre
    type: Mapped[str] = mapped_column(String(30), default="autre", index=True)
    objet: Mapped[str] = mapped_column(Text)
    beneficiaire: Mapped[str | None] = mapped_column(String(500))
    montant_fcfa: Mapped[int | None] = mapped_column(BigInteger, index=True)
    score_confiance: Mapped[float | None] = mapped_column(Float)
    statut_validation: Mapped[str] = mapped_column(String(20), default="a_valider", index=True)

    document: Mapped[Document] = relationship()

    def __str__(self) -> str:
        return f"[{self.type}] {self.objet[:60]}"


class BudgetExercice(Base):
    """Chiffres agrégés d'une loi de finances adoptée en Conseil des ministres."""

    __tablename__ = "budget_exercice"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("document.id"))
    exercice: Mapped[int] = mapped_column(Integer, index=True)
    type_loi: Mapped[str] = mapped_column(String(20), default="initiale")  # initiale | rectificative | reglement
    recettes_fcfa: Mapped[int | None] = mapped_column(BigInteger)
    depenses_fcfa: Mapped[int | None] = mapped_column(BigInteger)
    score_confiance: Mapped[float | None] = mapped_column(Float)
    statut_validation: Mapped[str] = mapped_column(String(20), default="a_valider", index=True)

    document: Mapped[Document] = relationship()

    def __str__(self) -> str:
        return f"Budget {self.exercice} ({self.type_loi})"


class MembreGouvernement(Base):
    """Composition officielle du gouvernement, issue du décret de composition."""

    __tablename__ = "membre_gouvernement"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("document.id"))  # décret source
    ordre: Mapped[int] = mapped_column(Integer)  # ordre protocolaire dans le décret
    civilite: Mapped[str | None] = mapped_column(String(100))  # Monsieur, Madame, grade…
    nom_complet: Mapped[str] = mapped_column(String(300))
    poste: Mapped[str] = mapped_column(String(500))
    photo_url: Mapped[str | None] = mapped_column(String(500))  # portrait officiel (Présidence)
    genre: Mapped[str | None] = mapped_column(String(1))  # F/M — la civilité (grade) ne suffit pas
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    score_confiance: Mapped[float | None] = mapped_column(Float)
    statut_validation: Mapped[str] = mapped_column(String(20), default="a_valider", index=True)

    document: Mapped[Document] = relationship()

    def __str__(self) -> str:
        return f"{self.nom_complet} — {self.poste[:50]}"


class Depute(Base):
    """Membre de l'Assemblée législative (synchronisé depuis assembleenationale.bf)."""

    __tablename__ = "depute"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom_complet: Mapped[str] = mapped_column(String(300), unique=True)
    legislature: Mapped[str | None] = mapped_column(String(50))
    photo_url: Mapped[str | None] = mapped_column(String(500))
    actif: Mapped[bool] = mapped_column(Boolean, default=True)

    def __str__(self) -> str:
        return self.nom_complet


class DotationBudgetaire(Base):
    """Dotation d'un ministère/institution dans la loi de finances d'un exercice.

    Alimentée par saisie assistée (admin) depuis les documents budgétaires
    officiels — les LF récentes ne sont pas disponibles en données ouvertes.
    """

    __tablename__ = "dotation_budgetaire"

    id: Mapped[int] = mapped_column(primary_key=True)
    exercice: Mapped[int] = mapped_column(Integer, index=True)
    ministere: Mapped[str] = mapped_column(String(300))
    montant_fcfa: Mapped[int] = mapped_column(BigInteger)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("document.id"))
    source_libre: Mapped[str | None] = mapped_column(String(500))  # référence si hors corpus
    score_confiance: Mapped[float | None] = mapped_column(Float)
    statut_validation: Mapped[str] = mapped_column(String(20), default="a_valider", index=True)

    document: Mapped[Document | None] = relationship()

    def __str__(self) -> str:
        return f"{self.exercice} — {self.ministere[:40]}"


class RepartitionBudgetaire(Base):
    """Répartition du budget d'un exercice : recettes par catégorie, dépenses par nature.

    Alimentée depuis les documents officiels (loi de finances, Budget citoyen,
    comptes rendus) — saisie assistée, chaque ligne sourcée.
    """

    __tablename__ = "repartition_budgetaire"

    id: Mapped[int] = mapped_column(primary_key=True)
    exercice: Mapped[int] = mapped_column(Integer, index=True)
    sens: Mapped[str] = mapped_column(String(10), index=True)  # recette | depense
    libelle: Mapped[str] = mapped_column(String(300))
    montant_fcfa: Mapped[int] = mapped_column(BigInteger)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("document.id"))
    source_libre: Mapped[str | None] = mapped_column(String(500))  # référence si hors corpus
    statut_validation: Mapped[str] = mapped_column(String(20), default="a_valider", index=True)

    document: Mapped[Document | None] = relationship()

    def __str__(self) -> str:
        return f"{self.exercice} {self.sens} — {self.libelle[:40]}"


class Mandat(Base):
    """Vue consolidée dérivée des nominations validées — alimente l'annuaire."""

    __tablename__ = "mandat"

    id: Mapped[int] = mapped_column(primary_key=True)
    personne_id: Mapped[int] = mapped_column(ForeignKey("personne.id"))
    structure_id: Mapped[int | None] = mapped_column(ForeignKey("structure.id"))
    poste: Mapped[str] = mapped_column(String(500))
    date_debut: Mapped[date | None] = mapped_column(Date)
    date_fin: Mapped[date | None] = mapped_column(Date)
    nomination_debut_id: Mapped[int | None] = mapped_column(ForeignKey("nomination.id"))
    nomination_fin_id: Mapped[int | None] = mapped_column(ForeignKey("nomination.id"))

    personne: Mapped[Personne] = relationship()
    structure: Mapped[Structure | None] = relationship()


class Run(Base):
    """Journal d'exécution des collecteurs — alimente l'alerte « source muette »."""

    __tablename__ = "run"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"))
    debut: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    statut: Mapped[str] = mapped_column(String(20), default="en_cours")  # en_cours | ok | echec
    nb_nouveaux: Mapped[int] = mapped_column(Integer, default=0)
    nb_vus: Mapped[int] = mapped_column(Integer, default=0)
    erreurs: Mapped[str | None] = mapped_column(Text)

    source: Mapped[Source] = relationship()
