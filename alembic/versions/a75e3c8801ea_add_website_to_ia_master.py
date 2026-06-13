"""Add website to ia_master

Revision ID: a75e3c8801ea
Revises: 509efa1fc461
Create Date: 2026-06-13 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a75e3c8801ea'
down_revision: Union[str, Sequence[str], None] = '509efa1fc461'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ia_master', sa.Column('website', sa.String(length=255), nullable=True))

def downgrade() -> None:
    op.drop_column('ia_master', 'website')
