"""Worker process skeleton.

Phase 0 proves the plumbing only: no extraction happens here yet. Each job
is walked through the real stage sequence (extract -> structure -> chunk ->
embed -> summarise -> done) in small steps so progress visibly advances in
the UI. Phase 1+ replaces the stub work inside each stage with real logic.
"""

import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import async_session_maker
from app.models.document import DocStatus, Document
from app.models.job import IngestJob, JobStage

logger = logging.getLogger(__name__)

STAGE_SEQUENCE: list[JobStage] = [
    JobStage.extract,
    JobStage.structure,
    JobStage.chunk,
    JobStage.embed,
    JobStage.summarise,
]
STEPS_PER_STAGE = 4


def _status_for_stage(stage: JobStage) -> DocStatus:
    if stage in (JobStage.extract, JobStage.structure):
        return DocStatus.extracting
    if stage in (JobStage.chunk, JobStage.embed, JobStage.summarise):
        return DocStatus.indexing
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


async def _advance(db: AsyncSession, job: IngestJob) -> None:
    document = await db.get(Document, job.document_id)
    if document is None:
        job.error = "document not found"
        return

    if job.started_at is None:
        job.started_at = datetime.now(UTC)

    current_stage = JobStage(job.stage)
    stage_index = STAGE_SEQUENCE.index(current_stage)
    step = round(job.progress * STEPS_PER_STAGE) + 1

    if step >= STEPS_PER_STAGE:
        if stage_index + 1 < len(STAGE_SEQUENCE):
            new_stage = STAGE_SEQUENCE[stage_index + 1]
            job.stage = new_stage.value
            job.progress = 0.0
        else:
            new_stage = JobStage.done
            job.stage = new_stage.value
            job.progress = 1.0
            job.finished_at = datetime.now(UTC)
    else:
        new_stage = current_stage
        job.progress = step / STEPS_PER_STAGE

    document.status = _status_for_stage(new_stage)


async def run_worker_iteration() -> bool:
    """Claim and advance one job by one step. Returns True if work was done."""
    async with async_session_maker() as db, db.begin():
        job = await _claim_next_job(db)
        if job is None:
            return False
        await _advance(db, job)
        return True


async def run_forever() -> None:
    settings = get_settings()
    logger.info("worker started, polling every %.1fs", settings.worker_poll_interval_seconds)
    while True:
        advanced = await run_worker_iteration()
        await asyncio.sleep(0.5 if advanced else settings.worker_poll_interval_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_forever())
