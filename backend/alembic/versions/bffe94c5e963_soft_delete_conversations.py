"""soft delete conversations

Revision ID: bffe94c5e963
Revises: 05cb0d50e6ad
Create Date: 2026-10-01 11:01:53.264489

A deleted conversation is hidden from every normal path (listing, reading
and sending messages) but never physically removed — it can be restored.
Messages and citations are untouched; they're only unreachable because
their parent conversation is hidden.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'bffe94c5e963'
down_revision: Union[str, Sequence[str], None] = '05cb0d50e6ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE conversations ADD COLUMN deleted_at TIMESTAMPTZ")


def downgrade() -> None:
    op.execute("ALTER TABLE conversations DROP COLUMN deleted_at")
