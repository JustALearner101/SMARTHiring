"""add_candidate_to_profile

Revision ID: 00676c75559c
Revises: 20261030_0003
Create Date: 2026-10-30 14:25:02.322281

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '00676c75559c'
down_revision: Union[str, None] = '20261030_0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tblm_profile', sa.Column('nid_candidate', sa.BigInteger(), nullable=True))
    op.create_index(op.f('ix_tblm_profile_nid_candidate'), 'tblm_profile', ['nid_candidate'], unique=False)
    op.create_foreign_key(
        op.f('fk_tblm_profile_nid_candidate_tblm_candidate'),
        'tblm_profile',
        'tblm_candidate',
        ['nid_candidate'],
        ['nid'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint(op.f('fk_tblm_profile_nid_candidate_tblm_candidate'), 'tblm_profile', type_='foreignkey')
    op.drop_index(op.f('ix_tblm_profile_nid_candidate'), table_name='tblm_profile')
    op.drop_column('tblm_profile', 'nid_candidate')
