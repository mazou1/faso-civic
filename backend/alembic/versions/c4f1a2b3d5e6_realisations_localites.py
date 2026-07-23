"""réalisations (inaugurations/infrastructures) + gazetteer localité

Revision ID: c4f1a2b3d5e6
Revises: b3e7c1a9f2d4
Create Date: 2026-07-23 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4f1a2b3d5e6"
down_revision: Union[str, None] = "b3e7c1a9f2d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "localite",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nom", sa.String(length=200), nullable=False),
        sa.Column("nom_normalise", sa.String(length=200), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("region", sa.String(length=120), nullable=True),
        sa.Column("province", sa.String(length=120), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("population", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=30), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_localite_nom"), "localite", ["nom"], unique=False)
    op.create_index(op.f("ix_localite_nom_normalise"), "localite", ["nom_normalise"], unique=False)
    op.create_index(op.f("ix_localite_region"), "localite", ["region"], unique=False)
    # index trigramme pour le géocodage flou (pg_trgm déjà activé)
    op.create_index(
        "ix_localite_nom_normalise_trgm",
        "localite",
        ["nom_normalise"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"nom_normalise": "gin_trgm_ops"},
    )

    op.create_table(
        "realisation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=True),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("titre", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("statut", sa.String(length=30), nullable=False),
        sa.Column("date_evenement", sa.Date(), nullable=True),
        sa.Column("localite_id", sa.Integer(), nullable=True),
        sa.Column("localisation_nom", sa.String(length=300), nullable=True),
        sa.Column("region", sa.String(length=120), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("precision_geo", sa.String(length=20), nullable=True),
        sa.Column("secteur", sa.String(length=60), nullable=True),
        sa.Column("maitre_ouvrage", sa.String(length=300), nullable=True),
        sa.Column("montant_fcfa", sa.BigInteger(), nullable=True),
        sa.Column("source_url", sa.String(length=1000), nullable=True),
        sa.Column("photo_url", sa.String(length=1000), nullable=True),
        sa.Column("score_confiance", sa.Float(), nullable=True),
        sa.Column("statut_validation", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["document.id"]),
        sa.ForeignKeyConstraint(["localite_id"], ["localite.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_realisation_type"), "realisation", ["type"], unique=False)
    op.create_index(op.f("ix_realisation_date_evenement"), "realisation", ["date_evenement"], unique=False)
    op.create_index(op.f("ix_realisation_region"), "realisation", ["region"], unique=False)
    op.create_index(op.f("ix_realisation_secteur"), "realisation", ["secteur"], unique=False)
    op.create_index(
        op.f("ix_realisation_statut_validation"), "realisation", ["statut_validation"], unique=False
    )


def downgrade() -> None:
    op.drop_table("realisation")
    op.drop_index("ix_localite_nom_normalise_trgm", table_name="localite")
    op.drop_index(op.f("ix_localite_region"), table_name="localite")
    op.drop_index(op.f("ix_localite_nom_normalise"), table_name="localite")
    op.drop_index(op.f("ix_localite_nom"), table_name="localite")
    op.drop_table("localite")
