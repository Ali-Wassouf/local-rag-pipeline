from pathlib import Path

from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.document import DocStatus, Document
from app.models.job import IngestJob, JobStage
from app.models.section import Section
from app.models.summary import SectionSummary


async def test_upload_returns_job_and_creates_document(client: AsyncClient) -> None:
    response = await client.post(
        "/documents",
        files={"file": ("report.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["deduped"] is False
    assert body["job_id"] is not None
    assert body["document"]["title"] == "report"
    assert body["document"]["format"] == "txt"


async def test_upload_detects_epub_format(client: AsyncClient) -> None:
    response = await client.post(
        "/documents",
        files={"file": ("book.epub", b"not a real epub, just checking format detection", "application/epub+zip")},
    )
    assert response.status_code == 201
    assert response.json()["document"]["format"] == "epub"


async def test_uploading_same_content_twice_dedupes(
    client: AsyncClient, db_session
) -> None:
    content = b"the quick brown fox"
    first = await client.post(
        "/documents", files={"file": ("a.txt", content, "text/plain")}
    )
    second = await client.post(
        "/documents", files={"file": ("b.txt", content, "text/plain")}
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["deduped"] is False
    assert second.json()["deduped"] is True
    assert second.json()["job_id"] is None
    assert first.json()["document"]["id"] == second.json()["document"]["id"]

    sha256 = first.json()["document"]["sha256"]
    count = await db_session.scalar(
        select(func.count()).select_from(Document).where(Document.sha256 == sha256)
    )
    assert count == 1


async def test_upload_rejects_unsupported_format(client: AsyncClient) -> None:
    response = await client.post(
        "/documents", files={"file": ("data.exe", b"binary", "application/octet-stream")}
    )
    assert response.status_code == 400


async def test_get_document_not_found(client: AsyncClient) -> None:
    response = await client.get("/documents/999999")
    assert response.status_code == 404


async def test_list_all_documents(client: AsyncClient) -> None:
    await client.post("/documents", files={"file": ("x.txt", b"content x", "text/plain")})
    response = await client.get("/documents")
    assert response.status_code == 200
    titles = [d["title"] for d in response.json()]
    assert "x" in titles


# --- opt-in summarization ----------------------------------------------


async def test_upload_defaults_to_generating_a_summary(client: AsyncClient) -> None:
    response = await client.post(
        "/documents", files={"file": ("default.txt", b"content", "text/plain")}
    )
    assert response.json()["document"]["generate_summary"] is True


async def test_upload_can_opt_out_of_summary_generation(client: AsyncClient) -> None:
    response = await client.post(
        "/documents",
        files={"file": ("optout.txt", b"content", "text/plain")},
        data={"generate_summary": "false"},
    )
    assert response.json()["document"]["generate_summary"] is False


async def test_summarize_endpoint_flips_the_flag_and_queues_a_job(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    upload = await client.post(
        "/documents",
        files={"file": ("later.txt", b"content", "text/plain")},
        data={"generate_summary": "false"},
    )
    document_id = upload.json()["document"]["id"]

    document = await db_session.get(Document, document_id)
    assert document is not None
    document.status = DocStatus.ready
    await db_session.commit()

    response = await client.post(f"/documents/{document_id}/summarize")
    assert response.status_code == 200
    assert response.json()["generate_summary"] is True

    jobs = (
        (
            await db_session.execute(
                select(IngestJob).where(IngestJob.document_id == document_id)
            )
        )
        .scalars()
        .all()
    )
    summarise_jobs = [j for j in jobs if j.stage == JobStage.summarise.value]
    assert len(summarise_jobs) == 1


async def test_summarize_endpoint_404s_for_unknown_document(client: AsyncClient) -> None:
    response = await client.post("/documents/999999/summarize")
    assert response.status_code == 404


async def test_summarize_endpoint_409s_if_document_is_not_ready_yet(
    client: AsyncClient,
) -> None:
    upload = await client.post(
        "/documents",
        files={"file": ("notready.txt", b"content", "text/plain")},
        data={"generate_summary": "false"},
    )
    document_id = upload.json()["document"]["id"]
    # Freshly uploaded — still "uploaded"/"extracting", not "ready" yet.

    response = await client.post(f"/documents/{document_id}/summarize")
    assert response.status_code == 409


async def test_summarize_endpoint_409s_if_already_in_progress(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    upload = await client.post(
        "/documents",
        files={"file": ("inprogress.txt", b"content", "text/plain")},
        data={"generate_summary": "false"},
    )
    document_id = upload.json()["document"]["id"]
    document = await db_session.get(Document, document_id)
    assert document is not None
    document.status = DocStatus.ready
    await db_session.commit()

    first = await client.post(f"/documents/{document_id}/summarize")
    assert first.status_code == 200

    second = await client.post(f"/documents/{document_id}/summarize")
    assert second.status_code == 409


async def test_delete_document_removes_everything(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    upload = await client.post(
        "/documents",
        files={"file": ("remove-me.txt", b"some content", "text/plain")},
    )
    document_id = upload.json()["document"]["id"]
    document = await db_session.get(Document, document_id)
    assert document is not None
    storage_path = Path(document.storage_path)
    assert storage_path.exists()

    section = Section(
        document_id=document_id,
        path="n1",
        title="T",
        display_path="T",
        depth=1,
        ordinal=1,
        char_start=0,
        char_end=12,
    )
    db_session.add(section)
    await db_session.flush()
    chunk = Chunk(
        document_id=document_id,
        section_id=section.id,
        ordinal=1,
        text="some content",
        embed_text="some content",
        char_start=0,
        char_end=12,
        token_count=2,
    )
    summary = SectionSummary(
        section_id=section.id, document_id=document_id, summary="A summary.", model="test"
    )
    db_session.add_all([chunk, summary])
    await db_session.commit()
    chunk_id, summary_id = chunk.id, summary.id

    section_id = section.id

    response = await client.delete(f"/documents/{document_id}")
    assert response.status_code == 204

    # The delete happened through the API's own session — force this
    # session's identity map to forget its cached (now stale) objects
    # rather than silently reusing them.
    db_session.expire_all()
    assert await db_session.get(Document, document_id) is None
    assert await db_session.get(Section, section_id) is None
    assert await db_session.get(Chunk, chunk_id) is None
    assert await db_session.get(SectionSummary, summary_id) is None
    assert not storage_path.exists()

    assert (await client.get(f"/documents/{document_id}")).status_code == 404


async def test_delete_unknown_document_404s(client: AsyncClient) -> None:
    response = await client.delete("/documents/999999")
    assert response.status_code == 404


async def test_reindex_wipes_sections_and_queues_extract_job(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    upload = await client.post(
        "/documents",
        files={"file": ("reindex-me.txt", b"original content", "text/plain")},
    )
    document_id = upload.json()["document"]["id"]
    document = await db_session.get(Document, document_id)
    assert document is not None
    document.status = DocStatus.ready
    document.raw_text = "original content"
    await db_session.flush()

    section = Section(
        document_id=document_id,
        path="n1",
        title="T",
        display_path="T",
        depth=1,
        ordinal=1,
        char_start=0,
        char_end=16,
    )
    db_session.add(section)
    await db_session.commit()

    # Clear the job the upload itself queued, so reindex sees a clean slate.
    existing_jobs = (
        await db_session.execute(select(IngestJob).where(IngestJob.document_id == document_id))
    ).scalars()
    for job in existing_jobs:
        await db_session.delete(job)
    await db_session.commit()

    section_id = section.id

    response = await client.post(f"/documents/{document_id}/reindex")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in ("uploaded", "extracting")

    db_session.expire_all()
    assert await db_session.get(Section, section_id) is None

    jobs = (
        await db_session.execute(select(IngestJob).where(IngestJob.document_id == document_id))
    ).scalars().all()
    assert len(jobs) == 1
    assert jobs[0].stage == JobStage.extract.value


async def test_reindex_409s_if_a_job_is_already_in_progress(client: AsyncClient) -> None:
    upload = await client.post(
        "/documents",
        files={"file": ("busy.txt", b"content", "text/plain")},
    )
    document_id = upload.json()["document"]["id"]
    # Upload itself queues an extract job — still unfinished.

    response = await client.post(f"/documents/{document_id}/reindex")
    assert response.status_code == 409


async def test_reindex_unknown_document_404s(client: AsyncClient) -> None:
    response = await client.post("/documents/999999/reindex")
    assert response.status_code == 404
