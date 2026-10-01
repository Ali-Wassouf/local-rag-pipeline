"""Backfill command — generates section summaries for documents that were
indexed before Phase 5 added summarisation, without re-extracting or
re-chunking anything (docs/build-phases.md Phase 5 "Done when").

    uv run python -m app.ingest.backfill_summaries [--project-id N]

Reuses the worker's own summarise-stage logic (app.ingest.worker._run_summarize)
so backfilled documents go through exactly the same threshold check and
upsert as a document summarised during normal ingest.
"""

import argparse
import asyncio
import logging

from sqlalchemy import select

from app.db.session import async_session_maker
from app.ingest.worker import _run_summarize
from app.models.document import DocStatus, Document, ProjectDocument

logger = logging.getLogger(__name__)


async def backfill(project_id: int | None = None) -> None:
    async with async_session_maker() as db:
        stmt = select(Document).where(Document.status == DocStatus.ready)
        if project_id is not None:
            stmt = stmt.join(
                ProjectDocument, ProjectDocument.document_id == Document.id
            ).where(ProjectDocument.project_id == project_id)
        documents = list((await db.execute(stmt)).scalars().all())

        logger.info("backfilling summaries for %d document(s)", len(documents))
        for document in documents:
            logger.info("summarising %r (id=%s)", document.title, document.id)
            await _run_summarize(db, document)
            await db.commit()
        logger.info("backfill complete")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", type=int, default=None)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    asyncio.run(backfill(project_id=args.project_id))


if __name__ == "__main__":
    main()
