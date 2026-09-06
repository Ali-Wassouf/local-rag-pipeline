from app.db.session import async_session_maker
from app.ingest.worker import STAGE_SEQUENCE, STEPS_PER_STAGE, run_worker_iteration
from app.models.document import DocFormat, DocStatus, Document
from app.models.job import IngestJob, JobStage


async def test_worker_advances_through_stubbed_stages() -> None:
    # The worker opens its own sessions and commits, so seed with a real
    # commit rather than the rollback-wrapped db_session fixture.
    async with async_session_maker() as db:
        document = Document(
            sha256="f" * 64,
            title="Worker Test Doc",
            format=DocFormat.txt,
            original_name="worker.txt",
            storage_path="/tmp/worker.txt",
        )
        db.add(document)
        await db.flush()
        job = IngestJob(document_id=document.id, stage=JobStage.extract.value, progress=0.0)
        db.add(job)
        await db.commit()
        document_id = document.id
        job_id = job.id

    total_steps = len(STAGE_SEQUENCE) * STEPS_PER_STAGE
    seen_stages: set[str] = set()
    try:
        for _ in range(total_steps):
            advanced = await run_worker_iteration()
            assert advanced is True
            async with async_session_maker() as db:
                refreshed = await db.get(IngestJob, job_id)
                assert refreshed is not None
                seen_stages.add(refreshed.stage)

        async with async_session_maker() as db:
            job = await db.get(IngestJob, job_id)
            document = await db.get(Document, document_id)
            assert job is not None
            assert document is not None
            assert job.stage == JobStage.done.value
            assert job.progress == 1.0
            assert job.finished_at is not None
            assert document.status == DocStatus.ready

        assert seen_stages == {s.value for s in STAGE_SEQUENCE} | {JobStage.done.value}
    finally:
        # Deleting the document cascades to its job (ON DELETE CASCADE).
        async with async_session_maker() as db:
            document = await db.get(Document, document_id)
            if document is not None:
                await db.delete(document)
                await db.commit()


async def test_worker_returns_false_when_no_jobs_pending() -> None:
    advanced = await run_worker_iteration()
    assert advanced is False
