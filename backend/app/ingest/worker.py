"""Ingest worker.

Wires extract -> structure -> chunk -> embed -> summarise for real.
Extraction and structure building happen as one atomic unit of work (Block
is deliberately never persisted — see app/extract/base.py — so there's no
checkpoint to resume from between them without re-parsing the file, which
docs/plan.md explicitly wants to avoid); the job still passes through the
"structure" stage value on its way to "chunk" so the stage name stays
meaningful in `ingest_jobs`.

A bad document must not kill the worker: any exception while advancing a
job — including fetching/deserialising the document row itself, not just
the stage's own work — marks that job failed with the error message and
moves on, rather than crashing the polling loop. That's the primary
guarantee, in `_advance`. `_poll_once` is a second, last-resort layer
around it: anything that still escapes (a DB connectivity blip, a bug in
the error-handling itself) is logged and swallowed there instead of taking
the whole process down. The two together are belt and suspenders — the
polling loop must never die, full stop.
"""

import asyncio
import logging
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import async_session_maker
from app.extract import docx as docx_extractor
from app.extract import epub as epub_extractor
from app.extract import pdf as pdf_extractor
from app.extract import pptx as pptx_extractor
from app.extract import text as text_extractor
from app.extract.base import ExtractFn
from app.ingest.chunk import persist_chunks
from app.ingest.embed import EMBEDDING_DIMENSION, embed_batch, get_or_create_embedding_run
from app.ingest.structure import build_structure, persist_structure
from app.ingest.summarize import needs_summary, persist_section_summary, summarize_section
from app.models.chunk import Chunk
from app.models.document import DocFormat, DocStatus, Document
from app.models.job import IngestJob, JobStage
from app.models.section import Section
from app.models.summary import SectionSummary

logger = logging.getLogger(__name__)

_EXTRACTORS: dict[DocFormat, ExtractFn] = {
    DocFormat.pdf: pdf_extractor.extract,
    DocFormat.docx: docx_extractor.extract,
    DocFormat.pptx: pptx_extractor.extract,
    DocFormat.txt: text_extractor.extract,
    DocFormat.md: text_extractor.extract,
    DocFormat.epub: epub_extractor.extract,
}


def _status_for_stage(stage: JobStage) -> DocStatus:
    # Called with the stage the job just transitioned INTO (the next
    # pending action), not the one just completed.
    if stage in (JobStage.extract, JobStage.structure):
        return DocStatus.extracting
    if stage in (JobStage.chunk, JobStage.embed):
        return DocStatus.indexing
    # stage is "summarise" (embedding just finished — chunks are queryable
    # now) or "done". Chat-usable the moment embedding is done; summarising
    # (slowest stage, docs/plan.md §3 step 7) must not keep the document
    # looking unusable while it runs in the background.
    return DocStatus.ready


async def _claim_next_job(db: AsyncSession) -> IngestJob | None:
    result = await db.execute(
        select(IngestJob)
        .where(IngestJob.stage != JobStage.done.value, IngestJob.error.is_(None))
        .order_by(IngestJob.id)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    return result.scalar_one_or_none()


async def _run_extract_and_structure(db: AsyncSession, document: Document) -> None:
    extractor = _EXTRACTORS[document.format]
    blocks = extractor(Path(document.storage_path))
    result = build_structure(blocks, document_title=document.title)
    await persist_structure(db, document, result)


async def _run_chunk(db: AsyncSession, document: Document) -> None:
    result = await db.execute(select(Section).where(Section.document_id == document.id))
    sections = list(result.scalars().all())
    await persist_chunks(db, document, sections)


async def _run_embed(db: AsyncSession, document: Document) -> None:
    result = await db.execute(
        select(Chunk).where(Chunk.document_id == document.id, Chunk.embedding.is_(None))
    )
    chunks = list(result.scalars().all())
    if not chunks:
        return

    settings = get_settings()
    run = await get_or_create_embedding_run(
        db, model=settings.embedding_model, dimension=EMBEDDING_DIMENSION
    )
    vectors = await embed_batch([chunk.embed_text for chunk in chunks])
    for chunk, vector in zip(chunks, vectors, strict=True):
        chunk.embedding = vector
        chunk.embedding_run_id = run.id


async def _run_summarize(db: AsyncSession, document: Document) -> tuple[int, int]:
    """Summarises at most one not-yet-summarised qualifying section, so a
    single call is cheap, resumable, and interruption-safe — the old
    all-sections-in-one-call version lost every bit of progress if the
    worker died partway through a long document (not just the in-flight
    section), and gave the UI nothing to show until the whole stage
    finished. Returns (done_count, total_count) over the qualifying set so
    the caller knows whether more remains and can show real progress.
    """
    result = await db.execute(select(Section).where(Section.document_id == document.id))
    sections = list(result.scalars().all())
    raw_text = document.raw_text or ""

    qualifying = [
        section
        for section in sections
        if needs_summary(raw_text[section.char_start : section.char_end])
    ]
    if not qualifying:
        return (0, 0)

    existing = await db.execute(
        select(SectionSummary.section_id).where(
            SectionSummary.section_id.in_([section.id for section in qualifying])
        )
    )
    done_ids = {row[0] for row in existing.all()}
    remaining = [section for section in qualifying if section.id not in done_ids]
    if not remaining:
        return (len(done_ids), len(qualifying))

    section = remaining[0]
    text = raw_text[section.char_start : section.char_end]
    summary_text = await summarize_section(text)
    vector = (await embed_batch([summary_text]))[0]
    settings = get_settings()
    await persist_section_summary(
        db, section, summary_text, vector, model=settings.generation_model
    )
    return (len(done_ids) + 1, len(qualifying))


async def _advance(db: AsyncSession, job: IngestJob) -> None:
    document: Document | None = None
    try:
        document = await db.get(Document, job.document_id)
        if document is None:
            job.error = "document not found"
            job.finished_at = datetime.now(UTC)
            return

        if job.started_at is None:
            job.started_at = datetime.now(UTC)

        stage = JobStage(job.stage)
        if stage is JobStage.extract:
            await _run_extract_and_structure(db, document)
            job.stage = JobStage.structure.value
        elif stage is JobStage.structure:
            job.stage = JobStage.chunk.value
        elif stage is JobStage.chunk:
            await _run_chunk(db, document)
            job.stage = JobStage.embed.value
        elif stage is JobStage.embed:
            await _run_embed(db, document)
            job.stage = JobStage.summarise.value
        elif stage is JobStage.summarise:
            # Opt-in (docs/build-phases.md Phase 5 follow-up) — summarizing
            # is a real time/resource cost, so a document that didn't ask
            # for it at upload time skips straight to done. It can still be
            # summarised later via POST /documents/{id}/summarize, which
            # queues a fresh job at this same stage with the flag flipped.
            if document.generate_summary:
                done_count, total_count = await _run_summarize(db, document)
                job.summary_done = done_count
                job.summary_total = total_count
                if done_count < total_count:
                    # More qualifying sections remain — stay on this stage
                    # so the next poll resumes with the next one, instead
                    # of summarising the whole document in one call with
                    # nothing visible until it's entirely done.
                    job.progress = done_count / total_count
                    return
            job.stage = JobStage.done.value
            job.finished_at = datetime.now(UTC)
    except Exception as exc:
        job.error = str(exc)
        job.finished_at = datetime.now(UTC)
        if document is not None:
            document.status = DocStatus.failed
        return

    job.progress = 1.0
    document.status = _status_for_stage(JobStage(job.stage))


async def run_worker_iteration() -> bool:
    """Claim and advance one job by one stage. Returns True if work was done."""
    async with async_session_maker() as db, db.begin():
        job = await _claim_next_job(db)
        if job is None:
            return False
        await _advance(db, job)
        return True


async def _poll_once() -> bool:
    """The last-resort layer (see the module docstring): per-job failures
    are already recorded on the job inside `_advance` and never reach here.
    This catches whatever still escapes that — a DB connectivity blip, a
    bug in the error handling itself — logs it, and lets the loop carry on
    instead of taking the whole worker down with it."""
    try:
        return await run_worker_iteration()
    except Exception:
        logger.exception("worker iteration failed outside normal per-job error handling")
        return False


async def run_forever() -> None:
    settings = get_settings()
    logger.info("worker started, polling every %.1fs", settings.worker_poll_interval_seconds)
    while True:
        advanced = await _poll_once()
        await asyncio.sleep(0.5 if advanced else settings.worker_poll_interval_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_forever())
