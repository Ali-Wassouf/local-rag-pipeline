"""Survey path — vector search over section_summaries, not chunks
(docs/plan.md §4.4). Single pass across all documents in the project, no
per-document reduce step (§8): top 6 summaries regardless of which document
they came from.

Every query joins through project_documents (CLAUDE.md invariant 1), same
as the needle path.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, ProjectDocument
from app.models.section import Section
from app.models.summary import SectionSummary

# Committed default from docs/plan.md §8 — do not tune without a query set.
DEFAULT_TOP_K = 6


async def survey_search(
    db: AsyncSession,
    project_id: int,
    query_embedding: list[float],
    top_k: int = DEFAULT_TOP_K,
) -> list[tuple[SectionSummary, Section, Document]]:
    stmt = (
        select(SectionSummary, Section, Document)
        .join(Section, Section.id == SectionSummary.section_id)
        .join(Document, Document.id == SectionSummary.document_id)
        .join(ProjectDocument, ProjectDocument.document_id == Document.id)
        .where(
            ProjectDocument.project_id == project_id, SectionSummary.embedding.is_not(None)
        )
        .order_by(SectionSummary.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )
    result = await db.execute(stmt)
    return [(row[0], row[1], row[2]) for row in result.all()]
