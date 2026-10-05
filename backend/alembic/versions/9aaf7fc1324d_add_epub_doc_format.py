"""add epub to doc_format

Revision ID: 9aaf7fc1324d
Revises: ce7ff2709c4c
Create Date: 2026-10-05 10:00:00.000000

Adding an enum value is not reversible in Postgres (there's no DROP VALUE),
so downgrade is a no-op — consistent with that limitation, not an oversight.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9aaf7fc1324d'
down_revision: Union[str, Sequence[str], None] = 'ce7ff2709c4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE doc_format ADD VALUE 'epub'")


def downgrade() -> None:
    pass
