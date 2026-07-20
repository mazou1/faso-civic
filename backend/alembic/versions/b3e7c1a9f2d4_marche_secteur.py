"""marche.secteur (secteur déduit de l'objet)

Revision ID: b3e7c1a9f2d4
Revises: 5fdbd4d6d5a6
Create Date: 2026-07-20 14:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b3e7c1a9f2d4'
down_revision: Union[str, None] = '5fdbd4d6d5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('marche', sa.Column('secteur', sa.String(length=60), nullable=True))
    op.create_index(op.f('ix_marche_secteur'), 'marche', ['secteur'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_marche_secteur'), table_name='marche')
    op.drop_column('marche', 'secteur')
