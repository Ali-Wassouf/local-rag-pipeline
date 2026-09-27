"""Vector-only retrieval (Phase 3's deliberate baseline — no hybrid, no
reranking; see docs/build-phases.md).

Every query joins through project_documents (CLAUDE.md invariant 1) — a
query without that join is a bug even if it returns plausible-looking
results.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.document import Document, ProjectDocument
from app.models.section import Section

DEFAULT_TOP_K = 8


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
