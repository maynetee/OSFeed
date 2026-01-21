"""merge_translation_branches

Revision ID: 53922b56144a
Revises: b4d5e6f7a8c9, b7c2d9e1f4a3
Create Date: 2026-01-21 17:51:04.266692

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '53922b56144a'
down_revision: Union[str, None] = ('b4d5e6f7a8c9', 'b7c2d9e1f4a3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
