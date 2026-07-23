"""réalisation : second point d'extrémité (liaisons routières)

Revision ID: d5a2b6c7e8f9
Revises: c4f1a2b3d5e6
Create Date: 2026-07-23 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d5a2b6c7e8f9"
down_revision: Union[str, None] = "c4f1a2b3d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("realisation", sa.Column("localisation_nom_arr", sa.String(length=300), nullable=True))
    op.add_column("realisation", sa.Column("latitude_arr", sa.Float(), nullable=True))
    op.add_column("realisation", sa.Column("longitude_arr", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("realisation", "longitude_arr")
    op.drop_column("realisation", "latitude_arr")
    op.drop_column("realisation", "localisation_nom_arr")
