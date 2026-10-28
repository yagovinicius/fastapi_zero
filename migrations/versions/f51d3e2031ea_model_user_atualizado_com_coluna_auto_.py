"""model User atualizado com coluna auto-incremental updated_at

Revision ID: f51d3e2031ea
Revises: ebadc47a87db
Create Date: 2026-10-28 17:10:48.009166

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f51d3e2031ea'
down_revision: Union[str, Sequence[str], None] = 'ebadc47a87db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
