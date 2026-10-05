"""add summary progress tracking to ingest jobs

Revision ID: 9d7e97b6d96a
Revises: 9aaf7fc1324d
Create Date: 2026-10-05 21:23:14.292605

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d7e97b6d96a'
down_revision: Union[str, Sequence[str], None] = '9aaf7fc1324d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("ingest_jobs", sa.Column("summary_done", sa.Integer(), nullable=True))
    op.add_column("ingest_jobs", sa.Column("summary_total", sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("ingest_jobs", "summary_total")
    op.drop_column("ingest_jobs", "summary_done")
