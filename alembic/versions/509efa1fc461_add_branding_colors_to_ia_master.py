"""Add branding colors to ia_master

Revision ID: 509efa1fc461
Revises: 2be1701b3d48
Create Date: 2026-05-18 15:06:19.422463

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '509efa1fc461'
down_revision: Union[str, Sequence[str], None] = '2be1701b3d48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ia_master', sa.Column('brand_background_color_light', sa.String(length=7), nullable=True))
    op.add_column('ia_master', sa.Column('brand_background_color_dark', sa.String(length=7), nullable=True))

def downgrade() -> None:
    op.drop_column('ia_master', 'brand_background_color_dark')
    op.drop_column('ia_master', 'brand_background_color_light')
