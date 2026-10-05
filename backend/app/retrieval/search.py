"""Vector and keyword retrieval — the two candidate sources fused by RRF in
app/retrieval/fuse.py (see docs/plan.md §4.3).

Every query joins through project_documents (CLAUDE.md invariant 1) — a
query without that join is a bug even if it returns plausible-looking
results.
"""

from typing import Any

from sqlalchemy import String, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.models.chunk import Chunk
from app.models.document import Document, ProjectDocument
from app.models.section import Section

DEFAULT_TOP_K = 8
DEFAULT_CANDIDATE_K = 50


async def vector_search(
    db: AsyncSession,
    project_id: int,
    query_embedding: list[float],
    top_k: int = DEFAULT_TOP_K,
) -> list[tuple[Chunk, Section, Document]]:
    stmt = (
        select(Chunk, Section, Document)
        .join(Section, Section.id == Chunk.section_id)
        .join(Document, Document.id == Chunk.document_id)
        .join(ProjectDocument, ProjectDocument.document_id == Document.id)
        .where(ProjectDocument.project_id == project_id, Chunk.embedding.is_not(None))
        .order_by(Chunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )
    result = await db.execute(stmt)
    return [(row[0], row[1], row[2]) for row in result.all()]


def _or_query(query_text: str) -> ColumnElement[Any]:
    """plainto_tsquery ANDs every lexeme it extracts — fine for a couple
    of search terms, but a full-sentence question produces half a dozen
    lexemes that all have to appear in the same chunk, so it comes back
    empty far more often than not and the keyword side of RRF contributes
    nothing. Rewriting its '&'s to '|'s (the standard Postgres idiom —
    plainto_tsquery's ::text output is itself valid to_tsquery syntax)
    keeps every chunk that matches at least one lexeme in the running,
    with ts_rank still favouring chunks that match more of them."""
    and_query = func.plainto_tsquery("english", query_text)
    or_lexemes = func.regexp_replace(cast(and_query, String), " & ", " | ", "g")
    return func.to_tsquery("english", or_lexemes)


async def keyword_search(
    db: AsyncSession,
    project_id: int,
    query_text: str,
    top_k: int = DEFAULT_CANDIDATE_K,
) -> list[tuple[Chunk, Section, Document]]:
    query = _or_query(query_text)
    rank = func.ts_rank(Chunk.tsv, query)
    stmt = (
        select(Chunk, Section, Document)
        .join(Section, Section.id == Chunk.section_id)
        .join(Document, Document.id == Chunk.document_id)
        .join(ProjectDocument, ProjectDocument.document_id == Document.id)
        .where(ProjectDocument.project_id == project_id, Chunk.tsv.op("@@")(query))
        .order_by(rank.desc())
        .limit(top_k)
    )
    result = await db.execute(stmt)
    return [(row[0], row[1], row[2]) for row in result.all()]
