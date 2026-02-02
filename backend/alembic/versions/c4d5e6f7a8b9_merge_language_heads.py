"""merge user_preferred_language and source_language_indexes heads

Revision ID: c4d5e6f7a8b9
Revises: b8c9d0e1f2a3, a1c2d3e4f5b6
Create Date: 2026-02-02 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, None] = ('b8c9d0e1f2a3', 'a1c2d3e4f5b6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
