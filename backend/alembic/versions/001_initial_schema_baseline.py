"""initial_schema_baseline

Revision ID: 001_initial_baseline
Revises: 
Create Date: 2026-09-05 11:37:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_baseline'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Baseline migration establish version history. No business tables created."""
    pass


def downgrade() -> None:
    """Revert baseline migration."""
    pass
