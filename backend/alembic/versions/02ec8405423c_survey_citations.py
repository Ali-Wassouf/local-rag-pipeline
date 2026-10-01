"""survey citations

Revision ID: 02ec8405423c
Revises: bffe94c5e963
Create Date: 2026-10-01 11:40:00.000000

A survey-mode citation points at a section_summaries row, not a chunk — a
message_citation now references exactly one of the two. Postgres can't put
a nullable column in a composite primary key, so this replaces the old
(message_id, chunk_id) primary key with a surrogate id, and a
UNIQUE(message_id, rank) constraint takes over the uniqueness the old key
gave for free.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '02ec8405423c'
down_revision: Union[str, Sequence[str], None] = 'bffe94c5e963'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE message_citations DROP CONSTRAINT message_citations_pkey")
    op.execute(
        "ALTER TABLE message_citations ADD COLUMN id BIGINT GENERATED ALWAYS AS IDENTITY"
    )
    op.execute("ALTER TABLE message_citations ADD PRIMARY KEY (id)")
    op.execute("ALTER TABLE message_citations ALTER COLUMN chunk_id DROP NOT NULL")
    op.execute(
        """
        ALTER TABLE message_citations
            ADD COLUMN section_summary_id BIGINT REFERENCES section_summaries(id) ON DELETE CASCADE
        """
    )
    op.execute(
        """
        ALTER TABLE message_citations
            ADD CONSTRAINT message_citations_exactly_one_source
            CHECK ((chunk_id IS NOT NULL) <> (section_summary_id IS NOT NULL))
        """
    )
    op.execute(
        """
        ALTER TABLE message_citations
            ADD CONSTRAINT message_citations_message_rank_unique UNIQUE (message_id, rank)
        """
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE message_citations DROP CONSTRAINT message_citations_message_rank_unique"
    )
    op.execute(
        "ALTER TABLE message_citations DROP CONSTRAINT message_citations_exactly_one_source"
    )
    op.execute("ALTER TABLE message_citations DROP COLUMN section_summary_id")
    op.execute("ALTER TABLE message_citations ALTER COLUMN chunk_id SET NOT NULL")
    op.execute("ALTER TABLE message_citations DROP CONSTRAINT message_citations_pkey")
    op.execute("ALTER TABLE message_citations DROP COLUMN id")
    op.execute("ALTER TABLE message_citations ADD PRIMARY KEY (message_id, chunk_id)")
