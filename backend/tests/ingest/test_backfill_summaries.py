from types import TracebackType

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingest.backfill_summaries import backfill
from app.models.document import DocFormat, DocStatus, Document, ProjectDocument
from app.models.project import Project


class _NoCloseSessionContext:
    """Wraps the test's own db_session so backfill()'s `async with
    async_session_maker()` doesn't close a session the fixture still owns."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None


async def _make_document(
    db_session: AsyncSession, name: str, status: DocStatus, project: Project | None = None
) -> Document:
    document = Document(
        sha256=name.ljust(64, "0"),
        title=f"Doc {name}",
        format=DocFormat.txt,
        original_name=f"{name}.txt",
        storage_path=f"/tmp/{name}.txt",
        status=status,
    )
    db_session.add(document)
    await db_session.flush()
    if project is not None:
        db_session.add(ProjectDocument(project_id=project.id, document_id=document.id))
        await db_session.flush()
    return document


async def test_backfill_only_processes_ready_documents(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    summarized_ids: list[int] = []

    async def fake_run_summarize(db: AsyncSession, document: Document) -> None:
        summarized_ids.append(document.id)

    monkeypatch.setattr("app.ingest.backfill_summaries._run_summarize", fake_run_summarize)
    monkeypatch.setattr(
        "app.ingest.backfill_summaries.async_session_maker",
        lambda: _NoCloseSessionContext(db_session),
    )

    ready = await _make_document(db_session, "ready", DocStatus.ready)
    await _make_document(db_session, "indexing", DocStatus.indexing)
    await _make_document(db_session, "failed", DocStatus.failed)
    await db_session.commit()

    await backfill()

    assert summarized_ids == [ready.id]


async def test_backfill_respects_the_project_filter(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    summarized_ids: list[int] = []

    async def fake_run_summarize(db: AsyncSession, document: Document) -> None:
        summarized_ids.append(document.id)

    monkeypatch.setattr("app.ingest.backfill_summaries._run_summarize", fake_run_summarize)
    monkeypatch.setattr(
        "app.ingest.backfill_summaries.async_session_maker",
        lambda: _NoCloseSessionContext(db_session),
    )

    project_a = Project(name="A")
    project_b = Project(name="B")
    db_session.add_all([project_a, project_b])
    await db_session.flush()

    doc_a = await _make_document(db_session, "a", DocStatus.ready, project=project_a)
    await _make_document(db_session, "b", DocStatus.ready, project=project_b)
    await db_session.commit()

    await backfill(project_id=project_a.id)

    assert summarized_ids == [doc_a.id]
