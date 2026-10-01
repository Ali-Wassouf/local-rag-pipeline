import tempfile
from pathlib import Path

import httpx
import pytest
from sqlalchemy import select

from app.db.session import async_session_maker
from app.ingest.worker import _run_embed, _run_summarize, run_worker_iteration
from app.models.chunk import Chunk
from app.models.document import DocFormat, DocStatus, Document
from app.models.job import IngestJob, JobStage
from app.models.section import Section
from app.models.summary import SectionSummary

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


async def test_document_is_ready_as_soon_as_embedding_finishes_not_after_summarising() -> None:
    """The summarise stage is the slowest (docs/plan.md §3 step 7) and must
    run in the background without the document looking unusable — status
    flips to ready the moment the job *enters* the summarise stage, not
    after summarising actually completes."""
    async with async_session_maker() as db:
        document = Document(
            sha256="4" * 64,
            title="Ready-Before-Summarise Doc",
            format=DocFormat.txt,
            original_name="ready.txt",
            storage_path="/tmp/ready.txt",
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
        chunk = Chunk(
            document_id=document.id,
            section_id=section.id,
            ordinal=1,
            text="ab",
            embed_text="ab",
            char_start=0,
            char_end=2,
            token_count=1,
            embedding=[0.1] * 1024,
        )
        db.add(chunk)
        job = IngestJob(document_id=document.id, stage=JobStage.embed.value, progress=0.0)
        db.add(job)
        await db.commit()
        document_id = document.id
        job_id = job.id

    try:
        await run_worker_iteration()

        async with async_session_maker() as db:
            job = await db.get(IngestJob, job_id)
            document = await db.get(Document, document_id)
            assert job is not None
            assert document is not None
            # The embed stage found nothing left to embed (already embedded
            # above) and advanced straight to summarise.
            assert job.stage == JobStage.summarise.value
            assert document.status == DocStatus.ready
    finally:
        async with async_session_maker() as db:
            document = await db.get(Document, document_id)
            if document is not None:
                await db.delete(document)
                await db.commit()


async def test_summarize_stage_only_summarizes_sections_above_the_threshold() -> None:
    if not await _ollama_is_running():
        pytest.skip("Ollama is not running locally")

    long_paragraph = (
        "Serializable isolation is the strongest isolation level, preventing "
        "dirty reads, non-repeatable reads, and phantom reads by ensuring "
        "transactions behave as if executed one at a time. "
    ) * 50
    short_text = "A short section."
    raw_text = long_paragraph + short_text

    async with async_session_maker() as db:
        document = Document(
            sha256="5" * 64,
            title="Summarise Doc",
            format=DocFormat.txt,
            original_name="summarise.txt",
            storage_path="/tmp/summarise.txt",
            raw_text=raw_text,
        )
        db.add(document)
        await db.flush()
        long_section = Section(
            document_id=document.id,
            path="n1",
            title="Long",
            display_path="Long",
            depth=1,
            ordinal=1,
            char_start=0,
            char_end=len(long_paragraph),
        )
        short_section = Section(
            document_id=document.id,
            path="n2",
            title="Short",
            display_path="Short",
            depth=1,
            ordinal=2,
            char_start=len(long_paragraph),
            char_end=len(raw_text),
        )
        db.add_all([long_section, short_section])
        await db.commit()
        document_id = document.id
        long_section_id = long_section.id
        short_section_id = short_section.id

    try:
        async with async_session_maker() as db:
            document = await db.get(Document, document_id)
            assert document is not None
            await _run_summarize(db, document)
            await db.commit()

        async with async_session_maker() as db:
            summaries = (
                (
                    await db.execute(
                        select(SectionSummary).where(
                            SectionSummary.section_id.in_([long_section_id, short_section_id])
                        )
                    )
                )
                .scalars()
                .all()
            )
            summarized_section_ids = {s.section_id for s in summaries}
            assert summarized_section_ids == {long_section_id}
            summary = summaries[0]
            assert summary.document_id == document_id
            assert len(summary.embedding) == 1024
            assert summary.model != ""
    finally:
        async with async_session_maker() as db:
            document = await db.get(Document, document_id)
            if document is not None:
                await db.delete(document)
                await db.commit()


async def test_summarise_stage_is_skipped_when_generate_summary_is_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("summarize_section must not be called when generate_summary=False")

    monkeypatch.setattr("app.ingest.worker.summarize_section", _fail_if_called)

    long_paragraph = (
        "Serializable isolation is the strongest isolation level, preventing "
        "dirty reads, non-repeatable reads, and phantom reads by ensuring "
        "transactions behave as if executed one at a time. "
    ) * 50

    async with async_session_maker() as db:
        document = Document(
            sha256="6" * 64,
            title="Opt-Out Doc",
            format=DocFormat.txt,
            original_name="optout.txt",
            storage_path="/tmp/optout.txt",
            raw_text=long_paragraph,
            generate_summary=False,
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
            char_end=len(long_paragraph),
        )
        db.add(section)
        job = IngestJob(document_id=document.id, stage=JobStage.summarise.value, progress=0.0)
        db.add(job)
        await db.commit()
        document_id = document.id
        section_id = section.id
        job_id = job.id

    try:
        advanced = await run_worker_iteration()
        assert advanced is True

        async with async_session_maker() as db:
            job = await db.get(IngestJob, job_id)
            assert job is not None
            assert job.stage == JobStage.done.value
            assert job.error is None

            summaries = (
                (
                    await db.execute(
                        select(SectionSummary).where(SectionSummary.section_id == section_id)
                    )
                )
                .scalars()
                .all()
            )
            assert summaries == []
    finally:
        async with async_session_maker() as db:
            document = await db.get(Document, document_id)
            if document is not None:
                await db.delete(document)
                await db.commit()
