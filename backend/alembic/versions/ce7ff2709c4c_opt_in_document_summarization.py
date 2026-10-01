"""opt-in document summarization

Revision ID: ce7ff2709c4c
Revises: 02ec8405423c
Create Date: 2026-10-01 15:00:00.000000

Summarization is costly (one generation call per long section), so it's now
an explicit choice at upload time rather than always running. Existing rows
default to TRUE — they already went through the pipeline as it worked
before this column existed, and the "generate a summary later" UI is only
meant to surface for documents where the user deliberately opted out going
forward.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'ce7ff2709c4c'
down_revision: Union[str, Sequence[str], None] = '02ec8405423c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE documents ADD COLUMN generate_summary BOOLEAN NOT NULL DEFAULT TRUE"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE documents DROP COLUMN generate_summary")
