import tempfile
from pathlib import Path

import httpx
import pytest
from sqlalchemy import select

from app.db.session import async_session_maker
from app.ingest.worker import _run_embed, run_worker_iteration
from app.models.chunk import Chunk
from app.models.document import DocFormat, DocStatus, Document
from app.models.job import IngestJob, JobStage
from app.models.section import Section

SCANNED_PDF_FIXTURE = Path(__file__).parent / "extract" / "fixtures" / "scanned.pdf"


async def _ollama_is_running() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5.0) as probe:
            response = await probe.get("http://localhost:11434/api/tags")
            response.raise_for_status()
        return True
    except httpx.HTTPError:
        return False


async def test_worker_runs_the_real_pipeline_end_to_end_for_a_text_document() -> None:
    if not await _ollama_is_running():
        pytest.skip("Ollama is not running locally")

    content = (
        "# Chapter One\n\n"
        "Body text for chapter one, long enough to be a realistic chunk of "
        "text for a first pass through the real ingest pipeline.\n\n"
        "## Section 1.1\n\n"
        "More body text here for section one point one, again long enough "
        "to be a believable paragraph rather than a single short line."
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        storage_path = f.name

    async with async_session_maker() as db:
        document = Document(
            sha256="1" * 64,
            title="Worker E2E Doc",
            format=DocFormat.txt,
            original_name="e2e.txt",
            storage_path=storage_path,
        )
        db.add(document)
        await db.flush()
        job = IngestJob(document_id=document.id, stage=JobStage.extract.value, progress=0.0)
        db.add(job)
        await db.commit()
        document_id = document.id
        job_id = job.id

    try:
        for _ in range(10):
            async with async_session_maker() as db:
                current = await db.get(IngestJob, job_id)
                assert current is not None
                if current.stage == JobStage.done.value or current.error is not None:
                    break
            await run_worker_iteration()

        async with async_session_maker() as db:
            job = await db.get(IngestJob, job_id)
            document = await db.get(Document, document_id)
            assert job is not None
            assert document is not None
            assert job.error is None
            assert job.stage == JobStage.done.value
            assert document.status == DocStatus.ready

            sections = (
                (await db.execute(select(Section).where(Section.document_id == document_id)))
                .scalars()
                .all()
            )
            titles = [s.title for s in sections]
            assert "Chapter One" in titles
            assert "Section 1.1" in titles

            chunks = (
                (await db.execute(select(Chunk).where(Chunk.document_id == document_id)))
                .scalars()
                .all()
            )
            assert len(chunks) > 0
            for chunk in chunks:
                assert chunk.embedding is not None
                assert len(chunk.embedding) == 1024
                assert chunk.embedding_run_id is not None
                # invariant: a chunk never crosses its own section's boundary
                section = next(s for s in sections if s.id == chunk.section_id)
                assert section.char_start <= chunk.char_start
                assert chunk.char_end <= section.char_end
    finally:
        Path(storage_path).unlink(missing_ok=True)
        async with async_session_maker() as db:
            document = await db.get(Document, document_id)
            if document is not None:
                await db.delete(document)
                await db.commit()


async def test_scanned_pdf_fails_the_job_instead_of_succeeding_empty() -> None:
    async with async_session_maker() as db:
        document = Document(
            sha256="2" * 64,
            title="Scanned Doc",
            format=DocFormat.pdf,
            original_name="scanned.pdf",
            storage_path=str(SCANNED_PDF_FIXTURE),
        )
        db.add(document)
        await db.flush()
        job = IngestJob(document_id=document.id, stage=JobStage.extract.value, progress=0.0)
        db.add(job)
        await db.commit()
        document_id = document.id
        job_id = job.id

    try:
        advanced = await run_worker_iteration()
        assert advanced is True

        async with async_session_maker() as db:
            job = await db.get(IngestJob, job_id)
            document = await db.get(Document, document_id)
            assert job is not None
            assert document is not None
            assert job.error is not None
            assert document.status == DocStatus.failed

            chunks = (
                (await db.execute(select(Chunk).where(Chunk.document_id == document_id)))
                .scalars()
                .all()
            )
            assert chunks == []
    finally:
        async with async_session_maker() as db:
            document = await db.get(Document, document_id)
            if document is not None:
                await db.delete(document)
                await db.commit()


async def test_embed_stage_does_not_recall_the_embedder_for_already_embedded_chunks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call_texts: list[list[str]] = []

    async def fake_embed_batch(texts: list[str]) -> list[list[float]]:
        call_texts.append(list(texts))
        return [[0.1] * 1024 for _ in texts]

    monkeypatch.setattr("app.ingest.worker.embed_batch", fake_embed_batch)

    async with async_session_maker() as db:
        document = Document(
            sha256="3" * 64,
            title="Embed Idempotency Doc",
            format=DocFormat.txt,
            original_name="embed.txt",
            storage_path="/tmp/embed.txt",
            raw_text="ab",
        )
        db.add(document)
        await db.flush()
        section = Section(
            document_id=document.id,
            path="n1",
            title="T",
            display_path="T",
            depth=1,
            ordinal=1,
            char_start=0,
            char_end=2,
        )
        db.add(section)
        await db.flush()
        chunk_a = Chunk(
            document_id=document.id,
            section_id=section.id,
            ordinal=1,
            text="a",
            embed_text="a",
            char_start=0,
            char_end=1,
            token_count=1,
        )
        chunk_b = Chunk(
            document_id=document.id,
            section_id=section.id,
            ordinal=2,
            text="b",
            embed_text="b",
            char_start=1,
            char_end=2,
            token_count=1,
        )
        db.add_all([chunk_a, chunk_b])
        await db.commit()
        document_id = document.id

    try:
        async with async_session_maker() as db:
            document = await db.get(Document, document_id)
            assert document is not None
            await _run_embed(db, document)
            await db.commit()

        assert len(call_texts) == 1
        assert sorted(call_texts[0]) == ["a", "b"]

        async with async_session_maker() as db:
            document = await db.get(Document, document_id)
            assert document is not None
            await _run_embed(db, document)
            await db.commit()

        assert len(call_texts) == 1  # no second call — nothing left to embed
    finally:
        async with async_session_maker() as db:
            document = await db.get(Document, document_id)
            if document is not None:
                await db.delete(document)
                await db.commit()


async def test_worker_returns_false_when_no_jobs_pending() -> None:
    advanced = await run_worker_iteration()
    assert advanced is False
